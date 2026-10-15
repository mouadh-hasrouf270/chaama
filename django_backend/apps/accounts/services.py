import re

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Client, LawyerProfile, User


LAWYER_ROLES = (User.Role.INTERNAL_ASSOCIATE, User.Role.EXTERNAL_SUBCONTRACTOR)


def normalize_phone(value):
    """Require an international number; never guess a user's country."""
    value = re.sub(r'[\s().-]', '', value.strip())
    if value.startswith('00'):
        value = '+' + value[2:]
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', value):
        raise ValidationError('Use an international phone number, e.g. +213555123456.')
    return value


@transaction.atomic
def ensure_profile(user):
    user = User.objects.select_for_update().get(pk=user.pk)
    if user.role in LAWYER_ROLES:
        LawyerProfile.objects.get_or_create(user=user)
    elif user.role == User.Role.CLIENT and user.phone:
        if Client.objects.filter(user=user).exists():
            return
        profile, created = Client.objects.get_or_create(
            phone=user.phone,
            defaults={'user': user, 'first_name': user.first_name,
                      'last_name': user.last_name, 'email': user.email},
        )
        if not created and user.phone_verified:
            Client.objects.filter(pk=profile.pk, user__isnull=True).update(user=user)
