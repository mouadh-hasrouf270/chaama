from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from apps.accounts.permissions import is_admin
from apps.accounts.services import LAWYER_ROLES


class StandardPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsLawyerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and
                    (is_admin(request.user) or request.user.role in LAWYER_ROLES))

