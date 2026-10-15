from django.contrib import admin
from .models import Matter, MatterAssignment


@admin.register(Matter)
class MatterAdmin(admin.ModelAdmin):
    list_display = ('reference', 'title', 'client', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('reference', 'title')


@admin.register(MatterAssignment)
class MatterAssignmentAdmin(admin.ModelAdmin):
    list_display = ('matter', 'associate', 'assigned_by', 'assigned_at')