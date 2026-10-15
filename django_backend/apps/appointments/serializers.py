from django.utils import timezone
from django.conf import settings
from zoneinfo import ZoneInfo
from rest_framework import serializers
from apps.accounts.models import Client, LawyerProfile
from apps.accounts.permissions import is_admin
from .models import Appointment, CalendarBlock, LawyerAvailability
from .services import visible_clients


class AppointmentSerializer(serializers.ModelSerializer):
    lawyer_name = serializers.SerializerMethodField()

    def get_lawyer_name(self, obj):
        return obj.lawyer.user.get_full_name() if obj.lawyer_id else 'À attribuer'
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ['id', 'lawyer', 'lawyer_name', 'client', 'client_name', 'start_at', 'end_at',
                  'consultation_type', 'status', 'meeting_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_client_name(self, obj) -> str:
        return str(obj.client) if obj.client else ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if not request:
            return
        user = request.user
        if not user.is_authenticated:
            self.fields['client'].queryset = Client.objects.none()
            return
        if user.role == 'CLIENT' and not is_admin(user):
            self.fields['client'].read_only = True
        else:
            self.fields['client'].queryset = visible_clients(user)
            if not is_admin(user):
                self.fields['lawyer'].queryset = LawyerProfile.objects.filter(user=user)
        if self.instance:
            self.fields['lawyer'].read_only = True
            self.fields['client'].read_only = True

    def validate(self, attrs):
        request = self.context['request']
        if not self.instance:
            attrs.pop('status', None)
            attrs.pop('meeting_url', None)
            if request.user.role == 'CLIENT' and not is_admin(request.user):
                profile = Client.objects.filter(user=request.user).first()
                if not profile:
                    raise serializers.ValidationError('A linked client profile is required.')
                attrs['client'] = profile
        start = attrs.get('start_at', getattr(self.instance, 'start_at', None))
        end = attrs.get('end_at', getattr(self.instance, 'end_at', None))
        if start and end and end <= start:
            raise serializers.ValidationError({'end_at': 'Must be after start_at.'})
        url = attrs.get('meeting_url')
        if url and not url.startswith('https://'):
            raise serializers.ValidationError({'meeting_url': 'Use an HTTPS meeting URL.'})
        return attrs


class CalendarBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalendarBlock
        fields = ['id', 'lawyer', 'start_at', 'end_at', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and not is_admin(request.user):
            self.fields['lawyer'].queryset = LawyerProfile.objects.filter(user_id=request.user.pk)
        if self.instance:
            self.fields['lawyer'].read_only = True


class WorkingHoursSerializer(CalendarBlockSerializer):
    class Meta:
        model = LawyerAvailability
        fields = ['id', 'lawyer', 'weekday', 'start_time', 'end_time']
        read_only_fields = ['id']

    def validate(self, attrs):
        start = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end = attrs.get('end_time', getattr(self.instance, 'end_time', None))
        if start and end and end <= start:
            raise serializers.ValidationError({'end_time': 'Must be after start_time.'})
        return attrs


class AvailabilityQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
    lawyer = serializers.IntegerField(min_value=1, required=False)
    specialty = serializers.SlugField(required=False)

    def validate_date(self, value):
        today = timezone.localdate()
        if value < today or (value - today).days > 90:
            raise serializers.ValidationError('Choose a date within the next 90 days.')
        return value


class AvailableSlotSerializer(serializers.Serializer):
    lawyer = serializers.IntegerField()
    start_at = serializers.DateTimeField(default_timezone=ZoneInfo(settings.BOOKING_TIME_ZONE))
    end_at = serializers.DateTimeField(default_timezone=ZoneInfo(settings.BOOKING_TIME_ZONE))
    timezone = serializers.CharField(default=settings.BOOKING_TIME_ZONE)
