from rest_framework import viewsets, permissions
from .models import CalendarEvent
from .serializers import CalendarEventSerializer


class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Role.SUPER_ADMIN:
            return CalendarEvent.objects.all()
        elif user.role == user.Role.INTERNAL_ASSOCIATE:
            return CalendarEvent.objects.filter(
                matter__assignments__associate=user
            ).distinct()
        elif user.role == user.Role.CLIENT:
            return CalendarEvent.objects.filter(matter__client=user)
        return CalendarEvent.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)