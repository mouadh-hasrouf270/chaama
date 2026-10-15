"""Office-wide fixed consultation slots; independent of case calendar events."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from .models import Appointment


def policy():
    return settings.BOOKING


def office_now():
    return timezone.now().astimezone(ZoneInfo(policy()['TIME_ZONE']))


def scheduled_slots(day):
    config = policy()
    now = office_now()
    if not now.date() <= day <= now.date() + timedelta(days=config['HORIZON_DAYS']):
        return []
    if day.weekday() not in config['WEEKDAYS']:
        return []
    zone = ZoneInfo(config['TIME_ZONE'])
    start = datetime.combine(day, time.fromisoformat(config['OPEN']), zone)
    closing = datetime.combine(day, time.fromisoformat(config['CLOSE']), zone)
    duration = timedelta(minutes=config['DURATION_MINUTES'])
    slots = []
    while start + duration <= closing:
        if start >= now + timedelta(minutes=config['NOTICE_MINUTES']):
            slots.append((start, start + duration))
        start += duration
    return slots


def available_slots(day):
    slots = scheduled_slots(day)
    if not slots:
        return []
    reserved = set(Appointment.objects.exclude(status=Appointment.Status.CANCELLED)
                   .filter(start_at__gte=slots[0][0], start_at__lte=slots[-1][0])
                   .values_list('start_at', flat=True))
    return [{'start_at': start.isoformat(), 'end_at': end.isoformat(),
             'timezone': policy()['TIME_ZONE']}
            for start, end in slots if start not in reserved]
