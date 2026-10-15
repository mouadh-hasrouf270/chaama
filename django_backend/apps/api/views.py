from django.db.models import Prefetch
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema
from apps.accounts.models import LawyerProfile, PracticeArea
from apps.accounts.views import ClientViewSet
from apps.appointments.services import visible_appointments, visible_clients
from apps.intakes.views import visible_intakes
from apps.assistance.views import visible_assistance
from apps.activity.models import Notification
from .common import StandardPagination, IsLawyerOrAdmin
from .serializers import PublicPracticeAreaSerializer, PublicLawyerSerializer, DashboardSerializer


class PublicPracticeAreaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PracticeArea.objects.filter(is_active=True)
    serializer_class = PublicPracticeAreaSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = StandardPagination


class LawyerFilter(filters.FilterSet):
    specialty = filters.CharFilter(field_name='practice_areas__slug')
    jurisdiction = filters.CharFilter(lookup_expr='iexact')
    bar_association = filters.CharFilter(lookup_expr='iexact')
    available = filters.BooleanFilter(method='filter_available')
    verified = filters.BooleanFilter(field_name='is_verified')

    class Meta:
        model = LawyerProfile
        fields = ['specialty', 'jurisdiction', 'bar_association', 'available', 'verified']

    def filter_available(self, qs, name, value):
        return qs.filter(availability_status='AVAILABLE' if value else 'UNAVAILABLE')


class PublicLawyerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LawyerProfile.objects.select_related('user', 'organization').prefetch_related(
        Prefetch('practice_areas', queryset=PracticeArea.objects.filter(is_active=True))).filter(
        user__is_active=True, user__role__in=['INTERNAL_ASSOCIATE', 'EXTERNAL_SUBCONTRACTOR'], is_verified=True).order_by('id')
    serializer_class = PublicLawyerSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = StandardPagination
    filterset_class = LawyerFilter


class PartnerViewSet(PublicLawyerViewSet):
    permission_classes = [IsLawyerOrAdmin]
    # Inherit JWT authentication instead of the anonymous public view.
    authentication_classes = [JWTAuthentication]
    queryset = LawyerProfile.objects.select_related('user', 'organization').prefetch_related(
        Prefetch('practice_areas', queryset=PracticeArea.objects.filter(is_active=True))).filter(
        user__is_active=True, user__role='EXTERNAL_SUBCONTRACTOR').order_by('id')


class ClientDirectoryViewSet(ClientViewSet):
    pagination_class = StandardPagination
    filter_backends = [filters.DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering_fields = ['first_name', 'last_name', 'created_at']
    ordering = ['-created_at', '-id']


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=DashboardSerializer)
    def get(self, request):
        now = timezone.now()
        appointments = visible_appointments(request.user).exclude(status='CANCELLED')
        data = {
            'today_appointments': appointments.filter(start_at__date=timezone.localdate()).order_by('start_at')[:100],
            'upcoming_appointments': appointments.filter(start_at__gt=now).order_by('start_at')[:10],
            'pending_intakes': visible_intakes(request.user).exclude(status='REVIEWED').count(),
            'pending_assistance_requests': visible_assistance(request.user).filter(status__in=['PENDING', 'CONFLICT_REVIEW']).count(),
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
            'clients_count': visible_clients(request.user).count() if request.user.role != 'CLIENT' else 0,
        }
        return Response(DashboardSerializer(data).data)
