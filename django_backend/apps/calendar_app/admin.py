from django.contrib import admin
from .models import CalendarEvent
from .models import PracticeArea, Appointment


@admin.register(PracticeArea)
class PracticeAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'full_name', 'start_at', 'consultation_type', 'status')
    list_filter = ('status', 'consultation_type', 'practice_area')
    search_fields = ('full_name', 'email', 'phone')
    readonly_fields = [field.name for field in Appointment._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('matter', 'event_type', 'event_date', 'is_completed')
    list_filter = ('event_type', 'is_completed')
    search_fields = ('title', 'matter__reference')
