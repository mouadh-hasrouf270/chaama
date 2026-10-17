from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Client, LawyerProfile, PracticeArea, User
from .permissions import CanManageClients, IsSuperAdmin, PracticeAreaPermission, is_admin
from .serializers import (
    ClientSelfSerializer, ClientSerializer, LawyerProfileSerializer,
    LawyerVerificationSerializer, ManagedUserSerializer, PracticeAreaSerializer,
    RegisterSerializer, UserSerializer, PhoneEnrollmentSerializer,
)
from .services import LAWYER_ROLES


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PhoneEnrollmentView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PhoneEnrollmentSerializer

    @extend_schema(request=PhoneEnrollmentSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = PhoneEnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                if user.phone:
                    raise serializers.ValidationError('This account already has a phone number.')
                for field, value in serializer.validated_data.items():
                    setattr(user, field, value)
                user.save(update_fields=['phone', 'first_name', 'last_name'])
        except IntegrityError:
            raise serializers.ValidationError({'phone': 'This phone number is already registered.'})
        return Response(UserSerializer(user).data)


class ManagedUserViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                         mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.order_by('id')
    permission_classes = [IsSuperAdmin]

    def get_serializer_class(self):
        return ManagedUserSerializer if self.action == 'create' else UserSerializer

    @extend_schema(request=None, responses=UserSerializer)
    @action(detail=True, methods=['post'], url_path='verify-phone')
    def verify_phone(self, request, pk=None):
        """Administrator attests phone ownership after an out-of-band check."""
        with transaction.atomic():
            user = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
            if not user.phone:
                raise serializers.ValidationError({'phone': 'The account has no phone number.'})
            if user.role == User.Role.CLIENT:
                profile = Client.objects.select_for_update().filter(phone=user.phone).first()
                if profile and profile.user_id not in (None, user.pk):
                    raise serializers.ValidationError({'phone': 'This client is linked to another account.'})
                if profile and Client.objects.filter(user=user).exclude(pk=profile.pk).exists():
                    raise serializers.ValidationError({'phone': 'This account already has another client profile.'})
            user.phone_verified = True
            user.save(update_fields=['phone_verified'])
        return Response(UserSerializer(user).data)


class PracticeAreaViewSet(viewsets.ModelViewSet):
    queryset = PracticeArea.objects.all()
    serializer_class = PracticeAreaSerializer
    permission_classes = [PracticeAreaPermission]


class LawyerProfileViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin, viewsets.GenericViewSet):
    serializer_class = LawyerProfileSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['jurisdiction', 'is_verified', 'practice_areas']

    def get_queryset(self):
        queryset = LawyerProfile.objects.select_related('user').prefetch_related('practice_areas').order_by('id')
        if not self.request.user.is_authenticated:
            return queryset.none()
        if is_admin(self.request.user):
            return queryset
        if self.request.user.role in LAWYER_ROLES:
            return queryset.filter(user=self.request.user)
        return queryset.none()

    @action(detail=False, methods=['get', 'patch'], url_path='me', filter_backends=[])
    def me(self, request):
        profile = get_object_or_404(self.get_queryset(), user=request.user)
        if request.method == 'PATCH':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(self.get_serializer(profile).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsSuperAdmin],
            serializer_class=LawyerVerificationSerializer)
    def verification(self, request, pk=None):
        serializer = LawyerVerificationSerializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClientViewSet(viewsets.ModelViewSet):
    """External partners can read assigned clients, never create or edit them."""
    def create(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied("Only the primary lawyer may create clients.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied("Partners cannot edit client records.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied("Partners cannot edit client records.")
        return super().partial_update(request, *args, **kwargs)

    serializer_class = ClientSerializer
    permission_classes = [CanManageClients]
    filterset_fields = ['city']

    def get_queryset(self):
        queryset = Client.objects.select_related('user', 'created_by')
        if not self.request.user.is_authenticated:
            return queryset.none()
        if is_admin(self.request.user):
            return queryset
        if self.request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            return queryset.filter(matters__lead_lawyer__user=self.request.user).distinct()
        return queryset.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Partners cannot create clients. The lead lawyer assigns existing clients.')
        from apps.activity.services import record_action
        with transaction.atomic():
            instance = serializer.save(created_by=self.request.user)
            record_action(self.request, 'client.created', instance)

    def perform_update(self, serializer):
        if self.request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Partners cannot change client master records.')
        from apps.activity.services import record_action
        with transaction.atomic():
            instance = serializer.save()
            record_action(self.request, 'client.updated', instance, {'fields': list(serializer.validated_data)})

    def perform_destroy(self, instance):
        if not is_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only administrators may delete client profiles.')
        if instance.user_id:
            raise serializers.ValidationError('A linked client profile cannot be deleted independently of its account.')
        instance.delete()


class MyClientProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ClientSelfSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def perform_update(self, serializer):
        if self.request.user.role == User.Role.EXTERNAL_SUBCONTRACTOR:
            raise PermissionDenied('Partners cannot change client master records.')
        from apps.activity.services import record_action
        with transaction.atomic():
            instance = serializer.save()
            record_action(self.request, 'client.updated', instance, {'fields': list(serializer.validated_data)})

    def get_object(self):
        if self.request.user.role != User.Role.CLIENT:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('This endpoint is for client accounts.')
        return get_object_or_404(Client, user=self.request.user)
