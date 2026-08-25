# apps/communication/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # ── Dashboard ─────────────────────────────
    path(
        '',
        views.comm_dashboard,
        name='comm_dashboard'
    ),

    # ── Announcements ─────────────────────────
    path(
        'announcements/',
        views.announcement_list,
        name='announcement_list'
    ),
    path(
        'announcements/create/',
        views.announcement_create,
        name='announcement_create'
    ),
    path(
        'announcements/<int:pk>/',
        views.announcement_detail,
        name='announcement_detail'
    ),
    path(
        'announcements/<int:pk>/edit/',
        views.announcement_edit,
        name='announcement_edit'
    ),
    path(
        'announcements/<int:pk>/delete/',
        views.announcement_delete,
        name='announcement_delete'
    ),
    path(
        'announcements/<int:pk>/toggle/',
        views.announcement_publish_toggle,
        name='announcement_publish_toggle'
    ),

    # ── Messages / Inbox ──────────────────────
    path(
        'messages/',
        views.inbox,
        name='inbox'
    ),
    path(
        'messages/new/',
        views.new_thread,
        name='new_thread'
    ),
    path(
        'messages/<int:pk>/',
        views.thread_detail,
        name='thread_detail'
    ),
    path(
        'messages/<int:pk>/delete/',
        views.thread_delete,
        name='thread_delete'
    ),

    # ── Notifications ─────────────────────────
    path(
        'notifications/',
        views.notification_list,
        name='notification_list'
    ),
    path(
        'notifications/<int:pk>/read/',
        views.notification_mark_read,
        name='notification_mark_read'
    ),
    path(
        'notifications/mark-all-read/',
        views.notification_mark_all_read,
        name='notification_mark_all_read'
    ),
    path(
        'notifications/json/',
        views.notifications_json,
        name='notifications_json'
    ),

    # ── Events ────────────────────────────────
    path(
        'events/',
        views.event_list,
        name='event_list'
    ),
    path(
        'events/create/',
        views.event_create,
        name='event_create'
    ),
    path(
        'events/<int:pk>/',
        views.event_detail,
        name='event_detail'
    ),
    path(
        'events/<int:pk>/edit/',
        views.event_edit,
        name='event_edit'
    ),
    path(
        'events/<int:pk>/delete/',
        views.event_delete,
        name='event_delete'
    ),
]