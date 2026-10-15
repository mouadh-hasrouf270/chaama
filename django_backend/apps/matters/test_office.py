import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from django.contrib.auth import get_user_model
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from .models import Client, Matter, MatterDocument, MatterAssignment, Invoice, InvoicePayment


class OfficeTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user('admin', is_staff=True, role='SUPER_ADMIN')
        self.associate = User.objects.create_user('associate', is_staff=True, role='INTERNAL_ASSOCIATE')
        self.other = User.objects.create_user('other', is_staff=True, role='INTERNAL_ASSOCIATE')
        self.client.force_authenticate(self.admin)
        self.person = Client.objects.create(first_name='Test', last_name='Client', phone='+213555111222', created_by=self.admin)
        self.matter = Matter.objects.create(reference='DOS-TEST', title='Test matter', client_profile=self.person, created_by=self.admin)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        field = MatterDocument._meta.get_field('file')
        storage = field.storage
        field.storage = FileSystemStorage(location=temp.name)
        self.addCleanup(setattr, field, 'storage', storage)

    def invoice(self):
        response = self.client.post('/api/v1/invoices/', {
            'matter': self.matter.pk, 'issuer_name': 'Cabinet Test', 'due_date': str(timezone.localdate() + timedelta(days=10)),
            'lines': [{'description': 'Consultation', 'quantity': '2', 'unit_price': '1000.25'}], 'tax_rate': '19.00',
        }, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        return response.data

    def issue(self, invoice):
        response = self.client.post(f'/api/v1/invoices/{invoice["id"]}/status/', {'status': 'ISSUED', 'version': invoice['version']})
        self.assertEqual(response.status_code, 200, response.data)
        return response.data

    def payment(self, invoice, amount, **overrides):
        return self.client.post(f'/api/v1/invoices/{invoice["id"]}/payments/', {
            'amount': amount, 'method': 'TRANSFER', 'paid_on': str(timezone.localdate()),
            'request_id': str(uuid.uuid4()), 'version': invoice['version'], **overrides,
        })

    def test_client_without_user_normalizes_phone_and_detects_duplicate(self):
        data = {'first_name': 'Alice', 'last_name': 'Test', 'phone': '0555 222 333'}
        result = self.client.post('/api/v1/clients/', data)
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(result.data['phone'], '+213555222333')
        self.assertIsNone(Client.objects.get(pk=result.data['id']).user_id)
        self.assertEqual(self.client.post('/api/v1/clients/', {**data, 'phone': '+213555222333'}).status_code, 400)
        self.assertEqual(self.client.post('/api/v1/clients/', {**data, 'phone': 'abc'}).status_code, 400)

    def test_client_search_and_edit_stale_version(self):
        data = self.client.get('/api/v1/clients/?search=Client').data
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['matters_count'], 1)
        url = f'/api/v1/clients/{self.person.pk}/'
        self.assertEqual(self.client.patch(url, {'city': 'Alger', 'version': 1}).status_code, 200)
        self.assertEqual(self.client.patch(url, {'city': 'Other', 'version': 1}).status_code, 409)
        self.assertEqual(self.client.delete(url).status_code, 405)

    def test_untrusted_roles_and_anonymous_cannot_access(self):
        user = get_user_model().objects.create_user('untrusted', role='SUPER_ADMIN')
        self.client.force_authenticate(user)
        for path in ['/api/v1/clients/', '/api/v1/matters/', '/api/v1/invoices/', '/api/matters/', '/api/assignments/']:
            self.assertEqual(self.client.get(path).status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/v1/clients/').status_code, 401)

    def test_other_staff_cannot_access_case_client_invoice_or_document(self):
        invoice = self.invoice()
        self.client.force_authenticate(self.other)
        for path in [f'/api/v1/clients/{self.person.pk}/', f'/api/v1/matters/{self.matter.pk}/',
                     f'/api/v1/invoices/{invoice["id"]}/', f'/api/v1/matters/{self.matter.pk}/documents/']:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.post('/api/v1/matters/', {'title': 'Forged', 'client_profile': self.person.pk}).status_code, 400)

    def test_assigned_staff_can_read_but_not_issue_invoice(self):
        invoice = self.invoice()
        MatterAssignment.objects.create(matter=self.matter, associate=self.associate)
        self.client.force_authenticate(self.associate)
        self.assertEqual(self.client.get(f'/api/v1/matters/{self.matter.pk}/').status_code, 200)
        self.assertEqual(self.client.get(f'/api/v1/clients/{self.person.pk}/').status_code, 200)
        self.assertEqual(self.client.post(f'/api/v1/invoices/{invoice["id"]}/status/', {'status': 'ISSUED', 'version': 1}).status_code, 403)
        self.assertEqual(self.client.post('/api/assignments/', {'matter': self.matter.pk, 'associate': self.other.pk}).status_code, 403)

    def test_case_creation_edit_and_status_history(self):
        result = self.client.post('/api/v1/matters/', {'title': 'New case', 'client_profile': self.person.pk, 'status': 'ARCHIVED'})
        self.assertEqual(result.status_code, 201, result.data)
        self.assertEqual(result.data['status'], 'OPEN')
        url = f'/api/v1/matters/{result.data["id"]}/'
        edit = self.client.patch(url, {'description': 'Updated', 'version': 1})
        self.assertEqual(edit.status_code, 200)
        self.assertEqual(self.client.patch(url, {'status': 'CLOSED', 'version': 2}).status_code, 400)
        close = self.client.post(url + 'status/', {'status': 'CLOSED', 'version': 2})
        self.assertEqual(close.status_code, 200)
        self.assertIsNotNone(close.data['closed_at'])
        self.assertEqual(self.client.patch(url, {'title': 'Changed', 'version': 3}).status_code, 409)
        reopen = self.client.post(url + 'status/', {'status': 'ACTIVE', 'version': 3})
        self.assertEqual(reopen.status_code, 200)
        self.assertIsNone(reopen.data['closed_at'])
        self.assertEqual(len(self.client.get(url + 'history/').data), 4)

    def test_no_invalid_or_stale_status_transition(self):
        url = f'/api/v1/matters/{self.matter.pk}/status/'
        self.assertEqual(self.client.post(url, {'status': 'ARCHIVED', 'version': 1}).status_code, 409)
        self.assertEqual(self.client.post(url, {'status': 'ACTIVE', 'version': 1}).status_code, 200)
        self.assertEqual(self.client.post(url, {'status': 'CLOSED', 'version': 1}).status_code, 409)
        self.assertEqual(self.client.post(url, {'status': 'BAD', 'version': 2}).status_code, 400)

    def test_document_upload_download_and_scope(self):
        url = f'/api/v1/matters/{self.matter.pk}/documents/'
        file = SimpleUploadedFile('proof.pdf', b'%PDF-1.4\nTest\n%%EOF', content_type='application/pdf')
        upload = self.client.post(url, {'file': file, 'version': 1}, format='multipart')
        self.assertEqual(upload.status_code, 201, upload.data)
        self.assertNotIn('file', upload.data)
        path = url + str(upload.data['id']) + '/content/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4\nTest\n%%EOF')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(path).status_code, 404)

    def test_document_invalid_empty_oversize_and_closed_case(self):
        url = f'/api/v1/matters/{self.matter.pk}/documents/'
        for file in [SimpleUploadedFile('script.pdf', b'<script>alert(1)</script>'),
                     SimpleUploadedFile('empty.pdf', b''), SimpleUploadedFile('large.pdf', b'%PDF-' + b'x' * (10 * 1024 * 1024))]:
            self.assertEqual(self.client.post(url, {'file': file, 'version': 1}, format='multipart').status_code, 400)
        self.matter.status = 'CLOSED'; self.matter.save()
        self.assertEqual(self.client.post(url, {'file': SimpleUploadedFile('test.pdf', b'%PDF-1.4'), 'version': 1}, format='multipart').status_code, 409)
        self.assertEqual(MatterDocument.objects.count(), 0)

    def test_invoice_totals_snapshot_and_immutable_issued_invoice(self):
        invoice = self.invoice()
        self.assertEqual(invoice['subtotal'], '2000.50')
        self.assertEqual(invoice['tax_amount'], '380.10')
        self.assertEqual(invoice['total'], '2380.60')
        issued = self.issue(invoice)
        self.person.first_name = 'Changed'; self.person.save()
        result = self.client.get(f'/api/v1/invoices/{invoice["id"]}/').data
        self.assertEqual(result['customer_name'], 'Test Client')
        self.assertEqual(self.client.patch(f'/api/v1/invoices/{invoice["id"]}/', {'notes': 'Edit', 'version': issued['version']}).status_code, 409)

    def test_partial_full_payment_and_idempotent_retry(self):
        invoice = self.issue(self.invoice())
        key = str(uuid.uuid4())
        paid = self.payment(invoice, '1000.00', request_id=key)
        self.assertEqual(paid.status_code, 201, paid.data)
        self.assertEqual(paid.data['status'], 'PARTIALLY_PAID')
        self.assertEqual(self.payment(invoice, '1000.00', request_id=key).status_code, 200)
        self.assertEqual(self.payment(invoice, '999.00', request_id=key).status_code, 409)
        full = self.payment(paid.data, '1380.60')
        self.assertEqual(full.data['status'], 'PAID')
        self.assertEqual(full.data['balance'], '0.00')
        self.assertEqual(InvoicePayment.objects.count(), 2)
        self.assertEqual(self.client.post(f'/api/v1/invoices/{invoice["id"]}/status/', {'status': 'CANCELLED', 'version': full.data['version']}).status_code, 409)

    def test_no_overpayment_or_future_payment(self):
        invoice = self.issue(self.invoice())
        for amount in ['0', '-1', '9999']:
            self.assertEqual(self.payment(invoice, amount).status_code, 400)
        self.assertEqual(self.payment(invoice, '1', paid_on=str(timezone.localdate() + timedelta(days=1))).status_code, 400)
        self.assertEqual(InvoicePayment.objects.count(), 0)

    def test_cancel_rejects_payment_and_archive_requires_settled_invoices(self):
        invoice = self.invoice()
        self.matter.refresh_from_db()
        url = f'/api/v1/matters/{self.matter.pk}/status/'
        closed = self.client.post(url, {'status': 'CLOSED', 'version': self.matter.version}).data
        self.assertEqual(self.client.post(url, {'status': 'ARCHIVED', 'version': closed['version']}).status_code, 409)
        cancelled = self.client.post(f'/api/v1/invoices/{invoice["id"]}/status/', {'status': 'CANCELLED', 'version': invoice['version']}).data
        self.assertEqual(self.payment(cancelled, '1').status_code, 409)
        self.assertEqual(self.client.post(url, {'status': 'ARCHIVED', 'version': closed['version']}).status_code, 200)

    def test_invalid_invoice_lines_tax_and_scope(self):
        payload = {'matter': self.matter.pk, 'due_date': str(timezone.localdate()), 'lines': []}
        self.assertEqual(self.client.post('/api/v1/invoices/', payload, format='json').status_code, 400)
        payload['lines'] = [{'description': 'Test', 'quantity': '-1', 'unit_price': '10'}]
        self.assertEqual(self.client.post('/api/v1/invoices/', payload, format='json').status_code, 400)
        payload['lines'][0]['quantity'] = '1'; payload['tax_rate'] = 101
        self.assertEqual(self.client.post('/api/v1/invoices/', payload, format='json').status_code, 400)


class PaymentConcurrencyTests(TransactionTestCase):
    def test_concurrent_payments_do_not_overpay(self):
        user = get_user_model().objects.create_user('payment-admin', role='SUPER_ADMIN', is_staff=True)
        person = Client.objects.create(first_name='A', last_name='B', phone='+213555987654')
        matter = Matter.objects.create(reference='CONCURRENT', title='Test', client_profile=person)
        invoice = Invoice.objects.create(reference='FAC-TEST', matter=matter, status='ISSUED',
            total=Decimal('1000'), subtotal=Decimal('1000'), due_date=timezone.localdate(), issue_date=timezone.localdate())
        barrier = Barrier(2)
        def pay(_):
            close_old_connections()
            try:
                client = APIClient(); client.force_authenticate(user)
                barrier.wait(timeout=10)
                return client.post(f'/api/v1/invoices/{invoice.pk}/payments/', {
                    'amount': '700', 'paid_on': str(timezone.localdate()), 'method': 'CASH',
                    'request_id': str(uuid.uuid4()), 'version': 1}).status_code
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(pay, range(2)))
        self.assertEqual(sorted(results), [201, 409])
        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal('700'))
        self.assertEqual(invoice.payments.count(), 1)
