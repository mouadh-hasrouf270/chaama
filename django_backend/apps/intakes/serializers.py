from rest_framework import serializers
from apps.accounts.serializers import PhoneField
from apps.accounts.permissions import is_admin
from apps.appointments.services import visible_appointments
from apps.accounts.models import LawyerProfile, PracticeArea
from apps.appointments.models import Appointment
from .models import Intake, IntakeEvidence


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntakeEvidence
        fields = ['id', 'original_name', 'mime_type', 'file_size', 'uploaded_at']
        read_only_fields = fields


class EvidenceUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class IntakeSerializer(serializers.ModelSerializer):
    phone = PhoneField()
    evidence = EvidenceSerializer(many=True, read_only=True)

    class Meta:
        model = Intake
        fields = ['id', 'appointment', 'full_name', 'email', 'phone', 'legal_topic', 'description',
                  'opposing_party', 'status', 'conflict_warning', 'created_at', 'updated_at', 'evidence']
        read_only_fields = ['id', 'status', 'conflict_warning', 'created_at', 'updated_at', 'evidence']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request:
            self.fields['appointment'].queryset = visible_appointments(request.user)
            if not is_admin(request.user):
                self.fields.pop('conflict_warning')

    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Describe the situation using at least 10 characters.')
        return value


class IntakeReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['REVIEWED', 'REVIEW_REQUIRED'])


class PublicBookingSerializer(serializers.Serializer):
    lawyer = serializers.PrimaryKeyRelatedField(queryset=LawyerProfile.objects.filter(is_verified=True, user__is_active=True))
    practice_area = serializers.PrimaryKeyRelatedField(queryset=PracticeArea.objects.filter(is_active=True))
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    consultation_type = serializers.ChoiceField(choices=Appointment.ConsultationType.choices)
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = PhoneField()
    legal_topic = serializers.CharField(max_length=200)
    description = serializers.CharField(min_length=10, max_length=20000)
    opposing_party = serializers.CharField(max_length=250, required=False, allow_blank=True)
    consent = serializers.BooleanField()

    def validate(self, attrs):
        if not attrs['consent']:
            raise serializers.ValidationError({'consent': 'Consent is required.'})
        if not attrs['lawyer'].practice_areas.filter(pk=attrs['practice_area'].pk).exists():
            raise serializers.ValidationError({'lawyer': 'Lawyer does not cover the selected practice area.'})
        return attrs


class BookingReceiptSerializer(serializers.Serializer):
    status = serializers.CharField()



class PublicBookingRequestSerializer(serializers.Serializer):
    practice_area = serializers.PrimaryKeyRelatedField(queryset=PracticeArea.objects.filter(is_active=True))
    requested_date = serializers.DateField()
    preferred_time = serializers.TimeField()
    consultation_type = serializers.ChoiceField(choices=Appointment.ConsultationType.choices)
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = PhoneField()
    legal_topic = serializers.CharField(max_length=200)
    description = serializers.CharField(min_length=10, max_length=20000)
    opposing_party = serializers.CharField(max_length=250, required=False, allow_blank=True)
    consent = serializers.BooleanField()

    def validate(self, attrs):
        from datetime import timedelta
        from django.utils import timezone
        if attrs['consent'] is not True:
            raise serializers.ValidationError({'consent': 'Consent is required.'})
        today = timezone.localdate()
        if attrs['requested_date'] < today or attrs['requested_date'] > today + timedelta(days=90):
            raise serializers.ValidationError({'requested_date': 'Select a date within 90 days.'})
        return attrs
