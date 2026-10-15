from django.conf import settings
from django.db import models
import uuid
from django.core.files.storage import FileSystemStorage


def private_storage():
    return FileSystemStorage(location=settings.PRIVATE_FILE_ROOT)


def document_path(instance, filename):
    from pathlib import Path
    return f'matters/{instance.matter_id}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class Client(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                blank=True, related_name='client_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, unique=True, null=True)
    secondary_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['last_name', 'first_name', 'pk']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Matter(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACTIVE = "ACTIVE", "Active"
        WAITING = "WAITING", "Waiting"
        CLOSED = "CLOSED", "Closed"
        ARCHIVED = "ARCHIVED", "Archived"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    reference = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="matters_as_client",
        limit_choices_to={"role": "CLIENT"},
        null=True, blank=True,
    )
    client_profile = models.ForeignKey(Client, on_delete=models.PROTECT, null=True, related_name='matters')
    version = models.PositiveIntegerField(default=1)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    opened_at = models.DateField(null=True, blank=True)
    closed_at = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_matters",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} — {self.title}"


class MatterAssignment(models.Model):
    matter = models.ForeignKey(
        Matter,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    associate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matter_assignments",
        limit_choices_to={"role": "INTERNAL_ASSOCIATE"},
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="matter_assignments_created",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["matter", "associate"],
                name="unique_matter_associate_assignment",
            )
        ]

    def __str__(self):
        return f"{self.associate.username} → {self.matter.title}"


class MatterHistory(models.Model):
    matter = models.ForeignKey(Matter, on_delete=models.PROTECT, related_name='history')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class MatterDocument(models.Model):
    matter = models.ForeignKey(Matter, on_delete=models.PROTECT, related_name='documents')
    file = models.FileField(storage=private_storage, upload_to=document_path)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class Invoice(models.Model):
    reference = models.CharField(max_length=50, unique=True)
    matter = models.ForeignKey(Matter, on_delete=models.PROTECT, related_name='invoices')
    status = models.CharField(max_length=20, default='DRAFT', choices=[(s, s) for s in
        ['DRAFT', 'ISSUED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED']])
    currency = models.CharField(max_length=3, default='DZD')
    issuer_name = models.CharField(max_length=200, default='CH2MA')
    issuer_address = models.TextField(blank=True)
    customer_name = models.CharField(max_length=250, blank=True)
    customer_address = models.TextField(blank=True)
    lines = models.JSONField(default=list)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    issue_date = models.DateField(null=True)
    due_date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-created_at', '-pk']


class InvoicePayment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    request_id = models.UUIDField(unique=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    method = models.CharField(max_length=20, choices=[('CASH', 'Espèces'), ('TRANSFER', 'Virement'), ('CHEQUE', 'Chèque')])
    reference = models.CharField(max_length=150, blank=True)
    paid_on = models.DateField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.CheckConstraint(condition=models.Q(amount__gt=0), name='payment_positive_amount')]
