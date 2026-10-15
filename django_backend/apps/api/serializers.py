from rest_framework import serializers
from apps.accounts.models import PracticeArea, LawyerProfile
from apps.appointments.serializers import AppointmentSerializer


class PublicPracticeAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeArea
        fields = ['id', 'name', 'slug', 'description']


class PublicLawyerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    practice_areas = PublicPracticeAreaSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True, allow_null=True)

    class Meta:
        model = LawyerProfile
        fields = ['id', 'name', 'organization_name', 'bar_association', 'jurisdiction',
                  'bio', 'years_experience', 'availability_status', 'is_verified', 'practice_areas']


class DashboardSerializer(serializers.Serializer):
    today_appointments = AppointmentSerializer(many=True)
    upcoming_appointments = AppointmentSerializer(many=True)
    pending_intakes = serializers.IntegerField()
    pending_assistance_requests = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    clients_count = serializers.IntegerField()

