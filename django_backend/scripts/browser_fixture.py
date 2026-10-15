"""Disposable backend for the browser smoke test; never uses the project database."""
import os
import sys
import tempfile
from datetime import time
from pathlib import Path

backend = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.conf import settings

# Keep the directory alive for the whole server process.
temporary = tempfile.TemporaryDirectory(prefix='chaama-browser-')
settings.DATABASES['default']['NAME'] = str(Path(temporary.name) / 'test.sqlite3')
settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
settings.CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:5174']
settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
settings.PRIVATE_EVIDENCE_ROOT = Path(temporary.name) / 'evidence'

import django
django.setup()
from django.core.management import call_command
from apps.accounts.models import User, Client, PracticeArea
from apps.appointments.models import LawyerAvailability
from apps.activity.models import Notification

call_command('migrate', verbosity=0)
user = User.objects.create_user(username='browser-lawyer', password='Browser-test-only-927!',
                                role='INTERNAL_ASSOCIATE', first_name='Browser', last_name='Lawyer')
profile = user.lawyer_profile
profile.is_verified = True
profile.availability_status = 'AVAILABLE'
profile.save()
area = PracticeArea.objects.create(name='Browser Practice', slug='browser-practice')
profile.practice_areas.add(area)
for weekday in range(7):
    LawyerAvailability.objects.create(lawyer=profile, weekday=weekday, start_time=time(9), end_time=time(17))
Client.objects.create(phone='+213555123456', first_name='Browser', last_name='Client',
                      email='browser@example.com', created_by=user)
Notification.objects.create(user=user, type='TEST', title='Browser notification', message='Test notification')
call_command('runserver', '127.0.0.1:8000', use_reloader=False)

