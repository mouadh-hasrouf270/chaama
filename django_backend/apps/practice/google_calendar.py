"""Per-user Google Calendar OAuth and explicit push sync for dossier events.
Configure redirect URI to /api/v1/google-calendar/callback/ and encrypt refresh tokens.
"""
import json
import secrets
from datetime import timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core import signing
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import is_admin
from apps.accounts.services import LAWYER_ROLES
from .models import GoogleCalendarConnection, GoogleEventLink, GoogleAppointmentLink, MatterEvent
from .api import EventViewSet


def secure_user(request):
    if not request.user.is_authenticated or not (is_admin(request.user) or request.user.role in LAWYER_ROLES):
        raise PermissionDenied('Staff account required.')


def cipher():
    if not settings.GOOGLE_CALENDAR_ENCRYPTION_KEY:
        raise ValidationError('Google Calendar encryption key is not configured.')
    try:
        return Fernet(settings.GOOGLE_CALENDAR_ENCRYPTION_KEY.encode())
    except ValueError:
        raise ValidationError('Invalid Google Calendar encryption key.')


def configured():
    if not all([settings.GOOGLE_CALENDAR_CLIENT_ID, settings.GOOGLE_CALENDAR_CLIENT_SECRET, settings.GOOGLE_CALENDAR_REDIRECT_URI]):
        raise ValidationError('Google Calendar OAuth credentials are not configured.')


def http_json(url, data=None, token=None, method=None):
    headers = {'Accept':'application/json'}
    if token: headers['Authorization'] = 'Bearer ' + token
    if data is not None:
        if token:
            body=json.dumps(data).encode()
            headers['Content-Type']='application/json'
        else:
            body=urlencode(data).encode()
            headers['Content-Type']='application/x-www-form-urlencoded'
    else: body=None
    try:
        with urlopen(Request(url, data=body, headers=headers, method=method), timeout=15) as response:
            return json.loads(response.read())
    except (HTTPError, URLError, ValueError) as exc:
        raise ValidationError({'google':'Google Calendar request failed; reconnect or retry.'}) from exc


