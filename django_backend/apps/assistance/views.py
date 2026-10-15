from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema
from apps.accounts.permissions import is_admin, IsSuperAdmin
from apps.api.common import StandardPagination
from .models import AssistanceRequest
from .serializers import AssistanceRequestSerializer, AssistanceReviewSerializer
from .services import submit_assistance_request, review_assistance


class AssistancePermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and
                    (is_admin(request.user) or request.user.role == 'EXTERNAL_SUBCONTRACTOR'))


def visible_assistance(user):
    qs = AssistanceRequest.objects.select_related('requesting_lawyer__user')
    if not user.is_authenticated:
        return qs.none()
    if is_admin(user):
        return qs
    return qs.filter(requesting_lawyer__user=user) if user.role == 'EXTERNAL_SUBCONTRACTOR' else qs.none()


class AssistanceRequestViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                               mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AssistanceRequestSerializer
    permission_classes = [AssistancePermission]
    pagination_class = StandardPagination
    filterset_fields = ['status', 'jurisdiction']

    def get_queryset(self):
        return visible_assistance(self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role != 'EXTERNAL_SUBCONTRACTOR':
            raise PermissionDenied('Only external lawyers submit their own assistance requests.')
        serializer.instance = submit_assistance_request(serializer.validated_data, self.request)

    def review(self, request, approved):
        serializer = AssistanceReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = review_assistance(self.get_object(), approved, request, **serializer.validated_data)
        return Response(self.get_serializer(instance).data)

    @extend_schema(request=AssistanceReviewSerializer, responses=AssistanceRequestSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def approve(self, request, pk=None):
        return self.review(request, True)

    @extend_schema(request=AssistanceReviewSerializer, responses=AssistanceRequestSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsSuperAdmin])
    def decline(self, request, pk=None):
        return self.review(request, False)

