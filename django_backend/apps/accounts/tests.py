from importlib import import_module
from types import SimpleNamespace

from django.apps import apps as django_apps
from django.db import connection
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Client, LawyerProfile, PracticeArea, User


class ProfileAPITests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', role=User.Role.SUPER_ADMIN)
        self.lawyer = User.objects.create_user(username='lawyer', role=User.Role.INTERNAL_ASSOCIATE)
        self.other_lawyer = User.objects.create_user(username='other', role=User.Role.EXTERNAL_SUBCONTRACTOR)

    def register(self, **overrides):
        data = {'username': 'newclient', 'password': 'Some-secure-pass-938!',
                'first_name': 'Amine', 'last_name': 'Ben', 'phone': '+213555123456'}
        data.update(overrides)
        return self.client.post(reverse('register'), data, format='json')

    def offline_client(self, **overrides):
        data = {'first_name': 'Original', 'last_name': 'Client', 'phone': '+213555123456',
                'notes': 'Private case details', 'created_by': self.lawyer}
        data.update(overrides)
        return Client.objects.create(**data)

    def test_registration_creates_profile_and_hashes_password(self):
        response = self.register()
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(username='newclient')
        self.assertTrue(user.check_password('Some-secure-pass-938!'))
        self.assertEqual(user.client_profile.first_name, 'Amine')
        self.assertNotIn('password', response.data)
        self.assertFalse(user.phone_verified)

    def test_privileged_public_registration_rejected(self):
        for role in [User.Role.SUPER_ADMIN, User.Role.INTERNAL_ASSOCIATE, User.Role.EXTERNAL_SUBCONTRACTOR]:
            response = self.register(role=role)
            self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='newclient').exists())

    def test_weak_password_and_invalid_phone_rejected(self):
        self.assertEqual(self.register(password='123').status_code, 400)
        self.assertEqual(self.register(phone='0555123456').status_code, 400)
        self.assertEqual(self.register(phone='').status_code, 400)

    def test_matching_profile_waits_for_verification_then_links_once(self):
        original = self.offline_client()
        response = self.register(phone='00 213 (555) 123-456')
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(username='newclient')
        original.refresh_from_db()
        self.assertIsNone(original.user_id)
        self.assertEqual(Client.objects.count(), 1)
        self.client.force_authenticate(user)
        me = self.client.get(reverse('me'))
        self.assertTrue(me.data['client_link_pending'])
        self.assertEqual(self.client.get(reverse('my-client-profile')).status_code, 404)
        verify_url = reverse('managed-user-verify-phone', args=[user.pk])
        self.assertEqual(self.client.post(verify_url).status_code, 403)
        self.client.force_authenticate(self.admin)
        for _ in range(2):
            self.assertEqual(self.client.post(verify_url).status_code, 200)
        original.refresh_from_db()
        user.refresh_from_db()
        self.assertEqual(original.user_id, user.pk)
        self.assertTrue(user.phone_verified)
        self.assertEqual(original.notes, 'Private case details')
        self.assertEqual(original.first_name, 'Original')
        self.assertEqual(original.created_by, self.lawyer)
        self.assertEqual(Client.objects.count(), 1)
        self.client.force_authenticate(user)
        response = self.client.get(reverse('my-client-profile'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('notes', response.data)
        self.assertNotIn('created_by', response.data)

    def test_duplicate_registered_phone_rejected_after_normalization(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register(username='duplicate', phone='00213 555 123456').status_code, 400)
        self.assertEqual(Client.objects.count(), 1)

    def test_client_self_update_cannot_change_phone_or_notes(self):
        self.register()
        user = User.objects.get(username='newclient')
        self.client.force_authenticate(user)
        response = self.client.patch(reverse('my-client-profile'), {
            'city': 'Algiers', 'phone': '+213666123456', 'notes': 'Overwrite', 'user': self.admin.pk,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        profile = Client.objects.get(user=user)
        self.assertEqual(profile.city, 'Algiers')
        self.assertEqual(profile.phone, '+213555123456')
        self.assertEqual(profile.notes, '')
        self.assertEqual(self.client.get(reverse('client-list')).status_code, 403)

    def test_lawyer_profiles_created_for_both_roles(self):
        self.assertTrue(LawyerProfile.objects.filter(user=self.lawyer).exists())
        self.assertTrue(LawyerProfile.objects.filter(user=self.other_lawyer).exists())
        self.assertFalse(LawyerProfile.objects.filter(user=self.admin).exists())
        self.lawyer.save()
        self.assertEqual(LawyerProfile.objects.filter(user=self.lawyer).count(), 1)

    def test_lawyer_can_update_own_profile_and_practice_areas_only(self):
        area = PracticeArea.objects.create(name='Family law')
        self.client.force_authenticate(self.lawyer)
        response = self.client.patch(reverse('lawyer-me'), {
            'bio': 'Family lawyer', 'practice_areas': [area.pk], 'is_verified': True,
            'user': self.other_lawyer.pk,
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        profile = LawyerProfile.objects.get(user=self.lawyer)
        self.assertFalse(profile.is_verified)
        self.assertEqual(list(profile.practice_areas.all()), [area])
        url = reverse('lawyer-detail', args=[self.other_lawyer.lawyer_profile.pk])
        self.assertEqual(self.client.patch(url, {'bio': 'Hacked'}).status_code, 404)
        self.assertEqual(self.client.patch(reverse('lawyer-me'), {'years_experience': -1}).status_code, 400)
        self.assertEqual(self.client.patch(reverse('lawyer-me'), {'practice_areas': [999]}).status_code, 400)

    def test_only_admin_verifies_lawyers(self):
        url = reverse('lawyer-verification', args=[self.lawyer.lawyer_profile.pk])
        self.client.force_authenticate(self.lawyer)
        self.assertEqual(self.client.patch(url, {'is_verified': True}).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.patch(url, {}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'is_verified': True}).status_code, 200)
        self.lawyer.lawyer_profile.refresh_from_db()
        self.assertTrue(self.lawyer.lawyer_profile.is_verified)

    def test_practice_area_read_and_admin_crud(self):
        url = reverse('practice-area-list')
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_authenticate(self.lawyer)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.post(url, {'name': 'Civil law'}).status_code, 403)
        self.client.force_authenticate(self.admin)
        response = self.client.post(url, {'name': 'Civil law'})
        self.assertEqual(response.status_code, 201)
        detail = reverse('practice-area-detail', args=[response.data['id']])
        self.assertEqual(self.client.patch(detail, {'description': 'Civil matters'}).status_code, 200)
        self.assertEqual(self.client.delete(detail).status_code, 204)

    def test_offline_client_creation_scope_and_duplicate_phone(self):
        self.client.force_authenticate(self.lawyer)
        data = {'first_name': 'Ali', 'last_name': 'Ben', 'phone': '00213 555 123456',
                'created_by': self.other_lawyer.pk, 'user': self.admin.pk}
        response = self.client.post(reverse('client-list'), data)
        self.assertEqual(response.status_code, 201, response.data)
        profile = Client.objects.get(pk=response.data['id'])
        self.assertIsNone(profile.user_id)
        self.assertEqual(profile.created_by, self.lawyer)
        self.assertEqual(self.client.post(reverse('client-list'), data).status_code, 400)
        url = reverse('client-detail', args=[profile.pk])
        self.assertEqual(self.client.patch(url, {'city': 'Oran'}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(self.other_lawyer)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(len(self.client.get(reverse('client-list')).data), 0)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_admin_creates_lawyer_account(self):
        self.client.force_authenticate(self.lawyer)
        url = reverse('managed-user-list')
        self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.client.force_authenticate(self.admin)
        response = self.client.post(url, {
            'username': 'newlawyer', 'password': 'Some-secure-pass-938!',
            'first_name': 'Sara', 'last_name': 'Ben', 'phone': '+213666123456',
            'role': User.Role.EXTERNAL_SUBCONTRACTOR,
        })
        self.assertEqual(response.status_code, 201, response.data)
        self.assertTrue(LawyerProfile.objects.filter(user__username='newlawyer').exists())

    def test_user_deletion_preserves_client_and_deletes_lawyer_profile(self):
        self.register()
        user = User.objects.get(username='newclient')
        profile_id = user.client_profile.pk
        user.delete()
        self.assertIsNone(Client.objects.get(pk=profile_id).user_id)
        lawyer_id = self.lawyer.lawyer_profile.pk
        self.lawyer.delete()
        self.assertFalse(LawyerProfile.objects.filter(pk=lawyer_id).exists())

    def test_linked_client_phone_and_deletion_are_protected(self):
        self.register()
        profile = Client.objects.get(user__username='newclient')
        self.client.force_authenticate(self.admin)
        url = reverse('client-detail', args=[profile.pk])
        self.assertEqual(self.client.patch(url, {'phone': '+213666123456'}).status_code, 400)
        self.assertEqual(self.client.delete(url).status_code, 400)

    def test_legacy_account_enrolls_phone_and_receives_profile(self):
        user = User.objects.create_user(username='legacy')
        self.client.force_authenticate(user)
        response = self.client.post(reverse('enroll-phone'), {
            'phone': '+213555123456', 'first_name': 'Legacy', 'last_name': 'Client',
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIsNotNone(response.data['client_profile_id'])
        self.assertEqual(self.client.post(reverse('enroll-phone'), {
            'phone': '+213666123456', 'first_name': 'Legacy', 'last_name': 'Client',
        }).status_code, 400)

    def test_legacy_phone_enrollment_does_not_claim_existing_profile(self):
        profile = self.offline_client()
        user = User.objects.create_user(username='legacy')
        self.client.force_authenticate(user)
        response = self.client.post(reverse('enroll-phone'), {
            'phone': '+213555123456', 'first_name': 'Legacy', 'last_name': 'Client',
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['client_link_pending'])
        profile.refresh_from_db()
        self.assertIsNone(profile.user_id)

    def test_anonymous_cannot_access_profiles(self):
        for name in ['me', 'my-client-profile', 'client-list', 'lawyer-list', 'managed-user-list']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 401)

    def test_jwt_login_access_and_logout(self):
        self.register()
        response = self.client.post('/api/token/', {
            'username': 'newclient', 'password': 'Some-secure-pass-938!',
        })
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])
        self.assertEqual(self.client.get(reverse('my-client-profile')).status_code, 200)
        self.assertEqual(self.client.post(reverse('logout'), {'refresh': response.data['refresh']}).status_code, 200)
        self.assertEqual(self.client.post('/api/token/refresh/', {'refresh': response.data['refresh']}).status_code, 401)


class AdminAccessTests(APITestCase):
    """The Django admin flags and the application role must agree."""
    password = 'Some-secure-pass-938!'

    def assert_admin_access(self, user):
        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.SUPER_ADMIN)
        self.assertTrue(user.is_staff and user.is_superuser)

    def test_command_line_superuser_becomes_super_admin(self):
        self.assert_admin_access(User.objects.create_superuser('root', password=self.password))

    def test_super_admin_role_can_log_into_django_admin(self):
        self.assert_admin_access(User.objects.create_user('boss', password=self.password, role=User.Role.SUPER_ADMIN))
        response = self.client.post('/admin/login/', {'username': 'boss', 'password': self.password, 'next': '/admin/'})
        self.assertRedirects(response, '/admin/', fetch_redirect_response=False)
        self.assertEqual(self.client.get('/admin/').status_code, 200)
        self.assertEqual(self.client.get('/admin/accounts/user/').status_code, 200)

    def test_command_line_superuser_reaches_api_dashboard_as_admin(self):
        User.objects.create_superuser('root', password=self.password)
        token = self.client.post('/api/token/', {'username': 'root', 'password': self.password}).data
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token['access'])
        self.assertEqual(self.client.get(reverse('me')).data['role'], User.Role.SUPER_ADMIN)
        self.assertEqual(self.client.get('/api/v1/dashboard/').status_code, 200)

    def test_super_admin_created_through_the_api_can_use_django_admin(self):
        self.client.force_authenticate(User.objects.create_superuser('root', password=self.password))
        response = self.client.post(reverse('managed-user-list'), {
            'username': 'second', 'password': self.password, 'first_name': 'Sam', 'last_name': 'Ali',
            'phone': '+213555000111', 'role': User.Role.SUPER_ADMIN}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assert_admin_access(User.objects.get(username='second'))

    def test_other_roles_are_left_alone(self):
        for role in [User.Role.CLIENT, User.Role.INTERNAL_ASSOCIATE, User.Role.EXTERNAL_SUBCONTRACTOR]:
            user = User.objects.create_user(f'user-{role}', role=role)
            user.refresh_from_db()
            self.assertEqual(user.role, role)
            self.assertFalse(user.is_staff or user.is_superuser)

    def test_migration_repairs_existing_accounts(self):
        superuser_client = User.objects.create_user('a', role=User.Role.CLIENT)
        plain_super_admin = User.objects.create_user('b', role=User.Role.SUPER_ADMIN)
        lawyer = User.objects.create_user('c', role=User.Role.INTERNAL_ASSOCIATE)
        client = User.objects.create_user('d', role=User.Role.CLIENT)
        # Rows as they were stored before the fix (`update()` skips `save()`).
        User.objects.filter(pk=superuser_client.pk).update(is_staff=True, is_superuser=True)
        User.objects.filter(pk=plain_super_admin.pk).update(is_staff=False, is_superuser=False)
        migration = import_module('apps.accounts.migrations.0006_sync_admin_access')
        migration.sync_admin_access(django_apps, SimpleNamespace(connection=connection))
        self.assert_admin_access(superuser_client)
        self.assert_admin_access(plain_super_admin)
        for user, role in [(lawyer, User.Role.INTERNAL_ASSOCIATE), (client, User.Role.CLIENT)]:
            user.refresh_from_db()
            self.assertEqual(user.role, role)
            self.assertFalse(user.is_staff or user.is_superuser)
