from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User
from .services import LAWYER_ROLES


def is_admin(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.role == User.Role.SUPER_ADMIN))


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)


class IsInternalAssociate(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.Role.INTERNAL_ASSOCIATE)


class IsExternalPartner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR)


class CanManageClients(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and (is_admin(request.user) or request.user.role in LAWYER_ROLES))


class PracticeAreaPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and (request.method in SAFE_METHODS or is_admin(request.user)))
