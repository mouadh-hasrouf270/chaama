from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenBlacklistView

from .views import (
    ClientViewSet, LawyerProfileViewSet, ManagedUserViewSet, MeView,
    MyClientProfileView, PracticeAreaViewSet, RegisterView, PhoneEnrollmentView,
)

router = DefaultRouter()
router.register('users', ManagedUserViewSet, basename='managed-user')
router.register('practice-areas', PracticeAreaViewSet, basename='practice-area')
router.register('lawyers', LawyerProfileViewSet, basename='lawyer')
router.register('clients', ClientViewSet, basename='client')

from . import partner_api
urlpatterns = [
    path('public-stats/', partner_api.public_stats),
    path('partner-applications/', partner_api.applications),
    path('partner-applications/apply/', partner_api.apply),
    path('partner-applications/<int:pk>/proof/', partner_api.proof),
    path('partner-applications/<int:pk>/decide/', partner_api.decide),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),
    path('me/phone/', PhoneEnrollmentView.as_view(), name='enroll-phone'),
    path('clients/me/', MyClientProfileView.as_view(), name='my-client-profile'),
    path('logout/', TokenBlacklistView.as_view(), name='logout'),
    path('', include(router.urls)),
]
