from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from apps.accounts.permissions import is_admin
from apps.accounts.booking_accounts import provision_booking_client
from apps.activity.services import record_action
from apps.appointments.services import visible_appointments, create_appointment
from apps.api.common import StandardPagination
from .models import Intake
from .serializers import (IntakeSerializer, EvidenceUploadSerializer, EvidenceSerializer,
                          PublicBookingSerializer, BookingReceiptSerializer, IntakeReviewSerializer, PublicBookingRequestSerializer)
from .services import submit_intake, save_evidence


def visible_intakes(user):
    return Intake.objects.select_related('appointment__lawyer__user').prefetch_related('evidence').filter(
        appointment__in=visible_appointments(user))


class IntakeViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = IntakeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return visible_intakes(self.request.user)

    def perform_create(self, serializer):
        serializer.instance = submit_intake(serializer.validated_data, self.request)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        for item in response.data['results']:
            record_action(request, 'intake.viewed', Intake(pk=item['id']))
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        record_action(request, 'intake.viewed', instance)
        return Response(self.get_serializer(instance).data)

    @extend_schema(request=IntakeReviewSerializer, responses=IntakeSerializer)
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        instance = self.get_object()
        if not is_admin(request.user) and (not instance.appointment.lawyer_id or instance.appointment.lawyer.user_id != request.user.pk):
            raise PermissionDenied()
        serializer = IntakeReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.status = serializer.validated_data['status']
        instance.save(update_fields=['status', 'updated_at'])
        record_action(request, 'intake.reviewed', instance, {'status': instance.status})
        return Response(self.get_serializer(instance).data)

    @extend_schema(request=EvidenceUploadSerializer, responses={201: EvidenceSerializer})
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def files(self, request, pk=None):
        intake = self.get_object()
        serializer = EvidenceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        evidence = save_evidence(intake, serializer.validated_data['file'], request)
        return Response(EvidenceSerializer(evidence).data, status=201)

    @extend_schema(responses={(200, 'application/octet-stream'): OpenApiTypes.BINARY})
    @action(detail=True, methods=['get'], url_path=r'files/(?P<file_id>[0-9]+)/download')
    def download(self, request, pk=None, file_id=None):
        intake = self.get_object()
        evidence = get_object_or_404(intake.evidence, pk=file_id)
        record_action(request, 'intake.evidence_accessed', evidence)
        response = FileResponse(evidence.file.open('rb'), as_attachment=True,
                                filename=evidence.original_name, content_type='application/octet-stream')
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cache-Control'] = 'private, no-store'
        return response


class PublicBookingThrottle(AnonRateThrottle):
    rate = '10/hour'


class PublicBookingView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [PublicBookingThrottle]

    @extend_schema(request=PublicBookingSerializer, responses={201: BookingReceiptSerializer})
    def post(self, request):
        serializer = PublicBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        data.pop('consent')
        data.pop('practice_area')
        with transaction.atomic():
            booking_fields = {key: data.pop(key) for key in
                              ['lawyer', 'start_at', 'end_at', 'consultation_type']}
            appointment = create_appointment(booking_fields, request)
            client = provision_booking_client(full_name=data['full_name'],
                                              email=data['email'], phone=data['phone'])
            if client is not None:
                appointment.client = client
                appointment.save(update_fields=['client', 'updated_at'])
            submit_intake({**data, 'appointment': appointment}, request)
        # A public receipt must never expose an existing client or private intake.
        transaction.on_commit(lambda appointment_id=appointment.pk: __import__(
            'apps.practice.google_calendar', fromlist=['queue_public_appointment_sync']
        ).queue_public_appointment_sync(appointment_id))
        return Response({'status': 'booked', 'appointment_reference': appointment.pk}, status=201)



class PublicBookingRequestView(APIView):
    """Accept requested times without promising that a lawyer is reserved."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [PublicBookingThrottle]

    @extend_schema(request=PublicBookingRequestSerializer, responses={201: BookingReceiptSerializer})
    def post(self, request):
        from zoneinfo import ZoneInfo
        from django.conf import settings
        from apps.accounts.models import LawyerProfile
        from apps.appointments.models import BookingRequest
        from apps.appointments.services import calculate_available_slots, BookingConflict
        serializer = PublicBookingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data.copy()
        data.pop('consent')
        with transaction.atomic():
            client = provision_booking_client(full_name=data['full_name'], email=data['email'], phone=data['phone'])
            lawyers = LawyerProfile.objects.filter(is_verified=True, user__is_active=True,
                availability_status='AVAILABLE', practice_areas=data['practice_area']).select_related('user').distinct()
            # Server-side slot discovery prevents a frontend availability failure from
            # turning a genuinely bookable time into an unconfirmed enquiry.
            for lawyer in lawyers:
                for slot in calculate_available_slots(lawyer, data['requested_date']):
                    local_time = slot['start_at'].astimezone(ZoneInfo(settings.BOOKING_TIME_ZONE)).time().replace(tzinfo=None)
                    if local_time != data['preferred_time']:
                        continue
                    try:
                        # Nested savepoint: one conflicting slot does not roll back
                        # the client identity created earlier in this transaction.
                        with transaction.atomic():
                            appt = create_appointment({
                                'lawyer': lawyer, 'start_at': slot['start_at'],
                                'end_at': slot['end_at'], 'consultation_type': data['consultation_type'],
                                'client': client,
                            }, request)
                            Intake.objects.create(appointment=appt, full_name=data['full_name'],
                                email=data['email'], phone=data['phone'], legal_topic=data['legal_topic'],
                                description=data['description'], opposing_party=data.get('opposing_party', ''))
                        transaction.on_commit(lambda appointment_id=appt.pk: __import__(
                            'apps.practice.google_calendar', fromlist=['queue_public_appointment_sync']
                        ).queue_public_appointment_sync(appointment_id))
                        return Response({'status': 'booked', 'appointment_reference': appt.pk}, status=201)
                    except BookingConflict:
                        continue
            # Do NOT silently convert a user's booking to an enquiry. A public
            # booking without an available lawyer remains a genuine Appointment,
            # visible in the administrative calendar, pending staff assignment.
            # It is not a promise that an individual lawyer has been reserved.
            from datetime import datetime, timedelta, timezone as dt_timezone
            from django.utils import timezone
            start_local = datetime.combine(data['requested_date'], data['preferred_time'], tzinfo=ZoneInfo(settings.BOOKING_TIME_ZONE))
            start_at = start_local.astimezone(dt_timezone.utc)
            if start_at <= timezone.now():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'preferred_time': 'Choisissez une heure future.'})
            from apps.appointments.models import Appointment
            appointment = Appointment.objects.create(
                lawyer=None, client=client, start_at=start_at,
                end_at=start_at + timedelta(minutes=settings.BOOKING_SLOT_MINUTES),
                consultation_type=data['consultation_type'], status='PENDING',
            )
            Intake.objects.create(appointment=appointment, full_name=data['full_name'],
                email=data['email'], phone=data['phone'], legal_topic=data['legal_topic'],
                description=data['description'], opposing_party=data.get('opposing_party', ''))
            from django.db import transaction as tx
            tx.on_commit(lambda appointment_id=appointment.pk: __import__(
                'apps.practice.google_calendar', fromlist=['queue_public_appointment_sync']
            ).queue_public_appointment_sync(appointment_id))
        return Response({'status': 'booked', 'assignment_pending': True,
                         'appointment_reference': appointment.pk}, status=201)
