from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.conf import settings
from django.db import transaction, OperationalError
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError, PermissionDenied
from apps.accounts.models import Client, LawyerProfile, User
from apps.accounts.permissions import is_admin
from apps.activity.services import notify, record_action
from .models import Appointment, CalendarBlock, LawyerAvailability


class BookingConflict(APIException):
    status_code = 409
    default_detail = 'This slot is no longer available. Refresh availability and retry.'


def visible_appointments(user):
    qs = Appointment.objects.select_related('lawyer__user', 'client')
    if not user.is_authenticated:
        return qs.none()
    if is_admin(user):
        return qs
    return qs.filter(Q(lawyer__user=user) | Q(client__user=user) | Q(created_by=user)).distinct()


def visible_clients(user):
    qs = Client.objects.all()
    return qs if is_admin(user) else qs.filter(created_by=user)


def lock_calendar(lawyer_id):
    # FIRST statement in the transaction is a write. This acquires SQLite's writer
    # lock before reading availability; on PostgreSQL it locks the lawyer row.
    # Every calendar mutation goes through this service and the same lock.
    try:
        if not LawyerProfile.objects.filter(pk=lawyer_id).update(updated_at=F('updated_at')):
            raise ValidationError({'lawyer': 'Unknown lawyer.'})
    except OperationalError as exc:
        if 'locked' in str(exc).lower():
            raise BookingConflict() from exc
        raise
    return LawyerProfile.objects.select_for_update().select_related('user').get(pk=lawyer_id)


def validate_interval(start_at, end_at):
    if end_at <= start_at:
        raise ValidationError({'end_at': 'Must be after start_at.'})
    if start_at <= timezone.now():
        raise ValidationError({'start_at': 'Must be in the future.'})


def check_calendar_conflict(lawyer_id, start_at, end_at, exclude_appointment=None, exclude_block=None):
    bookings = Appointment.objects.filter(lawyer_id=lawyer_id, start_at__lt=end_at, end_at__gt=start_at).exclude(status=Appointment.Status.CANCELLED)
    blocks = CalendarBlock.objects.filter(lawyer_id=lawyer_id, start_at__lt=end_at, end_at__gt=start_at)
    if exclude_appointment:
        bookings = bookings.exclude(pk=exclude_appointment)
    if exclude_block:
        blocks = blocks.exclude(pk=exclude_block)
    return bookings.exists() or blocks.exists()


def within_working_hours(lawyer_id, start_at, end_at):
    zone = ZoneInfo(settings.BOOKING_TIME_ZONE)
    start, end = start_at.astimezone(zone), end_at.astimezone(zone)
    if start.date() != end.date():
        return False
    return LawyerAvailability.objects.filter(
        lawyer_id=lawyer_id, weekday=start.weekday(),
        start_time__lte=start.time().replace(tzinfo=None),
        end_time__gte=end.time().replace(tzinfo=None),
    ).exists()


def validate_booking(lawyer, start_at, end_at, exclude=None):
    validate_interval(start_at, end_at)
    if not lawyer.user.is_active or not lawyer.is_verified or lawyer.availability_status != 'AVAILABLE':
        raise ValidationError({'lawyer': 'Lawyer is not available for booking.'})
    if end_at - start_at > timedelta(hours=4):
        raise ValidationError({'end_at': 'A consultation may not exceed four hours.'})
    if not within_working_hours(lawyer.pk, start_at, end_at):
        raise ValidationError({'start_at': 'Outside configured working hours.'})
    if check_calendar_conflict(lawyer.pk, start_at, end_at, exclude_appointment=exclude):
        raise BookingConflict()


def appointment_recipients(appointment):
    return [appointment.lawyer.user_id if appointment.lawyer_id else None,
            appointment.client.user_id if appointment.client else None,
            appointment.created_by_id]


def create_appointment(data, request):
    try:
        with transaction.atomic():
            lawyer = lock_calendar(data['lawyer'].pk)
            validate_booking(lawyer, data['start_at'], data['end_at'])
            appointment = Appointment.objects.create(
                **data, created_by=request.user if request.user.is_authenticated else None)
            record_action(request, 'appointment.created', appointment)
            notify(appointment_recipients(appointment), 'APPOINTMENT_CREATED',
                   'Nouveau rendez-vous', f'Rendez-vous #{appointment.pk}')
            return appointment
    except OperationalError as exc:
        if 'locked' in str(exc).lower():
            raise BookingConflict() from exc
        raise


