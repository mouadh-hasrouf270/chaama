from rest_framework import serializers
from .models import Matter, MatterAssignment


class MatterAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatterAssignment
        fields = ['id', 'matter', 'associate', 'assigned_by', 'assigned_at']
        read_only_fields = ['assigned_by', 'assigned_at']


class MatterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Matter
        fields = [
            'id', 'reference', 'title', 'description',
            'client', 'status', 'priority',
            'opened_at', 'closed_at',
            'created_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']