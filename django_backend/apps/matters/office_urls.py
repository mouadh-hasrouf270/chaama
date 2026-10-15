from rest_framework.routers import DefaultRouter
from .office_views import ClientViewSet, MatterViewSet, InvoiceViewSet

router = DefaultRouter()
router.register('clients', ClientViewSet, basename='office-client')
router.register('matters', MatterViewSet, basename='office-matter')
router.register('invoices', InvoiceViewSet, basename='office-invoice')
urlpatterns = router.urls
