from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError, close_old_connections, transaction
from django.test import TransactionTestCase
from rest_framework.test import APITestCase, APIClient

from .models import Appointment, PracticeArea

NOW = datetime(2026, 10, 11, 7, 0, tzinfo=ZoneInfo('Africa/Algiers'))


class BookingTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.clock = patch('django.utils.timezone.now', return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.area = PracticeArea.objects.create(name='Droit civil', slug='civil')
        self.staff = get_user_model().objects.create_user('staff', role='INTERNAL_ASSOCIATE', is_staff=True)
        self.payload = {'practice_area': self.area.pk, 'start_at': '2026-10-11T09:00:00+01:00',
                        'consultation_type': 'PHONE', 'full_name': 'Client Test', 'email': 'test@example.com',
                        'phone': '+213 555 123 456', 'legal_topic': 'Consultation',
                        'description': 'Une demande de consultation.', 'consent': True}

    def book(self, **overrides):
        return self.client.post('/api/v1/public/bookings/', {**self.payload, **overrides}, format='json')

    def slots(self, day='2026-10-11'):
        return self.client.get('/api/v1/appointments/availability/', {'date': day, 'specialty': 'civil'})

    def test_public_config_and_areas(self):
        self.assertEqual(self.client.get('/api/v1/public/booking-config/').data['timezone'], 'Africa/Algiers')
        self.assertIn('civil', [a['slug'] for a in self.client.get('/api/v1/public/practice-areas/').data])

    def test_booking_receipt_and_availability_do_not_leak_contact_details(self):
        before = self.slots().data
        self.assertEqual(len(before), 8)
        response = self.book()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertNotIn('email', response.data)
        self.assertEqual(len(self.slots().data), 7)
        self.assertNotIn('client_name', self.slots().data[0])
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.end_at - appointment.start_at, timedelta(hours=1))

    def test_duplicate_is_conflict_even_across_specialties(self):
        self.assertEqual(self.book().status_code, 201)
        other = PracticeArea.objects.create(name='Autre', slug='other')
        self.assertEqual(self.book(practice_area=other.pk).status_code, 409)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_database_enforces_exclusivity(self):
        self.book()
        first = Appointment.objects.get()
        first.pk = None
        import uuid
        first.reference = uuid.uuid4()
        with self.assertRaises(IntegrityError), transaction.atomic():
            first.save()

    def test_closed_days_past_and_horizon(self):
        for day in ['2026-10-09', '2026-10-16', '2027-03-01']:
            with self.subTest(day=day):
                self.assertEqual(self.slots(day).data, [])
                self.assertEqual(self.book(start_at=f'{day}T09:00:00+01:00').status_code, 400)

    def test_rejects_off_grid_outside_hours_and_near_term(self):
        for time in ['08:00', '09:30', '17:00']:
            with self.subTest(time=time):
                self.assertEqual(self.book(start_at=f'2026-10-11T{time}:00+01:00').status_code, 400)
        with patch('django.utils.timezone.now', return_value=NOW.replace(hour=8, minute=30)):
            self.assertEqual(self.book().status_code, 400)

    def test_validation_of_contact_and_consent(self):
        for values in [{'email': 'invalid'}, {'phone': 'abc'}, {'phone': '123'}, {'consent': False},
                       {'full_name': ' '}, {'description': 'short'}, {'consultation_type': 'INVALID'}]:
            with self.subTest(values=values):
                self.assertEqual(self.book(**values).status_code, 400)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_inactive_specialty_rejected(self):
        self.area.is_active = False
        self.area.save()
        self.assertEqual(self.book().status_code, 400)
        self.assertEqual(self.slots().status_code, 400)

    def test_untrusted_status_and_end_are_ignored(self):
        self.book(status='CONFIRMED', end_at='2099-01-01T10:00:00Z')
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.status, 'PENDING')
        self.assertEqual(appointment.end_at - appointment.start_at, timedelta(hours=1))

    def test_malformed_availability(self):
        self.assertEqual(self.slots('not-a-date').status_code, 400)
        self.assertEqual(self.client.get('/api/v1/appointments/availability/').status_code, 400)

    def test_private_endpoints_require_trusted_staff(self):
        for role in ['CLIENT', 'EXTERNAL_SUBCONTRACTOR', 'SUPER_ADMIN', 'INTERNAL_ASSOCIATE']:
            user = get_user_model().objects.create_user(role, role=role)
            self.client.force_authenticate(user)
            for path in ['/api/v1/appointments/', '/api/v1/dashboard/']:
                self.assertEqual(self.client.get(path).status_code, 403)
            self.assertEqual(self.client.post('/api/v1/appointments/1/cancel/').status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/v1/appointments/').status_code, 401)

    def test_shared_calendar_dashboard_confirm_and_cancel(self):
        self.book()
        appointment = Appointment.objects.get()
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/v1/appointments/').data[0]['id'], appointment.pk)
        dashboard = self.client.get('/api/v1/dashboard/').data
        self.assertEqual(dashboard['pending_intakes'], 1)
        self.assertEqual(len(dashboard['today_appointments']), 1)
        self.assertEqual(dashboard['upcoming_count'], 1)
        self.assertEqual(self.client.post(f'/api/v1/appointments/{appointment.pk}/confirm/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/dashboard/').data['confirmed_count'], 1)
        self.assertEqual(self.client.post(f'/api/v1/appointments/{appointment.pk}/cancel/').status_code, 200)
        self.assertEqual(self.client.get('/api/v1/dashboard/').data['upcoming_count'], 0)
        self.assertEqual(len(self.slots().data), 8)
        self.assertEqual(self.book().status_code, 201)

    def test_terminal_state_cannot_be_reactivated(self):
        self.book()
        appointment = Appointment.objects.get()
        self.client.force_authenticate(self.staff)
        path = f'/api/v1/appointments/{appointment.pk}/'
        self.assertEqual(self.client.post(path + 'cancel/').status_code, 200)
        self.assertEqual(self.client.post(path + 'cancel/').status_code, 200)
        self.assertEqual(self.client.post(path + 'confirm/').status_code, 409)
        self.assertEqual(self.client.post(path + 'unknown/').status_code, 404)

    def test_completion_requires_confirmed_and_finished(self):
        self.book()
        appointment = Appointment.objects.get()
        self.client.force_authenticate(self.staff)
        path = f'/api/v1/appointments/{appointment.pk}/'
        self.assertEqual(self.client.post(path + 'complete/').status_code, 409)
        self.client.post(path + 'confirm/')
        self.assertEqual(self.client.post(path + 'complete/').status_code, 409)
        with patch('django.utils.timezone.now', return_value=NOW.replace(hour=11)):
            self.assertEqual(self.client.post(path + 'complete/').status_code, 200)

    def test_range_filter_and_validation(self):
        self.book()
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/v1/appointments/?from=2026-10-12&to=2026-10-13').data, [])
        for query in ['from=invalid', 'from=2026-10-12&to=2026-10-11', 'from=2026-10-12&to=2028-10-11']:
            self.assertEqual(self.client.get('/api/v1/appointments/?' + query).status_code, 400)

    def test_timezone_offsets_represent_same_slot(self):
        self.assertEqual(self.book(start_at='2026-10-11T08:00:00Z').status_code, 201)
        self.assertEqual(self.book(start_at='2026-10-11T10:00:00+02:00').status_code, 409)

    def test_public_booking_throttled(self):
        for _ in range(20):
            self.book(email='invalid')
        self.assertEqual(self.book().status_code, 429)


class ConcurrentBookingTests(TransactionTestCase):
    def test_two_simultaneous_requests_reserve_only_one_slot(self):
        cache.clear()
        area = PracticeArea.objects.create(name='Concurrency', slug='concurrency')
        barrier = Barrier(2)
        payload = {'practice_area': area.pk, 'start_at': '2026-10-11T09:00:00+01:00',
                   'consultation_type': 'OFFICE', 'full_name': 'Test', 'email': 'test@example.com',
                   'phone': '+213555123456', 'legal_topic': 'Test',
                   'description': 'Test concurrent booking', 'consent': True}

        def reserve():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return APIClient().post('/api/v1/public/bookings/', payload, format='json').status_code
            finally:
                close_old_connections()

        with patch('django.utils.timezone.now', return_value=NOW), ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: reserve(), range(2)))
        self.assertEqual(sorted(results), [201, 409])
        self.assertEqual(Appointment.objects.count(), 1)
