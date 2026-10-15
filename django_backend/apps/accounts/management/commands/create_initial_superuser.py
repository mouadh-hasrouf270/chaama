
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the first Chaama administrator"

    def handle(self, *args, **options):
        username = os.environ.get("INITIAL_ADMIN_USERNAME", "").strip()
        email = os.environ.get("INITIAL_ADMIN_EMAIL", "").strip()
        password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")

        if not username or not email or not password:
            raise CommandError("Missing initial administrator settings")

        if len(password) < 12:
            raise CommandError("Administrator password must contain at least 12 characters")

        User = get_user_model()

        if User.objects.filter(username=username).exists():
            self.stdout.write("Account already exists; no changes made")
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role=User.Role.SUPER_ADMIN,
        )

        self.stdout.write(
            self.style.SUCCESS("Chaama Super Admin created successfully")
        )
