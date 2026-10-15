from django.db import models
from .storage import PrivateEvidenceStorage, evidence_path


class Intake(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        REVIEW_REQUIRED = 'REVIEW_REQUIRED', 'Review required'
        REVIEWED = 'REVIEWED', 'Reviewed'

    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.PROTECT, related_name='intake')
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    legal_topic = models.CharField(max_length=200)
    description = models.TextField()
    opposing_party = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    conflict_warning = models.CharField(max_length=20, default='NO_MATCH')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']


class IntakeEvidence(models.Model):
    intake = models.ForeignKey(Intake, on_delete=models.CASCADE, related_name='evidence')
    file = models.FileField(storage=PrivateEvidenceStorage(), upload_to=evidence_path)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

