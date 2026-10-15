from rest_framework.routers import DefaultRouter
from .views import MatterViewSet, MatterAssignmentViewSet

router = DefaultRouter()
router.register('matters', MatterViewSet, basename='matter')
router.register('assignments', MatterAssignmentViewSet, basename='matterassignment')

urlpatterns = router.urls