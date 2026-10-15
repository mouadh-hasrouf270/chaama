from ipaddress import ip_address
from .models import AuditLog, Notification


def record_action(request, action, obj, metadata=None):
    address = request.META.get('REMOTE_ADDR') if request else None
    try:
        address = str(ip_address(address)) if address else None
    except ValueError:
        address = None
    user = request.user if request and request.user.is_authenticated else None
    # Metadata is a server-authored allowlist, never request.data or file contents.
    safe = {key: value for key, value in (metadata or {}).items()
            if key in {'fields', 'status', 'warning', 'file_size'}}
    return AuditLog.objects.create(
        user=user, action=action, object_type=obj._meta.label_lower, object_id=str(obj.pk),
        organization_id=getattr(obj, 'organization_id', None), ip_address=address,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
        metadata=safe,
    )


def notify(user_ids, event, title, message):
    Notification.objects.bulk_create([
        Notification(user_id=user_id, type=event, title=title, message=message)
        for user_id in set(user_ids) if user_id
    ])
