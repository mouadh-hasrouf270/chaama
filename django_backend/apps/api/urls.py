from django.urls import include, path
from apps.practice.api import MatterViewSet, DocumentViewSet, EventViewSet, NoteViewSet, InvoiceViewSet
from rest_framework.routers import DefaultRouter
from apps.appointments.views import AppointmentViewSet, CalendarBlockViewSet, WorkingHoursViewSet
from apps.intakes.views import IntakeViewSet, PublicBookingView, PublicBookingRequestView
from apps.assistance.views import AssistanceRequestViewSet
from apps.activity.views import NotificationViewSet, AuditLogViewSet
from .views import PublicPracticeAreaViewSet, PublicLawyerViewSet, PartnerViewSet, ClientDirectoryViewSet, DashboardView

from apps.practice.google_calendar import GoogleCalendarStart, GoogleCalendarCallback, GoogleCalendarStatus, GoogleCalendarSync

app_name = 'api_v1'
router = DefaultRouter()
router.register('public/practice-areas', PublicPracticeAreaViewSet, basename='public-practice-area')
router.register('public/lawyers', PublicLawyerViewSet, basename='public-lawyer')
router.register('partners', PartnerViewSet, basename='partner')
router.register('clients', ClientDirectoryViewSet, basename='client')
router.register('matters', MatterViewSet, basename='matter')
router.register('matter-documents', DocumentViewSet, basename='matter-document')
router.register('matter-events', EventViewSet, basename='matter-event')
router.register('matter-notes', NoteViewSet, basename='matter-note')
router.register('invoices', InvoiceViewSet, basename='invoice')
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('calendar-blocks', CalendarBlockViewSet, basename='calendar-block')
router.register('working-hours', WorkingHoursViewSet, basename='working-hours')
router.register('intakes', IntakeViewSet, basename='intake')
router.register('assistance-requests', AssistanceRequestViewSet, basename='assistance-request')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('audit-logs', AuditLogViewSet, basename='audit-log')
urlpatterns = [
    path('public/bookings/', PublicBookingView.as_view(), name='public-booking'),
    path('public/booking-requests/', PublicBookingRequestView.as_view(), name='public-booking-request'),
    path('google-calendar/start/', GoogleCalendarStart.as_view()),
    path('google-calendar/callback/', GoogleCalendarCallback.as_view()),
    path('google-calendar/status/', GoogleCalendarStatus.as_view()),
    path('google-calendar/sync/', GoogleCalendarSync.as_view()),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', include(router.urls)),
]

