import uuid
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


def evidence_path(instance, filename):
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    return f'protected/dossiers/{instance.matter_id}/{uuid.uuid4().hex}{ext}'


class Matter(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Ouvert'
        IN_PROGRESS = 'IN_PROGRESS', 'En cours'
        ON_HOLD = 'ON_HOLD', 'En attente'
        CLOSED = 'CLOSED', 'Clôturé'
    client = models.ForeignKey('accounts.Client', on_delete=models.PROTECT, related_name='matters')
    reference = models.CharField(max_length=32, unique=True, editable=False)
    title = models.CharField(max_length=250)
    matter_type = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    opposing_party = models.CharField(max_length=250, blank=True)
    jurisdiction = models.CharField(max_length=180, blank=True)
    court_reference = models.CharField(max_length=140, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    opened_at = models.DateField()
    closed_at = models.DateField(null=True, blank=True)
    lead_lawyer = models.ForeignKey('accounts.LawyerProfile', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_matters')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'DOS-' + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)


class MatterDocument(models.Model):
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=evidence_path, validators=[FileExtensionValidator(['pdf','jpg','jpeg','png','doc','docx','xlsx','txt'])])
    category = models.CharField(max_length=80, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class MatterEvent(models.Model):
    class Kind(models.TextChoices):
        HEARING = 'HEARING', 'Audience'
        DEADLINE = 'DEADLINE', 'Échéance'
        MEETING = 'MEETING', 'Réunion'
        OTHER = 'OTHER', 'Autre'
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=220)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    location = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['start_at']


class MatterNote(models.Model):
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name='notes')
    body = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Brouillon'
        ISSUED = 'ISSUED', 'Émise'
        PARTIAL = 'PARTIAL', 'Partiellement payée'
        PAID = 'PAID', 'Payée'
        CANCELLED = 'CANCELLED', 'Annulée'
    reference = models.CharField(max_length=32, unique=True, editable=False)
    matter = models.ForeignKey(Matter, on_delete=models.PROTECT, related_name='invoices')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    issue_date = models.DateField()
    due_date = models.DateField()
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='DZD')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'FAC-' + uuid.uuid4().hex[:12].upper()
        super().save(*args, **kwargs)
    class Meta:
        ordering = ['-created_at']


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    description = models.CharField(max_length=300)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)


class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateField()
    method = models.CharField(max_length=50)
    reference = models.CharField(max_length=140, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class GoogleCalendarConnection(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_calendar_connection')
    encrypted_refresh_token = models.TextField()
    calendar_id = models.CharField(max_length=255, default='primary')
    connected_at = models.DateTimeField(auto_now_add=True)


class GoogleEventLink(models.Model):
    connection = models.ForeignKey(GoogleCalendarConnection, on_delete=models.CASCADE)
    event = models.ForeignKey(MatterEvent, on_delete=models.CASCADE)
    google_event_id = models.CharField(max_length=255)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['connection','event'], name='unique_google_matter_event')]


class GoogleAppointmentLink(models.Model):
    """Stable per-user Google event mapping for client appointments."""
    connection = models.ForeignKey(GoogleCalendarConnection, on_delete=models.CASCADE)
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.CASCADE)
    google_event_id = models.CharField(max_length=255)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['connection', 'appointment'], name='unique_google_client_appointment')]
