from rest_framework import serializers
from .models import AuditLog, Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'is_read', 'created_at']
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'organization', 'action', 'object_type', 'object_id',
                  'ip_address', 'user_agent', 'metadata', 'created_at']
        read_only_fields = fields

