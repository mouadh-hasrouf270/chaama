from django.db.models import Q
from rest_framework.permissions import BasePermission
from .models import Client, Matter


def is_admin(user):
    return user.is_superuser or (user.is_staff and user.role == 'SUPER_ADMIN')


class OfficeAccess(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user.is_authenticated and (is_admin(user) or (
            user.is_staff and user.role == 'INTERNAL_ASSOCIATE')))


def visible_matters(user):
    qs = Matter.objects.select_related('client_profile', 'created_by')
    return qs if is_admin(user) else qs.filter(Q(created_by=user) | Q(assignments__associate=user)).distinct()


def visible_clients(user):
    qs = Client.objects.all()
    return qs if is_admin(user) else qs.filter(Q(created_by=user) | Q(matters__in=visible_matters(user))).distinct()