class GoogleCalendarStart(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        secure_user(request); configured(); cipher()
        nonce=secrets.token_urlsafe(32)
        state=signing.dumps({'user_id':request.user.pk,'nonce':nonce},salt='chaama-calendar',compress=True)
        params={'client_id':settings.GOOGLE_CALENDAR_CLIENT_ID,'redirect_uri':settings.GOOGLE_CALENDAR_REDIRECT_URI,'response_type':'code','scope':'https://www.googleapis.com/auth/calendar.events','access_type':'offline','prompt':'consent','state':state}
        return Response({'authorization_url':'https://accounts.google.com/o/oauth2/v2/auth?'+urlencode(params)})


class GoogleCalendarCallback(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        secure_user(request); configured()
        if request.query_params.get('error'):
            raise ValidationError({'google':'Authorization cancelled.'})
        try:
            state=signing.loads(request.query_params.get('state',''),salt='chaama-calendar',max_age=600)
        except signing.BadSignature:
            raise ValidationError({'state':'Invalid or expired OAuth state.'})
        if not state.get('nonce') or state.get('user_id')!=request.user.pk:
            raise ValidationError({'state':'OAuth state/user mismatch.'})
        code=request.query_params.get('code')
        if not code: raise ValidationError({'code':'Missing authorization code.'})
        result=http_json('https://oauth2.googleapis.com/token',{'code':code,'client_id':settings.GOOGLE_CALENDAR_CLIENT_ID,'client_secret':settings.GOOGLE_CALENDAR_CLIENT_SECRET,'redirect_uri':settings.GOOGLE_CALENDAR_REDIRECT_URI,'grant_type':'authorization_code'})
        refresh=result.get('refresh_token')
        if not refresh: raise ValidationError({'google':'No refresh token returned; reconnect with consent.'})
        GoogleCalendarConnection.objects.update_or_create(user=request.user,defaults={'encrypted_refresh_token':cipher().encrypt(refresh.encode()).decode()})
        return Response({'connected':True,'message':'Google Calendar connected. You can now synchronize dossier events.'})


class GoogleCalendarStatus(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        secure_user(request)
        return Response({'connected':GoogleCalendarConnection.objects.filter(user=request.user).exists(),'configured':bool(settings.GOOGLE_CALENDAR_CLIENT_ID)})
    def delete(self,request):
        secure_user(request)
        GoogleCalendarConnection.objects.filter(user=request.user).delete()
        return Response({'connected':False})


class GoogleCalendarSync(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        secure_user(request); configured()
        connection=GoogleCalendarConnection.objects.filter(user=request.user).first()
        if not connection: raise ValidationError('Connect Google Calendar first.')
        try:
            refresh=cipher().decrypt(connection.encrypted_refresh_token.encode()).decode()
        except InvalidToken:
            raise ValidationError('Calendar credentials cannot be decrypted. Reconnect.')
        token=http_json('https://oauth2.googleapis.com/token',{'client_id':settings.GOOGLE_CALENDAR_CLIENT_ID,'client_secret':settings.GOOGLE_CALENDAR_CLIENT_SECRET,'refresh_token':refresh,'grant_type':'refresh_token'}).get('access_token')
        if not token: raise ValidationError('Could not refresh Google access token.')
        from django.db.models import Q
        from .models import Matter
        matters=Matter.objects.all() if is_admin(request.user) else Matter.objects.filter(Q(created_by=request.user)|Q(lead_lawyer__user=request.user)|Q(client__created_by=request.user)).distinct()
        events=MatterEvent.objects.filter(matter__in=matters,start_at__gte=timezone.now()-timedelta(days=30)).select_related('matter')[:500]
        success=0
        errors=[]
        from apps.appointments.models import Appointment
        from urllib.parse import quote
        url='https://www.googleapis.com/calendar/v3/calendars/'+quote(connection.calendar_id,safe='')+'/events'
        for event in events:
            item={'summary':event.title,'description':f'Dossier {event.matter.reference}: {event.matter.title}\n{event.notes}', 'start':{'dateTime':event.start_at.isoformat()},'end':{'dateTime':event.end_at.isoformat()},'location':event.location}
            link=GoogleEventLink.objects.filter(connection=connection,event=event).first()
            try:
                result=http_json(url+'/'+quote(link.google_event_id,safe='') if link else url,item,token,method='PUT' if link else 'POST')
                if not link: GoogleEventLink.objects.create(connection=connection,event=event,google_event_id=result['id'])
                success+=1
            except (ValidationError,KeyError) as exc:
                errors.append({'event':event.pk,'error':'Google rejected event or connection requires attention.'})
        # Client appointments appear in the Chaama agenda but were previously
        # omitted from Google Calendar entirely. Only assigned, non-cancelled
        # appointments are exported; unconfirmed booking requests are not events.
        appointment_query = Appointment.objects.exclude(status=Appointment.Status.CANCELLED).filter(start_at__gte=timezone.now()-timedelta(days=30))
        if not is_admin(request.user):
            appointment_query = appointment_query.filter(lawyer__user=request.user)
        appointments = appointment_query.select_related('client', 'lawyer')[:500]
        for appointment in appointments:
            item = {
                'summary': 'Rendez-vous Chaama',
                # Do not expose client/legal confidential information to calendar
                # attendees or devices unnecessarily.
                'description': f'Rendez-vous Chaama #{appointment.pk}',
                'start': {'dateTime': appointment.start_at.isoformat()},
                'end': {'dateTime': appointment.end_at.isoformat()},
            }
            link = GoogleAppointmentLink.objects.filter(connection=connection, appointment=appointment).first()
            try:
                result = http_json(url+'/'+quote(link.google_event_id, safe='') if link else url,
                                   item, token, method='PUT' if link else 'POST')
                if not link:
                    GoogleAppointmentLink.objects.create(connection=connection, appointment=appointment, google_event_id=result['id'])
                success += 1
            except (ValidationError, KeyError):
                errors.append({'appointment': appointment.pk, 'error': 'Google rejected appointment; verify the connected account.'})
        return Response({'synced':success,'failed':len(errors),'errors':errors,'mode':'manual_one_way_push',
                         'message':'Only assigned appointments and dossier events are synchronized. Unassigned requests must be confirmed first.'})


def sync_new_public_appointment(appointment_id):
    """Best effort Google push after DB commit, never compromise booking on Google outage.

    Only connected administrator calendars are destinations for public bookings.
    Existing manually syncable events remain available if Google was disconnected.
    """
    import logging
    from apps.accounts.models import User
    from apps.appointments.models import Appointment
    from urllib.parse import quote
    logger = logging.getLogger(__name__)
    appointment = Appointment.objects.filter(pk=appointment_id).first()
    if appointment is None:
        return
    connections = GoogleCalendarConnection.objects.filter(user__is_staff=True)
    for connection in connections:
        try:
            configured()
            refresh = cipher().decrypt(connection.encrypted_refresh_token.encode()).decode()
            token = http_json('https://oauth2.googleapis.com/token', {
                'client_id': settings.GOOGLE_CALENDAR_CLIENT_ID,
                'client_secret': settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                'refresh_token': refresh, 'grant_type': 'refresh_token'
            }).get('access_token')
            if not token:
                continue
            url = 'https://www.googleapis.com/calendar/v3/calendars/' + quote(connection.calendar_id, safe='') + '/events'
            item = {'summary': 'Rendez-vous Chaama' + (' — à attribuer' if not appointment.lawyer_id else ''),
                    'description': f'Chaama RDV #{appointment.pk} (sans détails confidentiels)',
                    'start': {'dateTime': appointment.start_at.isoformat()},
                    'end': {'dateTime': appointment.end_at.isoformat()}}
            link = GoogleAppointmentLink.objects.filter(connection=connection, appointment=appointment).first()
            result = http_json(url + '/' + quote(link.google_event_id, safe='') if link else url,
                               item, token, method='PUT' if link else 'POST')
            if not link:
                GoogleAppointmentLink.objects.get_or_create(
                    connection=connection, appointment=appointment,
                    defaults={'google_event_id': result['id']})
        except Exception:
            logger.exception('Google Calendar push failed for appointment %s', appointment_id)


def queue_public_appointment_sync(appointment_id):
    """Non-blocking best effort, never delay/roll back customer success response.

    Durable retry is available through the administrative Synchroniser button.
    Production deployments should replace this daemon thread with a worker/outbox.
    """
    from threading import Thread
    from django.db import close_old_connections
    def worker():
        close_old_connections()
        try:
            sync_new_public_appointment(appointment_id)
        finally:
            close_old_connections()
    Thread(target=worker, daemon=True, name=f'chaama-calendar-{appointment_id}').start()
