"""Regression checks; run with `python manage.py test apps.practice`."""
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import Client
from .models import Matter, Invoice, InvoiceLine, Payment
from .api import totals

User=get_user_model()


class PracticeWorkflowTests(TestCase):
    def setUp(self):
        self.staff=User.objects.create_user(username='lawyer-practice',password='testPass123!',role='INTERNAL_ASSOCIATE')
        self.other=User.objects.create_user(username='other-practice',password='testPass123!',role='INTERNAL_ASSOCIATE')
        self.admin=User.objects.create_superuser(username='admin-practice',email='admin@example.test',password='testPass123!')
        self.client_record=Client.objects.create(first_name='Client',last_name='Example',phone='+213555889977',created_by=self.staff)
        self.matter=Matter.objects.create(client=self.client_record,title='Commercial dispute',opened_at=date.today(),created_by=self.staff)
        self.api=APIClient()

    def test_reference_and_visibility(self):
        self.assertTrue(self.matter.reference.startswith('DOS-'))
        self.api.force_authenticate(user=self.other)
        self.assertEqual(self.api.get('/api/v1/matters/').data, [] )
        self.assertEqual(self.api.get(f'/api/v1/matters/{self.matter.pk}/').status_code,404)
        self.api.force_authenticate(user=self.staff)
        self.assertEqual(self.api.get(f'/api/v1/matters/{self.matter.pk}/').status_code,200)

    def test_client_cannot_read_dossiers(self):
        user=User.objects.create_user(username='client-practice',password='testPass123!',role='CLIENT')
        self.api.force_authenticate(user=user)
        self.assertEqual(self.api.get('/api/v1/matters/').status_code,403)

    def test_note_scoping(self):
        self.api.force_authenticate(user=self.other)
        result=self.api.post('/api/v1/matter-notes/',{'matter':self.matter.pk,'body':'confidential'})
        self.assertEqual(result.status_code,400)

    def test_invoice_amounts_and_payments(self):
        invoice=Invoice.objects.create(matter=self.matter,issue_date=date.today(),due_date=date.today()+timedelta(days=10),tax_rate=19,created_by=self.staff)
        InvoiceLine.objects.create(invoice=invoice,description='Consultation',quantity=2,unit_price=Decimal('1000.00'))
        self.assertEqual(totals(invoice)[2],Decimal('2380.00'))
        self.api.force_authenticate(user=self.staff)
        self.assertEqual(self.api.post(f'/api/v1/invoices/{invoice.pk}/issue/').status_code,403)
        self.api.force_authenticate(user=self.admin)
        self.assertEqual(self.api.post(f'/api/v1/invoices/{invoice.pk}/issue/').status_code,200)
        self.assertEqual(self.api.post(f'/api/v1/invoices/{invoice.pk}/record_payment/',{'amount':'1000.00','paid_at':str(date.today()),'method':'VIREMENT'}).status_code,200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status,'PARTIAL')
        self.assertEqual(self.api.post(f'/api/v1/invoices/{invoice.pk}/record_payment/',{'amount':'3000.00','paid_at':str(date.today()),'method':'VIREMENT'}).status_code,400)
        self.assertEqual(self.api.post(f'/api/v1/invoices/{invoice.pk}/record_payment/',{'amount':'1380.00','paid_at':str(date.today()),'method':'VIREMENT'}).status_code,200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status,'PAID')

class PartnerAssignmentPermissionTests(TestCase):
    """Partners cannot self-assign or access unassigned client records."""
    def setUp(self):
        from apps.accounts.models import LawyerProfile
        self.admin = User.objects.create_superuser(username='assignment-admin', email='assignment@example.test', password='Strong!23456789')
        self.partner = User.objects.create_user(username='assignment-partner', password='Strong!23456789', role=User.Role.EXTERNAL_SUBCONTRACTOR)
        self.other_partner = User.objects.create_user(username='unassigned-partner', password='Strong!23456789', role=User.Role.EXTERNAL_SUBCONTRACTOR)
        self.profile = LawyerProfile.objects.create(user=self.partner)
        self.client_record = Client.objects.create(first_name='Restricted', last_name='Client', phone='+213555881234', created_by=self.admin)
        self.matter = Matter.objects.create(client=self.client_record, title='Private dispute', opened_at=date.today(), created_by=self.admin)
        self.api = APIClient()

    def test_partner_cannot_create_client_or_dossier(self):
        self.api.force_authenticate(user=self.partner)
        self.assertEqual(self.api.post('/api/v1/clients/', {'first_name':'Another','last_name':'Person','phone':'+213555881233'}).status_code, 403)
        self.assertEqual(self.api.post('/api/v1/matters/', {'client':self.client_record.pk, 'title':'Unauthorized','opened_at':str(date.today())}).status_code, 403)
        self.assertFalse(Matter.objects.filter(title='Unauthorized').exists())

    def test_assignment_controls_access_and_revocation(self):
        self.api.force_authenticate(user=self.partner)
        self.assertEqual(self.api.get(f'/api/v1/clients/{self.client_record.pk}/').status_code, 404)
        self.assertEqual(self.api.get(f'/api/v1/matters/{self.matter.pk}/').status_code, 404)
        self.api.force_authenticate(user=self.admin)
        response = self.api.patch(f'/api/v1/matters/{self.matter.pk}/', {'lead_lawyer':self.profile.pk}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.api.force_authenticate(user=self.partner)
        self.assertEqual(self.api.get(f'/api/v1/clients/{self.client_record.pk}/').status_code, 200)
        self.assertEqual(self.api.get(f'/api/v1/matters/{self.matter.pk}/').status_code, 200)
        self.assertEqual(self.api.patch(f'/api/v1/matters/{self.matter.pk}/', {'lead_lawyer':None}, format='json').status_code, 403)
        self.assertEqual(self.api.patch(f'/api/v1/clients/{self.client_record.pk}/', {'city':'Other'}, format='json').status_code, 403)
        self.assertEqual(self.api.post('/api/v1/matter-notes/', {'matter':self.matter.pk, 'body':'Case update'}, format='json').status_code, 201)
        self.api.force_authenticate(user=self.other_partner)
        self.assertEqual(self.api.get(f'/api/v1/matters/{self.matter.pk}/').status_code, 404)
        self.api.force_authenticate(user=self.admin)
        self.assertEqual(self.api.patch(f'/api/v1/matters/{self.matter.pk}/', {'lead_lawyer':None}, format='json').status_code, 200)
        self.api.force_authenticate(user=self.partner)
        self.assertEqual(self.api.get(f'/api/v1/matters/{self.matter.pk}/').status_code, 404)
        self.assertEqual(self.api.get(f'/api/v1/clients/{self.client_record.pk}/').status_code, 404)
