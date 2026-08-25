from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'get_full_name', 'email', 'role', 'is_active', 'date_joined']
    list_filter   = ['role', 'is_active', 'gender']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering      = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('Extra Info', {
            'fields': ('role', 'phone', 'address', 'date_of_birth', 'gender', 'profile_image')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Info', {
            'fields': ('role', 'phone', 'first_name', 'last_name', 'email')
        }),
    )