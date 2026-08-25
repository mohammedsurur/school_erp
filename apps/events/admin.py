
from django.contrib import admin
from .models import Event, EventCategory


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'icon']
    search_fields = ['name']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'event_type',
        'start_date', 'end_date',
        'is_published', 'created_by'
    ]
    list_filter   = ['category', 'event_type', 'is_published', 'start_date']
    search_fields = ['title', 'description', 'location']
    ordering      = ['-start_date']
    date_hierarchy = 'start_date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'description', 'category', 'event_type')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time', 'location')
        }),
        ('Audience', {
            'fields': ('audience', 'is_published', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )