"""Account provisioning for unauthenticated appointment bookings.

A public booking proves neither phone nor email ownership. Never attach existing
private client profiles to a newly provisioned user without verification.
"""
from uuid import uuid4

from django.db import transaction

from .models import Client, User
from .services import normalize_phone


def provision_booking_client(*, full_name, email, phone):
    """Return a client record when safe; create an unverified login identity.

    Existing accounts/profiles are NEVER overwritten or linked by a public
    request. Password activation requires a separately verified workflow.
    """
    phone = normalize_phone(phone)
    existing_user = User.objects.filter(phone=phone).first()
    existing_client = Client.objects.filter(phone=phone).first()
    if existing_user or existing_client:
        # Matching contact details are not evidence of account ownership.
        # The intake retains the submitted contact info independently.
        return None
    parts = full_name.strip().split(None, 1)
    first_name, last_name = parts[0][:100], (parts[1] if len(parts) > 1 else '')[:100]
    with transaction.atomic():
        user = User(username=f'client_{uuid4().hex}', first_name=first_name,
                    last_name=last_name, email=email, phone=phone,
                    role=User.Role.CLIENT, phone_verified=False)
        user.set_unusable_password()
        user.save()  # Signal provisions matching Client; no password or tokens exposed.
        return Client.objects.get(user=user)
