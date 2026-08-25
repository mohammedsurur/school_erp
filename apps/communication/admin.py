# apps/communication/admin.py

from django.contrib    import admin
from django.utils.html import format_html
from django.utils      import timezone
from .models           import (
    Announcement, AnnouncementAttachment,
    MessageThread, Message, Notification, Event
)


# ─────────────────────────────────────────────
#  Announcement Admin
# ─────────────────────────────────────────────

class AnnouncementAttachmentInline(admin.TabularInline):
    model  = AnnouncementAttachment
    extra  = 0
    fields = ['file', 'filename', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display   = [
        'title', 'audience', 'priority_display',
        'status_display', 'target_grade',
        'created_by', 'created_at'
    ]
    list_filter    = ['audience', 'priority', 'is_published']
    search_fields  = ['title', 'body']
    readonly_fields= ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines        = [AnnouncementAttachmentInline]
    actions        = ['publish', 'unpublish']

    def priority_display(self, obj):
        colours = {
            'normal':   '#6b7280',
            'urgent':   '#f59e0b',
            'critical': '#ef4444',
        }
        colour = colours.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="color:{};font-weight:700">{}</span>',
            colour,
            obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'

    def status_display(self, obj):
        labels = {
            'active':    ('<span style="color:green">● Active</span>',),
            'draft':     ('<span style="color:gray">○ Draft</span>',),
            'scheduled': ('<span style="color:#f59e0b">◷ Scheduled</span>',),
            'expired':   ('<span style="color:red">✕ Expired</span>',),
        }
        html = labels.get(obj.status_label, ('—',))[0]
        return format_html(html)
    status_display.short_description = 'Status'

    def publish(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, f'{queryset.count()} announcement(s) published.')
    publish.short_description = 'Publish selected'

    def unpublish(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, f'{queryset.count()} announcement(s) unpublished.')
    unpublish.short_description = 'Unpublish selected'


# ─────────────────────────────────────────────
#  Message Thread Admin
# ─────────────────────────────────────────────

class MessageInline(admin.TabularInline):
    model          = Message
    extra          = 0
    fields         = ['sender', 'body', 'sent_at']
    readonly_fields= ['sent_at']
    show_change_link = True


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display  = ['subject', 'participant_count', 'message_count', 'updated_at']
    search_fields = ['subject', 'participants__first_name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['participants']
    inlines       = [MessageInline]

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ['sender', 'thread', 'body_preview', 'sent_at']
    list_filter   = ['sent_at']
    search_fields = ['sender__first_name', 'body', 'thread__subject']
    readonly_fields = ['sent_at']

    def body_preview(self, obj):
        return obj.body[:60] + ('…' if len(obj.body) > 60 else '')
    body_preview.short_description = 'Message'


# ─────────────────────────────────────────────
#  Notification Admin
# ─────────────────────────────────────────────

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = [
        'recipient', 'notif_type', 'title',
        'is_read', 'created_at'
    ]
    list_filter   = ['notif_type', 'is_read']
    search_fields = ['recipient__first_name', 'title', 'body']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    actions        = ['mark_read', 'mark_unread']

    def mark_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} notification(s) marked read.')
    mark_read.short_description = 'Mark selected as read'

    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'{queryset.count()} notification(s) marked unread.')
    mark_unread.short_description = 'Mark selected as unread'


# ─────────────────────────────────────────────
#  Event Admin
# ─────────────────────────────────────────────

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = [
        'title', 'category', 'start_date', 'end_date',
        'audience', 'is_published', 'state_display', 'created_by'
    ]
    list_filter   = ['category', 'audience', 'is_published']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at']
    date_hierarchy  = 'start_date'
    actions         = ['publish', 'unpublish']

    def state_display(self, obj):
        if obj.is_upcoming:
            return format_html('<span style="color:#f59e0b">Upcoming</span>')
        if obj.is_ongoing:
            return format_html('<span style="color:green">Ongoing</span>')
        return format_html('<span style="color:gray">Past</span>')
    state_display.short_description = 'State'

    def publish(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, f'{queryset.count()} event(s) published.')
    publish.short_description = 'Publish selected'

    def unpublish(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, f'{queryset.count()} event(s) unpublished.')
    unpublish.short_description = 'Unpublish selected'