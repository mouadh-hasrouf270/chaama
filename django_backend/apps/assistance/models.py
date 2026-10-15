from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class AssistanceRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        CONFLICT_REVIEW = 'CONFLICT_REVIEW', 'Conflict review'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'

    requesting_lawyer = models.ForeignKey('accounts.LawyerProfile', on_delete=models.PROTECT, related_name='assistance_requests')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assistance_type = models.CharField(max_length=100)
    jurisdiction = models.CharField(max_length=150)
    opposing_party = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    proposed_fee = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    fee_share_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    conflict_warning = models.CharField(max_length=20, default='NO_MATCH')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']

