from django.contrib import admin
from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = [
        'staff_id', 'get_full_name', 'staff_type',
        'department', 'qualification', 'join_date',
        'salary', 'is_active'
    ]
    list_filter   = ['staff_type', 'qualification', 'is_active', 'department']
    search_fields = [
        'staff_id',
        'user__first_name',
        'user__last_name',
        'user__email',
        'department',
    ]
    ordering      = ['-join_date']
    readonly_fields = ['staff_id']

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'staff_id', 'staff_type', 'department', 'photo')
        }),
        ('Qualification', {
            'fields': ('qualification', 'specialization', 'experience_years')
        }),
        ('Employment', {
            'fields': ('join_date', 'salary', 'is_active')
        }),
        ('Banking', {
            'fields': ('bank_name', 'bank_account'),
            'classes': ('collapse',)
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'user__first_name'