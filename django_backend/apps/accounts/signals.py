from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User
from .services import ensure_profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, raw=False, **kwargs):
    if not raw:
        ensure_profile(instance)
