import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, time
from threading import Barrier
from types import SimpleNamespace

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework.exceptions import APIException
from apps.accounts.models import User, Client, PracticeArea
from apps.activity.models import AuditLog, Notification
from apps.assistance.models import AssistanceRequest
from apps.intakes.models import Intake
from apps.intakes.conflicts import flag_possible_conflict
from .models import Appointment, LawyerAvailability, CalendarBlock, BookingRequest
from .services import create_appointment

BASE = '/api/v1/'


class PlatformTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user(username='admin', role='SUPER_ADMIN')
        self.lawyer = User.objects.create_user(username='lawyer', role='INTERNAL_ASSOCIATE')
        self.external = User.objects.create_user(username='external', role='EXTERNAL_SUBCONTRACTOR')
        self.other = User.objects.create_user(username='other', role='EXTERNAL_SUBCONTRACTOR')
        self.user = User.objects.create_user(username='client', phone='+213555123456', first_name='Test', last_name='Client')
        self.area = PracticeArea.objects.create(name='Criminal Law', slug='criminal-law')
        self.profile = self.lawyer.lawyer_profile
        self.profile.is_verified = True
        self.profile.availability_status = 'AVAILABLE'
        self.profile.jurisdiction = 'Algiers'
        self.profile.save()
        self.profile.practice_areas.add(self.area)
        self.start = (timezone.now() + timedelta(days=2)).replace(hour=9, minute=0, second=0, microsecond=0)
        self.end = self.start + timedelta(minutes=30)
        LawyerAvailability.objects.create(lawyer=self.profile, weekday=self.start.weekday(),
                                          start_time=time(9), end_time=time(12))
        self.client.force_authenticate(self.user)

    def booking(self, **extra):
        return {'lawyer': self.profile.pk, 'start_at': self.start.isoformat(),
                'end_at': self.end.isoformat(), 'consultation_type': 'OFFICE', **extra}

    def make_appointment(self):
        response = self.client.post(BASE+'appointments/', self.booking(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def intake(self, appointment):
        return {'appointment': appointment, 'full_name': 'Test Client', 'email': 'test@example.com',
                'phone': '+213555123456', 'legal_topic': 'Advice', 'description': 'A detailed consultation request',
                'opposing_party': 'Unknown business'}

    def test_public_practice_areas_and_lawyers_hide_private_fields(self):
        PracticeArea.objects.create(name='Hidden', is_active=False)
        self.client.force_authenticate(None)
        response = self.client.get(BASE+'public/practice-areas/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['count'], 1)
        response = self.client.get(BASE+'public/lawyers/')
        self.assertEqual(response.data['count'], 1)
        for field in ['user', 'email', 'phone', 'password', 'bar_number']:
            self.assertNotIn(field, response.data['results'][0])
        self.assertEqual(self.client.get(BASE+f'public/lawyers/{self.external.lawyer_profile.pk}/').status_code, 404)

    def test_public_booking_request_without_available_lawyer(self):
        self.client.force_authenticate(None)
        before = Appointment.objects.count()
        day = timezone.localdate() + timedelta(days=3)
        response = self.client.post(BASE+'public/booking-requests/', {
            'practice_area': self.area.pk,
            'requested_date': day.isoformat(),
            'preferred_time': '14:30',
            'consultation_type': 'OFFICE',
            'full_name': 'New Booking Client',
            'email': 'newbooking@example.com',
            'phone': '+213555112233',
            'legal_topic': 'Première consultation — Contrat',
            'description': 'A proper legal consultation about a contract.',
            'consent': True,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'booked')
        self.assertTrue(response.data['assignment_pending'])
        self.assertEqual(Appointment.objects.count(), before + 1)
        appt = Appointment.objects.get(pk=response.data['appointment_reference'])
        self.assertIsNone(appt.lawyer)
        self.assertIsNotNone(appt.client)
        self.assertFalse(appt.client.user.has_usable_password())
        self.assertTrue(Intake.objects.filter(appointment=appt).exists())
        self.client.force_authenticate(self.admin)
        self.assertIn(appt.pk, [row['id'] for row in self.client.get(BASE+'appointments/').data['results']])

    def test_booking_request_rejects_missing_consent_and_past_date(self):
        self.client.force_authenticate(None)
        payload = {'practice_area': self.area.pk, 'requested_date': (timezone.localdate() - timedelta(days=1)).isoformat(),
                   'preferred_time': '12:00', 'consultation_type': 'PHONE', 'full_name': 'Client X',
                   'email': 'clientx@example.com', 'phone': '+213555112244', 'legal_topic': 'Advice',
                   'description': 'Detailed legal enquiry is described here.', 'consent': True}
        self.assertEqual(self.client.post(BASE+'public/booking-requests/', payload, format='json').status_code, 400)
        payload['requested_date'] = (timezone.localdate() + timedelta(days=1)).isoformat()
        payload['consent'] = False
        self.assertEqual(self.client.post(BASE+'public/booking-requests/', payload, format='json').status_code, 400)
        self.assertEqual(BookingRequest.objects.count(), 0)

    def test_clients_search_pagination_and_scope(self):
        Client.objects.create(first_name='Owned', last_name='Person', phone='+213666123456', created_by=self.external)
        Client.objects.create(first_name='Secret', last_name='Person', phone='+213777123456', created_by=self.other)
        self.client.force_authenticate(self.external)
        response = self.client.get(BASE+'clients/', {'search': 'Owned'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(self.client.get(BASE+'clients/', {'search': 'Secret'}).data['count'], 0)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(BASE+'clients/').status_code, 403)

    def test_client_updates_are_audited_without_notes(self):
        self.client.force_authenticate(self.lawyer)
        response = self.client.post(BASE+'clients/', {'first_name': 'New', 'last_name': 'Client', 'phone': '+213666123456', 'notes': 'secret'}, format='json')
        self.assertEqual(response.status_code, 201)
        response = self.client.patch(BASE+f"clients/{response.data['id']}/", {'city': 'Algiers'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditLog.objects.filter(action__startswith='client.').count(), 2)
        self.assertNotIn('secret', str(list(AuditLog.objects.values())))

    def test_appointment_create_forces_own_client_and_pending_status(self):
        response = self.client.post(BASE+'appointments/', self.booking(client=999, status='CONFIRMED'), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['client'], self.user.client_profile.pk)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertTrue(Notification.objects.filter(user=self.lawyer, type='APPOINTMENT_CREATED').exists())
        self.assertTrue(AuditLog.objects.filter(action='appointment.created').exists())

    def test_overlapping_booking_is_rejected_and_adjacent_allowed(self):
        self.make_appointment()
        response = self.client.post(BASE+'appointments/', self.booking(), format='json')
        self.assertEqual(response.status_code, 409)
        response = self.client.post(BASE+'appointments/', self.booking(start_at=(self.start+timedelta(minutes=15)).isoformat()), format='json')
        self.assertEqual(response.status_code, 409)
        response = self.client.post(BASE+'appointments/', self.booking(start_at=self.end.isoformat(), end_at=(self.end+timedelta(minutes=30)).isoformat()), format='json')
        self.assertEqual(response.status_code, 201)

    def test_working_hours_and_positive_duration_required(self):
        for data in [self.booking(end_at=self.start.isoformat()),
                     self.booking(start_at=(self.start-timedelta(hours=1)).isoformat()),
                     self.booking(start_at=(self.start-timedelta(days=4)).isoformat(), end_at=(self.end-timedelta(days=4)).isoformat())]:
            self.assertEqual(self.client.post(BASE+'appointments/', data, format='json').status_code, 400)

    def test_calendar_block_affects_booking_and_availability(self):
        self.client.force_authenticate(self.lawyer)
        response = self.client.post(BASE+'calendar-blocks/', {'lawyer': self.profile.pk, 'start_at': self.start.isoformat(), 'end_at': self.end.isoformat(), 'reason': 'Private'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.client.force_authenticate(None)
        response = self.client.get(BASE+'appointments/availability/', {'date': self.start.date().isoformat(), 'lawyer': self.profile.pk})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data), 5)
        self.assertNotIn('Private', str(response.data))
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(BASE+'appointments/', self.booking(), format='json').status_code, 409)

    def test_block_cannot_overlap_existing_booking_or_another_lawyers_calendar(self):
        self.make_appointment()
        self.client.force_authenticate(self.lawyer)
        data = {'lawyer': self.profile.pk, 'start_at': self.start.isoformat(), 'end_at': self.end.isoformat()}
        self.assertEqual(self.client.post(BASE+'calendar-blocks/', data, format='json').status_code, 409)
        self.client.force_authenticate(self.external)
        self.assertEqual(self.client.post(BASE+'calendar-blocks/', data, format='json').status_code, 400)

    def test_working_hours_permissions(self):
        self.client.force_authenticate(self.external)
        self.assertEqual(self.client.post(BASE+'working-hours/', {'lawyer': self.profile.pk, 'weekday': 1, 'start_time': '09:00', 'end_time': '12:00'}).status_code, 400)
        self.client.force_authenticate(self.lawyer)
        self.assertEqual(self.client.post(BASE+'working-hours/', {'lawyer': self.profile.pk, 'weekday': 1, 'start_time': '12:00', 'end_time': '09:00'}).status_code, 400)

    def test_availability_subtracts_appointments_and_cancel_restores_slot(self):
        pk = self.make_appointment()
        params = {'date': self.start.date().isoformat(), 'specialty': self.area.slug}
        self.assertEqual(len(self.client.get(BASE+'appointments/availability/', params).data), 5)
        url = BASE+f'appointments/{pk}/cancel/'
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(len(self.client.get(BASE+'appointments/availability/', params).data), 6)

    def test_appointment_scope_and_status_permissions(self):
        pk = self.make_appointment()
        url = BASE+f'appointments/{pk}/'
        self.assertEqual(self.client.patch(url, {'status': 'CONFIRMED'}, format='json').status_code, 403)
        self.client.force_authenticate(self.external)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_authenticate(self.lawyer)
        self.assertEqual(self.client.patch(url, {'status': 'CONFIRMED'}, format='json').status_code, 200)

    def test_reschedule_rechecks_overlap(self):
        pk = self.make_appointment()
        second = self.client.post(BASE+'appointments/', self.booking(start_at=self.end.isoformat(), end_at=(self.end+timedelta(minutes=30)).isoformat()), format='json')
        response = self.client.patch(BASE+f"appointments/{second.data['id']}/", {'start_at': self.start.isoformat()}, format='json')
        self.assertEqual(response.status_code, 409)

    def test_intake_and_evidence_access(self):
        pk = self.make_appointment()
        response = self.client.post(BASE+'intakes/', self.intake(pk), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        intake_id = response.data['id']
        self.assertNotIn('conflict_warning', response.data)
        self.assertEqual(self.client.post(BASE+'intakes/', self.intake(pk), format='json').status_code, 400)
        with tempfile.TemporaryDirectory() as directory:
            from apps.intakes.models import IntakeEvidence
            from django.core.files.storage import FileSystemStorage
            storage = IntakeEvidence._meta.get_field('file').storage
            old_location = storage._location
            storage._location = directory
            storage.__dict__.pop('base_location', None)
            storage.__dict__.pop('location', None)
            try:
                upload = SimpleUploadedFile('proof.pdf', b'%PDF-1.7\nExample evidence', content_type='application/pdf')
                response = self.client.post(BASE+f'intakes/{intake_id}/files/', {'file': upload}, format='multipart')
                self.assertEqual(response.status_code, 201, response.data)
                self.assertNotIn('file', response.data)
                url = BASE+f"intakes/{intake_id}/files/{response.data['id']}/download/"
                self.client.force_authenticate(self.external)
                self.assertEqual(self.client.get(url).status_code, 404)
                self.client.force_authenticate(None)
                self.assertEqual(self.client.get(url).status_code, 401)
                self.client.force_authenticate(self.lawyer)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn('attachment', response['Content-Disposition'])
                b''.join(response.streaming_content)
                response.close()
                self.assertTrue(AuditLog.objects.filter(action='intake.evidence_accessed').exists())
            finally:
                storage._location = old_location
                storage.__dict__.pop('base_location', None)
                storage.__dict__.pop('location', None)

    def test_invalid_file_and_size_rejected(self):
        pk = self.make_appointment()
        intake_id = self.client.post(BASE+'intakes/', self.intake(pk), format='json').data['id']
        url = BASE+f'intakes/{intake_id}/files/'
        for file in [SimpleUploadedFile('x.html', b'<script>bad</script>', content_type='text/html'),
                     SimpleUploadedFile('x.pdf', b'not pdf', content_type='application/pdf')]:
            self.assertEqual(self.client.post(url, {'file': file}, format='multipart').status_code, 400)
        with override_settings(INTAKE_MAX_FILE_SIZE=5):
            file = SimpleUploadedFile('x.pdf', b'%PDF-too large', content_type='application/pdf')
            self.assertEqual(self.client.post(url, {'file': file}, format='multipart').status_code, 400)

    def test_intake_cannot_use_another_users_appointment(self):
        pk = self.make_appointment()
        self.client.force_authenticate(self.external)
        self.assertEqual(self.client.post(BASE+'intakes/', self.intake(pk), format='json').status_code, 400)

    def test_public_booking_is_atomic_and_has_no_private_receipt(self):
        self.client.force_authenticate(None)
        data = {**self.booking(), **self.intake(None), 'practice_area': self.area.pk, 'consent': True}
        data.pop('appointment')
        response = self.client.post(BASE+'public/bookings/', data, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data, {'status': 'submitted'})
        appointment = Appointment.objects.get()
        self.assertIsNone(appointment.client_id)
        self.assertEqual(Intake.objects.count(), 1)
        self.assertEqual(self.client.post(BASE+'public/bookings/', data, format='json').status_code, 409)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_public_booking_creates_unverified_client_account(self):
        self.client.force_authenticate(None)
        data = {**self.booking(), **self.intake(None), 'practice_area': self.area.pk, 'consent': True}
        data.pop('appointment')
        data.update(full_name='Nadia Benali', email='nadia@example.com', phone='+213666111222')
        response = self.client.post(BASE+'public/bookings/', data, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        account = User.objects.get(phone='+213666111222')
        self.assertEqual(account.role, User.Role.CLIENT)
        self.assertEqual((account.first_name, account.last_name), ('Nadia', 'Benali'))
        self.assertFalse(account.phone_verified)
        self.assertFalse(account.has_usable_password())
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.client.user_id, account.pk)
        self.assertEqual(Intake.objects.get().appointment_id, appointment.pk)
        self.assertNotIn('password', response.data)

    def test_public_booking_does_not_take_over_existing_profile(self):
        self.client.force_authenticate(None)
        profile = Client.objects.create(first_name='Private', last_name='Person',
                                        phone='+213666111333', notes='secret')
        data = {**self.booking(), **self.intake(None), 'practice_area': self.area.pk, 'consent': True}
        data.pop('appointment')
        data.update(full_name='Fake Name', email='fake@example.com', phone=profile.phone)
        response = self.client.post(BASE+'public/bookings/', data, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        profile.refresh_from_db()
        self.assertIsNone(profile.user_id)
        self.assertEqual(profile.notes, 'secret')
        self.assertFalse(User.objects.filter(phone=profile.phone).exists())
        self.assertIsNone(Appointment.objects.get().client_id)

    def test_public_booking_invalid_intake_creates_nothing(self):
        self.client.force_authenticate(None)
        data = {**self.booking(), **self.intake(None), 'practice_area': self.area.pk, 'consent': False}
        self.assertEqual(self.client.post(BASE+'public/bookings/', data, format='json').status_code, 400)
        self.assertEqual(Appointment.objects.count(), 0)

    def test_partner_filtering(self):
        profile = self.external.lawyer_profile
        profile.jurisdiction = 'Algiers'
        profile.is_verified = True
        profile.availability_status = 'AVAILABLE'
        profile.save()
        profile.practice_areas.add(self.area)
        self.client.force_authenticate(self.lawyer)
        response = self.client.get(BASE+'partners/', {'specialty': 'criminal-law', 'jurisdiction': 'algiers', 'available': 'true', 'verified': 'true'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], profile.pk)

    def assistance(self):
        self.client.force_authenticate(self.external)
        response = self.client.post(BASE+'assistance-requests/', {
            'title': 'Help', 'description': 'Detailed help request', 'assistance_type': 'Consultation',
            'jurisdiction': 'Algiers', 'opposing_party': 'Unknown other party', 'proposed_fee': '100.00',
            'fee_share_percentage': '20.00'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data['id']

    def test_assistance_owner_scope_and_admin_review(self):
        pk = self.assistance()
        url = BASE+f'assistance-requests/{pk}/'
        self.assertNotIn('conflict_warning', self.client.get(url).data)
        self.assertEqual(self.client.post(url+'approve/').status_code, 403)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_authenticate(self.lawyer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(url+'approve/', {}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url+'decline/').status_code, 400)
        self.assertTrue(Notification.objects.filter(user=self.external, type='ASSISTANCE_ACCEPTED').exists())

    def test_conflict_is_only_warning_and_requires_human_acknowledgement(self):
        self.assertEqual(flag_possible_conflict('TEST CLIENT'), 'POSSIBLE_MATCH')
        pk = self.assistance()
        AssistanceRequest.objects.filter(pk=pk).update(opposing_party='Test Client')
        self.client.force_authenticate(self.admin)
        url = BASE+f'assistance-requests/{pk}/approve/'
        self.assertEqual(self.client.post(url, {}, format='json').status_code, 400)
        self.assertEqual(self.client.post(url, {'acknowledge_conflict': True}, format='json').status_code, 200)

    def test_assistance_decline_notifies_owner_and_validates_fee(self):
        pk = self.assistance()
        url = BASE+f'assistance-requests/{pk}/decline/'
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_authenticate(self.admin)
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'DECLINED')
        self.assertEqual(response.data['reviewed_by'], self.admin.pk)
        self.assertTrue(Notification.objects.filter(user=self.external, type='ASSISTANCE_DECLINED').exists())
        self.client.force_authenticate(self.external)
        response = self.client.post(BASE+'assistance-requests/', {
            'title': 'Help', 'description': 'Details', 'assistance_type': 'Advice',
            'jurisdiction': 'Algiers', 'proposed_fee': '-1', 'fee_share_percentage': '101',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('proposed_fee', response.data)
        self.assertIn('fee_share_percentage', response.data)

    def test_intake_review_and_view_are_audited(self):
        pk = self.make_appointment()
        response = self.client.post(BASE+'intakes/', self.intake(pk), format='json')
        url = BASE+f"intakes/{response.data['id']}/"
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action='intake.viewed').exists())
        self.assertEqual(self.client.post(url+'review/', {'status': 'REVIEWED'}, format='json').status_code, 403)
        self.client.force_authenticate(self.lawyer)
        self.assertEqual(self.client.post(url+'review/', {'status': 'REVIEWED'}, format='json').status_code, 200)
        self.assertEqual(self.client.get(BASE+'dashboard/').data['pending_intakes'], 0)

    def test_notifications_read_and_read_all_are_scoped(self):
        own = Notification.objects.create(user=self.user, type='TEST', title='Own', message='Own')
        other = Notification.objects.create(user=self.external, type='TEST', title='Other', message='Other')
        self.assertEqual(self.client.get(BASE+'notifications/').data['count'], 1)
        self.assertEqual(self.client.post(BASE+f'notifications/{other.pk}/read/').status_code, 404)
        self.assertEqual(self.client.post(BASE+f'notifications/{own.pk}/read/').status_code, 200)
        self.assertEqual(self.client.post(BASE+'notifications/read-all/').status_code, 200)
        other.refresh_from_db()
        self.assertFalse(other.is_read)

    def test_audit_api_and_model_are_append_only(self):
        self.make_appointment()
        self.assertEqual(self.client.get(BASE+'audit-logs/').status_code, 403)
        self.client.force_authenticate(self.admin)
        log = AuditLog.objects.first()
        self.assertEqual(self.client.get(BASE+'audit-logs/').status_code, 200)
        for method in [self.client.patch, self.client.delete]:
            self.assertEqual(method(BASE+f'audit-logs/{log.pk}/').status_code, 405)
        with self.assertRaises(TypeError):
            log.delete()
        with self.assertRaises(TypeError):
            AuditLog.objects.filter(pk=log.pk).update(action='changed')

    def test_dashboard_real_data_is_scoped(self):
        self.make_appointment()
        response = self.client.get(BASE+'dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['upcoming_appointments']), 1)
        self.assertNotIn('matters', response.data)
        self.client.force_authenticate(self.external)
        self.assertEqual(len(self.client.get(BASE+'dashboard/').data['upcoming_appointments']), 0)

    def test_private_endpoints_require_authentication(self):
        self.client.force_authenticate(None)
        for path in ['clients/', 'appointments/', 'intakes/', 'partners/', 'assistance-requests/', 'notifications/', 'audit-logs/', 'dashboard/', 'calendar-blocks/', 'working-hours/']:
            self.assertEqual(self.client.get(BASE+path).status_code, 401, path)


class ConcurrentBookingTests(TransactionTestCase):
    def test_simultaneous_requests_never_double_book(self):
        lawyer = User.objects.create_user(username='concurrent', role='INTERNAL_ASSOCIATE')
        profile = lawyer.lawyer_profile
        profile.is_verified = True
        profile.availability_status = 'AVAILABLE'
        profile.save()
        start = (timezone.now()+timedelta(days=3)).replace(hour=9, minute=0, second=0, microsecond=0)
        LawyerAvailability.objects.create(lawyer=profile, weekday=start.weekday(), start_time=time(9), end_time=time(12))
        barrier = Barrier(2)
        def book():
            close_old_connections()
            user = User.objects.get(pk=lawyer.pk)
            lawyer_profile = user.lawyer_profile
            request = SimpleNamespace(user=user, META={})
            barrier.wait(timeout=10)
            try:
                create_appointment({'lawyer': lawyer_profile, 'start_at': start, 'end_at': start+timedelta(minutes=30),
                                    'consultation_type': 'OFFICE'}, request)
                return 201
            except APIException as exc:
                return exc.status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: book(), range(2)))
        self.assertEqual(sorted(responses), [201, 409])
        self.assertEqual(Appointment.objects.count(), 1)

class PublicBookingConversionTests(APITestCase):
    def test_requested_time_becomes_real_booking_when_lawyer_is_available(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from django.conf import settings
        area = PracticeArea.objects.create(name='Civil', slug='civil')
        lawyer_user = User.objects.create_user(username='booking_lawyer', role='INTERNAL_ASSOCIATE')
        profile = lawyer_user.lawyer_profile
        profile.is_verified = True
        profile.availability_status = 'AVAILABLE'
        profile.save()
        profile.practice_areas.add(area)
        day = timezone.localdate() + timedelta(days=4)
        LawyerAvailability.objects.create(lawyer=profile, weekday=day.weekday(), start_time=time(9), end_time=time(12))
        response = self.client.post(BASE+'public/booking-requests/', {
            'practice_area': area.pk, 'requested_date': day.isoformat(),
            'preferred_time': '10:00', 'consultation_type': 'OFFICE',
            'full_name': 'Appointment Test', 'email': 'booked@example.com',
            'phone': '+213555300001', 'legal_topic': 'Legal consultation',
            'description': 'Description of a legal consultation for booking.', 'consent': True,
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'booked')
        appointment = Appointment.objects.get(pk=response.data['appointment_reference'])
        self.assertEqual(appointment.lawyer_id, profile.pk)
        self.assertIsNotNone(appointment.client_id)
        self.assertTrue(hasattr(appointment, 'intake'))
        self.assertEqual(BookingRequest.objects.count(), 0)