def update_appointment(instance, data, request, cancel=False):
    try:
        with transaction.atomic():
            lawyer = lock_calendar(instance.lawyer_id) if instance.lawyer_id else None
            current = Appointment.objects.select_for_update().get(pk=instance.pk)
            if current.status in [Appointment.Status.CANCELLED, Appointment.Status.COMPLETED]:
                if cancel and current.status == Appointment.Status.CANCELLED:
                    return current
                raise ValidationError('A closed appointment cannot be modified.')
            if cancel:
                data = {'status': Appointment.Status.CANCELLED}
            else:
                status = data.get('status', current.status)
                if status == Appointment.Status.CANCELLED:
                    raise ValidationError({'status': 'Use the cancel action.'})
                staff = is_admin(request.user) or (current.lawyer_id and current.lawyer.user_id == request.user.pk)
                if not staff and any(k in data for k in ['meeting_url', 'status']):
                    raise PermissionDenied('Only the assigned lawyer or admin can update status or meeting URL.')
                if status == Appointment.Status.COMPLETED:
                    if current.end_at > timezone.now():
                        raise ValidationError('A future appointment cannot be completed.')
                elif any(k in data for k in ['start_at', 'end_at']) and lawyer is not None:
                    validate_booking(lawyer, data.get('start_at', current.start_at),
                                     data.get('end_at', current.end_at), exclude=current.pk)
            for field, value in data.items():
                setattr(current, field, value)
            current.save()
            record_action(request, 'appointment.cancelled' if cancel else 'appointment.updated', current,
                          {'fields': list(data)})
            if cancel:
                notify(appointment_recipients(current), 'APPOINTMENT_CANCELLED',
                       'Rendez-vous annulé', f'Rendez-vous #{current.pk}')
            return current
    except OperationalError as exc:
        if 'locked' in str(exc).lower():
            raise BookingConflict() from exc
        raise


def calculate_available_slots(lawyer, day):
    if not lawyer.user.is_active or not lawyer.is_verified or lawyer.availability_status != 'AVAILABLE':
        return []
    zone = ZoneInfo(settings.BOOKING_TIME_ZONE)
    duration = timedelta(minutes=settings.BOOKING_SLOT_MINUTES)
    now = timezone.now()
    slots = []
    seen = set()
    bookings = list(Appointment.objects.filter(lawyer=lawyer).exclude(status='CANCELLED').filter(
        start_at__lt=datetime.combine(day + timedelta(days=1), datetime.min.time(), zone),
        end_at__gt=datetime.combine(day, datetime.min.time(), zone)).values_list('start_at', 'end_at'))
    blocks = list(CalendarBlock.objects.filter(lawyer=lawyer).filter(
        start_at__lt=datetime.combine(day + timedelta(days=1), datetime.min.time(), zone),
        end_at__gt=datetime.combine(day, datetime.min.time(), zone)).values_list('start_at', 'end_at'))
    for working in lawyer.working_hours.filter(weekday=day.weekday()):
        cursor = datetime.combine(day, working.start_time, zone)
        finish = datetime.combine(day, working.end_time, zone)
        while cursor + duration <= finish:
            end = cursor + duration
            if cursor > now and cursor not in seen and not any(a < end and b > cursor for a, b in bookings + blocks):
                slots.append({'lawyer': lawyer.pk, 'start_at': cursor, 'end_at': end})
                seen.add(cursor)
            cursor = end
    return slots


def save_calendar_block(data, request, instance=None):
    with transaction.atomic():
        lawyer_id = instance.lawyer_id if instance else data['lawyer'].pk
        lock_calendar(lawyer_id)
        if instance:
            instance.refresh_from_db()
        start = data.get('start_at', instance.start_at if instance else None)
        end = data.get('end_at', instance.end_at if instance else None)
        validate_interval(start, end)
        if check_calendar_conflict(lawyer_id, start, end, exclude_block=instance.pk if instance else None):
            raise BookingConflict()
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
            instance.save()
        else:
            instance = CalendarBlock.objects.create(**data)
        record_action(request, 'calendar.block_saved', instance)
        return instance


def save_working_hours(data, request, instance=None):
    with transaction.atomic():
        lawyer_id = instance.lawyer_id if instance else data['lawyer'].pk
        lock_calendar(lawyer_id)
        if instance:
            instance.refresh_from_db()
            for key, value in data.items():
                setattr(instance, key, value)
            instance.save()
        else:
            instance = LawyerAvailability.objects.create(**data)
        record_action(request, 'calendar.working_hours_saved', instance)
        return instance
