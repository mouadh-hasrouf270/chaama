from pathlib import Path
from django.conf import settings
from django.db import transaction, IntegrityError
from rest_framework.exceptions import ValidationError
from apps.activity.services import record_action, notify
from apps.appointments.models import Appointment
from apps.appointments.services import appointment_recipients, lock_calendar
from .conflicts import flag_possible_conflict
from .models import Intake, IntakeEvidence


def submit_intake(data, request):
    with transaction.atomic():
        # Serialize submissions against the appointment, including SQLite.
        if data['appointment'].lawyer_id:
            lock_calendar(data['appointment'].lawyer_id)
        appointment = Appointment.objects.get(pk=data['appointment'].pk)
        if appointment.status == 'CANCELLED':
            raise ValidationError({'appointment': 'This appointment is cancelled.'})
        if Intake.objects.filter(appointment=appointment).exists():
            raise ValidationError({'appointment': 'An intake already exists for this appointment.'})
        warning = flag_possible_conflict(data.get('opposing_party', ''))
        try:
            with transaction.atomic():
                intake = Intake.objects.create(
                    **data, conflict_warning=warning,
                    status='SUBMITTED' if warning == 'NO_MATCH' else 'REVIEW_REQUIRED')
        except IntegrityError:
            raise ValidationError({'appointment': 'An intake already exists for this appointment.'})
        record_action(request, 'intake.submitted', intake, {'warning': warning})
        notify([appointment.lawyer.user_id] if appointment.lawyer_id else [], 'INTAKE_SUBMITTED',
               'Formulaire reçu', f'Formulaire du rendez-vous #{appointment.pk}')
        return intake


def validate_evidence(upload):
    if upload.size <= 0 or upload.size > settings.INTAKE_MAX_FILE_SIZE:
        raise ValidationError({'file': 'File must contain data and be at most 10 MB.'})
    original = Path(upload.name.replace('\\', '/')).name
    suffix = Path(original).suffix.lower()
    header = upload.read(16)
    upload.seek(0)
    allowed = {'.pdf': ('application/pdf', b'%PDF-'),
               '.png': ('image/png', b'\x89PNG\r\n\x1a\n'),
               '.jpg': ('image/jpeg', b'\xff\xd8\xff'),
               '.jpeg': ('image/jpeg', b'\xff\xd8\xff')}
    if suffix not in allowed or not header.startswith(allowed[suffix][1]):
        raise ValidationError({'file': 'Only PDF, PNG and JPEG files with matching signatures are accepted.'})
    mime = allowed[suffix][0]
    if upload.content_type not in [mime, 'application/octet-stream']:
        raise ValidationError({'file': 'File content type does not match its contents.'})
    return original[:255], mime


def save_evidence(intake, upload, request):
    original, mime = validate_evidence(upload)
    evidence = IntakeEvidence(intake=intake, original_name=original, mime_type=mime, file_size=upload.size)
    try:
        with transaction.atomic():
            evidence.file.save(original, upload, save=False)
            evidence.save()
            record_action(request, 'intake.evidence_uploaded', evidence, {'file_size': upload.size})
    except Exception:
        if evidence.file.name:
            evidence.file.storage.delete(evidence.file.name)
        raise
    return evidence

