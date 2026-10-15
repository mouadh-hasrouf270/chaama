from django.urls import path
from .booking_api import (PublicAreas, Availability, BookingConfig, PublicBooking,
                          AppointmentList, AppointmentTransition, BookingDashboard)

urlpatterns = [
    path('public/practice-areas/', PublicAreas.as_view()),
    path('public/booking-config/', BookingConfig.as_view()),
    path('public/bookings/', PublicBooking.as_view()),
    path('appointments/availability/', Availability.as_view()),
    path('appointments/', AppointmentList.as_view()),
    path('appointments/<int:pk>/<str:action>/', AppointmentTransition.as_view()),
    path('dashboard/', BookingDashboard.as_view()),
]
