from django.conf import settings
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import F, Q


class LawyerAvailability(models.Model):
    lawyer = models.ForeignKey('accounts.LawyerProfile', on_delete=models.CASCADE, related_name='working_hours')
    weekday = models.PositiveSmallIntegerField(validators=[MaxValueValidator(6)], help_text='Monday=0, Sunday=6; times use BOOKING_TIME_ZONE.')
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['weekday', 'start_time']
        constraints = [
            models.CheckConstraint(condition=Q(end_time__gt=F('start_time')), name='working_hours_positive'),
            models.CheckConstraint(condition=Q(weekday__lte=6), name='working_weekday_valid'),
        ]


class Appointment(models.Model):
    class ConsultationType(models.TextChoices):
        OFFICE = 'OFFICE', 'Office'
        VIDEO = 'VIDEO', 'Video'
        PHONE = 'PHONE', 'Phone'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'

    lawyer = models.ForeignKey('accounts.LawyerProfile', on_delete=models.PROTECT, null=True, blank=True, related_name='appointments')
    client = models.ForeignKey('accounts.Client', on_delete=models.PROTECT, null=True, blank=True, related_name='appointments')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField()
    consultation_type = models.CharField(max_length=10, choices=ConsultationType.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    meeting_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_at', 'id']
        constraints = [models.CheckConstraint(condition=Q(end_at__gt=F('start_at')), name='appointment_positive_duration')]


class CalendarBlock(models.Model):
    lawyer = models.ForeignKey('accounts.LawyerProfile', on_delete=models.CASCADE, related_name='calendar_blocks')
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    reason = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_at', 'id']
        constraints = [models.CheckConstraint(condition=Q(end_at__gt=F('start_at')), name='calendar_block_positive_duration')]



class BookingRequest(models.Model):
    """Unassigned appointment enquiry; NOT a confirmed calendar reservation."""
    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        CONTACTED = 'CONTACTED', 'Contacted'
        CONVERTED = 'CONVERTED', 'Converted to appointment'
        CLOSED = 'CLOSED', 'Closed'

    appointment = models.OneToOneField('Appointment', null=True, blank=True, on_delete=models.PROTECT, related_name='source_request')
    client = models.ForeignKey('accounts.Client', null=True, blank=True, on_delete=models.SET_NULL, related_name='booking_requests')
    practice_area = models.ForeignKey('accounts.PracticeArea', on_delete=models.PROTECT)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=32)
    legal_topic = models.CharField(max_length=200)
    description = models.TextField()
    opposing_party = models.CharField(max_length=250, blank=True)
    requested_date = models.DateField()
    preferred_time = models.TimeField()
    consultation_type = models.CharField(max_length=10, choices=Appointment.ConsultationType.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
