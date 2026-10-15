from rest_framework import serializers
from apps.accounts.permissions import is_admin
from .models import AssistanceRequest


class AssistanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistanceRequest
        fields = ['id', 'requesting_lawyer', 'title', 'description', 'assistance_type',
                  'jurisdiction', 'opposing_party', 'status', 'proposed_fee',
                  'fee_share_percentage', 'reviewed_by', 'reviewed_at', 'conflict_warning', 'created_at', 'updated_at']
        read_only_fields = ['id', 'requesting_lawyer', 'status', 'reviewed_by', 'reviewed_at', 'conflict_warning', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and not is_admin(request.user):
            self.fields.pop('conflict_warning')


class AssistanceReviewSerializer(serializers.Serializer):
    acknowledge_conflict = serializers.BooleanField(default=False)

