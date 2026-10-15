from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from apps.accounts.permissions import IsSuperAdmin
from apps.api.common import StandardPagination
from .models import Notification, AuditLog
from .serializers import NotificationSerializer, AuditLogSerializer


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    filterset_fields = ['is_read']

    def get_queryset(self):
        return Notification.objects.filter(user_id=self.request.user.pk)

    @extend_schema(request=None, responses=NotificationSerializer)
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        obj = self.get_object()
        obj.is_read = True
        obj.save(update_fields=['is_read'])
        return Response(self.get_serializer(obj).data)

    @extend_schema(request=None, responses=inline_serializer('ReadAllResult', fields={'updated': serializers.IntegerField()}))
    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'updated': count})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardPagination
    filterset_fields = ['action', 'object_type', 'user']

