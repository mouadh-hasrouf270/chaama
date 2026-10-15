from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.conf import settings
from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import LawyerProfile
from apps.appointments.services import create_appointment, calculate_available_slots
from apps.intakes.models import Intake
from .models import BookingRequest, Appointment

@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'requested_date', 'preferred_time', 'practice_area', 'status', 'appointment_id', 'created_at')
    list_filter = ('status', 'practice_area', 'requested_date')
    search_fields = ('full_name', 'phone', 'email', 'legal_topic')
    readonly_fields = ('appointment', 'client', 'practice_area', 'full_name', 'email', 'phone', 'legal_topic', 'description', 'opposing_party', 'requested_date', 'preferred_time', 'consultation_type', 'created_at', 'updated_at')
    actions = ['confirm_selected_requests']

    @admin.action(description='Créer un vrai rendez-vous si un avocat est disponible à l’heure demandée')
    def confirm_selected_requests(self, request, queryset):
        success = 0
        for item in queryset.select_related('practice_area', 'client'):
            if item.status == BookingRequest.Status.CONVERTED or item.appointment_id:
                self.message_user(request, f'Demande #{item.pk} déjà convertie.', level=messages.WARNING)
                continue
            lawyers = LawyerProfile.objects.filter(is_verified=True, user__is_active=True, availability_status='AVAILABLE', practice_areas=item.practice_area).select_related('user').distinct()
            chosen = None
            for lawyer in lawyers:
                for slot in calculate_available_slots(lawyer, item.requested_date):
                    if slot['start_at'].astimezone(ZoneInfo(settings.BOOKING_TIME_ZONE)).time().replace(tzinfo=None) == item.preferred_time:
                        chosen = (lawyer, slot)
                        break
                if chosen:
                    break
            if not chosen:
                self.message_user(request, f'Demande #{item.pk}: aucun avocat disponible le {item.requested_date} à {item.preferred_time}. Configurez les horaires, puis réessayez.', level=messages.WARNING)
                continue
            lawyer, slot = chosen
            try:
                with transaction.atomic():
                    locked = BookingRequest.objects.select_for_update().get(pk=item.pk)
                    if locked.appointment_id or locked.status == BookingRequest.Status.CONVERTED:
                        continue
                    appt = create_appointment({'lawyer': lawyer, 'start_at': slot['start_at'], 'end_at': slot['end_at'], 'consultation_type': locked.consultation_type, 'client': locked.client}, request)
                    Intake.objects.create(appointment=appt, full_name=locked.full_name, email=locked.email, phone=locked.phone, legal_topic=locked.legal_topic, description=locked.description, opposing_party=locked.opposing_party)
                    locked.appointment = appt
                    locked.status = BookingRequest.Status.CONVERTED
                    locked.save(update_fields=['appointment', 'status', 'updated_at'])
                    success += 1
            except Exception as exc:
                self.message_user(request, f'Demande #{item.pk}: conversion impossible ({exc}).', level=messages.ERROR)
        if success:
            self.message_user(request, f'{success} rendez-vous créés dans le calendrier.', level=messages.SUCCESS)

    def has_delete_permission(self, request, obj=None):
        return False
