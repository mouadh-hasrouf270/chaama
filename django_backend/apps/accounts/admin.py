from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Client, LawyerProfile, PracticeArea, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'phone_verified', 'is_staff')
    readonly_fields = ('phone_verified',)
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'phone', 'phone_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile', {'fields': ('role', 'phone', 'first_name', 'last_name')}),
    )


@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bar_number', 'jurisdiction', 'is_verified')
    list_filter = ('is_verified', 'jurisdiction', 'practice_areas')
    search_fields = ('user__username', 'bar_number')
    filter_horizontal = ('practice_areas',)
    readonly_fields = ('user', 'created_at')

    def has_add_permission(self, request):
        return False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'user', 'created_by')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    readonly_fields = ('user', 'created_by', 'created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields + ('phone',) if obj and obj.user_id else fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PracticeArea)
class PracticeAreaAdmin(admin.ModelAdmin):
    search_fields = ('name',)
