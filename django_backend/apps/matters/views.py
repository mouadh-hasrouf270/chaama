# Keep legacy routes on the same guarded implementation; no alternate write path.
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from .office_views import MatterViewSet
from .models import MatterAssignment
from .serializers import MatterAssignmentSerializer
from .office_access import OfficeAccess, is_admin


class MatterAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = MatterAssignmentSerializer
    permission_classes = [OfficeAccess]

    def get_queryset(self):
        if not is_admin(self.request.user):
            raise PermissionDenied('Seul l’administrateur peut gérer les affectations.')
        return MatterAssignment.objects.all()

    def perform_create(self, serializer):
        self.get_queryset()
        if not serializer.validated_data['associate'].is_staff:
            raise PermissionDenied('Le collaborateur doit disposer d’un accès personnel autorisé.')
        serializer.save(assigned_by=self.request.user)

    def perform_update(self, serializer):
        if not serializer.validated_data.get('associate', serializer.instance.associate).is_staff:
            raise PermissionDenied('Le collaborateur doit disposer d’un accès personnel autorisé.')
        serializer.save()
