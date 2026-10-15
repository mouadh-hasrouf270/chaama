from django.conf import settings
from django.db import models
import uuid
from apps.matters.models import Matter


class CalendarEvent(models.Model):
    class EventType(models.TextChoices):
        HEARING = 'HEARING', 'Hearing'
        PROCEDURAL_DEADLINE = 'PROCEDURAL_DEADLINE', 'Procedural Deadline'
        STATUTORY_DEADLINE = 'STATUTORY_DEADLINE', 'Statutory Deadline'
        OTHER = 'OTHER', 'Other'

    matter = models.ForeignKey(
        Matter,
        on_delete=models.CASCADE,
        related_name='calendar_events',
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    is_completed = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_calendar_events',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['event_date']

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.title} ({self.event_date.date()})"


class PracticeArea(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'À confirmer'
        CONFIRMED = 'CONFIRMED', 'Confirmé'
        CANCELLED = 'CANCELLED', 'Annulé'
        COMPLETED = 'COMPLETED', 'Terminé'

    class ConsultationType(models.TextChoices):
        OFFICE = 'OFFICE', 'Au cabinet'
        VIDEO = 'VIDEO', 'Visioconférence'
        PHONE = 'PHONE', 'Téléphone'

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    practice_area = models.ForeignKey(PracticeArea, on_delete=models.PROTECT)
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField()
    consultation_type = models.CharField(max_length=10, choices=ConsultationType.choices)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    legal_topic = models.CharField(max_length=255)
    description = models.TextField(max_length=5000)
    opposing_party = models.CharField(max_length=255, blank=True)
    consent = models.BooleanField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_at', 'pk']
        constraints = [
            # All non-cancelled appointments reserve one office-wide fixed slot.
            models.UniqueConstraint(fields=['start_at'], condition=~models.Q(status='CANCELLED'),
                                    name='unique_reserved_appointment_slot'),
            models.CheckConstraint(condition=models.Q(end_at__gt=models.F('start_at')),
                                   name='appointment_positive_duration'),
        ]
