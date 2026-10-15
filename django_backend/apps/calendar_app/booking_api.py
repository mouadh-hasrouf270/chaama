import re
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .booking import available_slots, office_now, policy, scheduled_slots
from .models import Appointment, PracticeArea


class BookingConflict(APIException):
    status_code = 409
    default_detail = 'Ce créneau vient d’être réservé. Choisissez un autre horaire.'


class BookingThrottle(AnonRateThrottle):
    rate = '20/hour'


class OfficeStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        # Public registration accepts role input in the legacy accounts app.
        # Require the server-managed staff flag, not that untrusted role alone.
        return bool(user.is_authenticated and (user.is_superuser or (
            user.is_staff and user.role in ('SUPER_ADMIN', 'INTERNAL_ASSOCIATE'))))


class BookingSerializer(serializers.ModelSerializer):
    # Report slot collisions consistently as 409 via the database, not DRF's
    # automatically generated uniqueness validator (400, and race-prone).
    start_at = serializers.DateTimeField()
    practice_area = serializers.PrimaryKeyRelatedField(queryset=PracticeArea.objects.filter(is_active=True))
    description = serializers.CharField(min_length=10, max_length=5000)
    consent = serializers.BooleanField(required=True)

    class Meta:
        model = Appointment
        validators = []
        fields = ['practice_area', 'start_at', 'consultation_type', 'full_name', 'email',
                  'phone', 'legal_topic', 'description', 'opposing_party', 'consent']

    def validate_phone(self, value):
        if not re.fullmatch(r'\+?[\d\s().-]+', value) or not 8 <= len(re.sub(r'\D', '', value)) <= 15:
            raise serializers.ValidationError('Saisissez un numéro de téléphone valide.')
        return value

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError('Votre consentement est nécessaire.')
        return value

    def validate(self, attrs):
        start = attrs['start_at'].astimezone(ZoneInfo(policy()['TIME_ZONE']))
        match = next((end for slot, end in scheduled_slots(start.date()) if slot == start), None)
        if match is None:
            raise serializers.ValidationError({'start_at': 'Ce créneau est hors des horaires disponibles.'})
        attrs['end_at'] = match
        return attrs


class AppointmentSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='full_name')
    practice_area_name = serializers.CharField(source='practice_area.name')

    class Meta:
        model = Appointment
        fields = ['id', 'reference', 'practice_area', 'practice_area_name', 'start_at', 'end_at',
                  'consultation_type', 'client_name', 'email', 'phone', 'legal_topic',
                  'description', 'opposing_party', 'status', 'created_at']


class PublicAreas(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(list(PracticeArea.objects.filter(is_active=True).values('id', 'name', 'slug')))


class AvailabilityQuery(serializers.Serializer):
    date = serializers.DateField()
    specialty = serializers.SlugField()


class Availability(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        query = AvailabilityQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        if not PracticeArea.objects.filter(slug=query.validated_data['specialty'], is_active=True).exists():
            raise serializers.ValidationError({'specialty': 'Expertise indisponible.'})
        return Response(available_slots(query.validated_data['date']))


class BookingConfig(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        config = policy()
        return Response({'timezone': config['TIME_ZONE'], 'min_date': office_now().date(),
                         'max_date': office_now().date() + timedelta(days=config['HORIZON_DAYS']),
                         'weekdays': config['WEEKDAYS'], 'duration_minutes': config['DURATION_MINUTES']})


class PublicBooking(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [BookingThrottle]

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            # The database constraint arbitrates concurrent requests, including SQLite.
            with transaction.atomic():
                appointment = serializer.save()
        except IntegrityError:
            raise BookingConflict()
        return Response({'reference': appointment.reference, 'status': appointment.status,
                         'start_at': appointment.start_at, 'end_at': appointment.end_at,
                         'timezone': policy()['TIME_ZONE']}, status=status.HTTP_201_CREATED)


class AppointmentList(APIView):
    permission_classes = [OfficeStaff]

    def get(self, request):
        appointments = Appointment.objects.select_related('practice_area')
        # Bounded calendar range, defaulting to the booking horizon.
        dates = {}
        for key in ('from', 'to'):
            if key in request.query_params:
                dates[key] = serializers.DateField().run_validation(request.query_params[key])
        first = dates.get('from', office_now().date() - timedelta(days=7))
        last = dates.get('to', first + timedelta(days=policy()['HORIZON_DAYS']))
        if last < first or (last - first).days > 366:
            raise serializers.ValidationError('La période doit être comprise entre 0 et 366 jours.')
        from datetime import datetime, time
        zone = ZoneInfo(policy()['TIME_ZONE'])
        appointments = appointments.filter(start_at__gte=datetime.combine(first, time.min, zone),
            start_at__lt=datetime.combine(last + timedelta(days=1), time.min, zone))
        return Response(AppointmentSerializer(appointments, many=True).data)


class AppointmentTransition(APIView):
    permission_classes = [OfficeStaff]

    def post(self, request, pk, action):
        rules = {'confirm': (['PENDING'], 'CONFIRMED'),
                 'cancel': (['PENDING', 'CONFIRMED'], 'CANCELLED'),
                 'complete': (['CONFIRMED'], 'COMPLETED')}
        if action not in rules:
            return Response(status=404)
        from django.shortcuts import get_object_or_404
        appointment = get_object_or_404(Appointment, pk=pk)
        allowed, target = rules[action]
        if appointment.status == target:
            return Response(AppointmentSerializer(appointment).data)
        now = timezone.now()
        if (target == 'CONFIRMED' and appointment.start_at <= now) or (
                target == 'COMPLETED' and appointment.end_at > now):
            return Response({'detail': 'Cette action ne correspond pas à la date du rendez-vous.'}, status=409)
        updated = Appointment.objects.filter(pk=pk, status__in=allowed).update(status=target, updated_at=now)
        if not updated:
            return Response({'detail': 'Le statut a changé. Actualisez le calendrier.'}, status=409)
        appointment.refresh_from_db()
        return Response(AppointmentSerializer(appointment).data)


class BookingDashboard(APIView):
    permission_classes = [OfficeStaff]

    def get(self, request):
        from datetime import datetime, time
        now = office_now()
        start = datetime.combine(now.date(), time.min, now.tzinfo)
        active = Appointment.objects.select_related('practice_area').exclude(status='CANCELLED')
        today = active.filter(start_at__gte=start, start_at__lt=start + timedelta(days=1))
        upcoming = active.filter(start_at__gte=now, status__in=['PENDING', 'CONFIRMED'])
        return Response({'timezone': policy()['TIME_ZONE'],
                         'today_appointments': AppointmentSerializer(today, many=True).data,
                         'upcoming_appointments': AppointmentSerializer(upcoming[:10], many=True).data,
                         'upcoming_count': upcoming.count(),
                         'pending_intakes': active.filter(status='PENDING').count(),
                         'confirmed_count': upcoming.filter(status='CONFIRMED').count()})
