from rest_framework.routers import DefaultRouter
from .views import CalendarEventViewSet

router = DefaultRouter()
router.register('calendar-events', CalendarEventViewSet, basename='calendarevent')

urlpatterns = router.urls