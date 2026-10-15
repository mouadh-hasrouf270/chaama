from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        INTERNAL_ASSOCIATE = 'INTERNAL_ASSOCIATE', 'Internal Associate'
        EXTERNAL_SUBCONTRACTOR = 'EXTERNAL_SUBCONTRACTOR', 'External Subcontractor'
        CLIENT = 'CLIENT', 'Client'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    phone = models.CharField(max_length=30, unique=True, null=True, blank=True)
    phone_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"

    def clean(self):
        super().clean()
        from .services import normalize_phone
        self.phone = normalize_phone(self.phone) if self.phone else None
        if self.pk:
            old_phone = type(self).objects.filter(pk=self.pk).values_list('phone', flat=True).first()
            if old_phone and self.phone != old_phone:
                raise ValidationError({'phone': 'Changing an enrolled phone requires a separate ownership verification flow.'})

    def sync_admin_access(self):
        """Keep the application role and the Django admin flags consistent.

        The API and frontend look at `role` while /admin/ only honours
        `is_staff`/`is_superuser`, so an account holding just one of them
        could reach one side but not the other (see `is_admin()`, which
        already treats both as administrators).
        """
        if self.is_superuser and self.role == self.Role.CLIENT:
            # `createsuperuser` leaves the default CLIENT role behind.
            self.role = self.Role.SUPER_ADMIN
        if self.role == self.Role.SUPER_ADMIN:
            self.is_staff = self.is_superuser = True

    def save(self, *args, **kwargs):
        self.clean()
        self.sync_admin_access()
        return super().save(*args, **kwargs)


class PracticeArea(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            from uuid import uuid4
            self.slug = f'{slugify(self.name)[:140] or "practice"}-{uuid4().hex[:12]}'
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LawyerProfile(models.Model):
    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        UNAVAILABLE = 'UNAVAILABLE', 'Unavailable'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='lawyers')
    availability_status = models.CharField(max_length=20, choices=AvailabilityStatus.choices, default=AvailabilityStatus.UNAVAILABLE)
    updated_at = models.DateTimeField(auto_now=True)
    bar_number = models.CharField(max_length=100, blank=True)
    bar_association = models.CharField(max_length=150, blank=True)
    jurisdiction = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    practice_areas = models.ManyToManyField(PracticeArea, blank=True, related_name='lawyers')

    def __str__(self):
        return str(self.user)


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, unique=True)
    secondary_phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_clients')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def clean(self):
        super().clean()
        from .services import normalize_phone
        self.phone = normalize_phone(self.phone)
        if self.secondary_phone:
            self.secondary_phone = normalize_phone(self.secondary_phone)

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)


class PartnerApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        APPROVED = 'APPROVED', 'Acceptée'
        REJECTED = 'REJECTED', 'Refusée'

    full_name = models.CharField(max_length=200)
    cabinet = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=35)
    bar_number = models.CharField(max_length=100)
    jurisdiction = models.CharField(max_length=150)
    specialties = models.JSONField(default=list)
    proof = models.FileField(upload_to='partner_proofs/%Y/%m/')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    account = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='partner_applications')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='partner_reviews')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
