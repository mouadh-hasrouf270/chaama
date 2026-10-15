from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=60)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError('Audit records are append-only.')

    def delete(self):
        raise TypeError('Audit records are append-only.')

    def bulk_update(self, *args, **kwargs):
        raise TypeError('Audit records are append-only.')


class AuditLog(models.Model):
    # Preserve historical references even when a user or organization is removed.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey('organizations.Organization', null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=80)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=80)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = AppendOnlyQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at', '-id']

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise TypeError('Audit records are append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError('Audit records are append-only.')

