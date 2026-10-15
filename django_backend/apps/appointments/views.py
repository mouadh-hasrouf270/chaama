from django.db import transaction
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.accounts.models import LawyerProfile
from apps.accounts.permissions import is_admin
from apps.api.common import StandardPagination, IsLawyerOrAdmin
from apps.activity.services import record_action
from .models import Appointment, CalendarBlock, LawyerAvailability
from .serializers import (AppointmentSerializer, CalendarBlockSerializer, WorkingHoursSerializer,
                          AvailabilityQuerySerializer, AvailableSlotSerializer)
from .services import (visible_appointments, create_appointment, update_appointment,
                       calculate_available_slots, save_calendar_block, lock_calendar, save_working_hours)


class AppointmentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                         mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filterset_fields = ['status', 'lawyer', 'consultation_type']

    def get_queryset(self):
        return visible_appointments(self.request.user)

    def perform_create(self, serializer):
        serializer.instance = create_appointment(serializer.validated_data, self.request)

    def perform_update(self, serializer):
        serializer.instance = update_appointment(serializer.instance, serializer.validated_data, self.request)

    @extend_schema(request=None, responses=AppointmentSerializer)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        obj = update_appointment(self.get_object(), {}, request, cancel=True)
        return Response(self.get_serializer(obj).data)

    @extend_schema(parameters=[AvailabilityQuerySerializer], responses=AvailableSlotSerializer(many=True))
    @action(detail=False, methods=['get'], permission_classes=[AllowAny], authentication_classes=[],
            pagination_class=None, filter_backends=[])
    def availability(self, request):
        query = AvailabilityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = query.validated_data
        lawyers = LawyerProfile.objects.select_related('user').filter(
            is_verified=True, user__is_active=True, availability_status='AVAILABLE',
            user__role__in=['INTERNAL_ASSOCIATE', 'EXTERNAL_SUBCONTRACTOR'])
        if data.get('lawyer'):
            lawyers = lawyers.filter(pk=data['lawyer'])
        if data.get('specialty'):
            lawyers = lawyers.filter(practice_areas__slug=data['specialty'], practice_areas__is_active=True)
        slots = []
        for lawyer in lawyers.distinct():
            slots.extend(calculate_available_slots(lawyer, data['date']))
        return Response(AvailableSlotSerializer(sorted(slots, key=lambda x: (x['start_at'], x['lawyer'])), many=True).data)


class CalendarBlockViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarBlockSerializer
    permission_classes = [IsLawyerOrAdmin]
    pagination_class = StandardPagination

    def get_queryset(self):
        qs = CalendarBlock.objects.all()
        if not self.request.user.is_authenticated:
            return qs.none()
        return qs if is_admin(self.request.user) else qs.filter(lawyer__user=self.request.user)

    def perform_create(self, serializer):
        serializer.instance = save_calendar_block(serializer.validated_data, self.request)

    def perform_update(self, serializer):
        serializer.instance = save_calendar_block(serializer.validated_data, self.request, serializer.instance)

    def perform_destroy(self, instance):
        with transaction.atomic():
            lock_calendar(instance.lawyer_id)
            record_action(self.request, 'calendar.block_deleted', instance)
            instance.delete()


class WorkingHoursViewSet(CalendarBlockViewSet):
    serializer_class = WorkingHoursSerializer

    def get_queryset(self):
        qs = LawyerAvailability.objects.all()
        if not self.request.user.is_authenticated:
            return qs.none()
        return qs if is_admin(self.request.user) else qs.filter(lawyer__user=self.request.user)

    def perform_create(self, serializer):
        serializer.instance = save_working_hours(serializer.validated_data, self.request)

    def perform_update(self, serializer):
        serializer.instance = save_working_hours(serializer.validated_data, self.request, serializer.instance)

    def perform_destroy(self, instance):
        with transaction.atomic():
            lock_calendar(instance.lawyer_id)
            record_action(self.request, 'calendar.working_hours_deleted', instance)
            instance.delete()
