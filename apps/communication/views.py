# apps/communication/views.py

from django.shortcuts        import render, redirect, get_object_or_404
from django.contrib          import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator   import Paginator
from django.db.models        import Q, Count, Max
from django.utils            import timezone
from django.http             import JsonResponse
from django.contrib.auth     import get_user_model

from apps.core.decorators    import admin_required, principal_or_above
from .models                 import (
    Announcement, AnnouncementAttachment,
    MessageThread, Message, Notification, Event
)
from .forms                  import (
    AnnouncementForm, AnnouncementAttachmentForm,
    NewThreadForm, ReplyForm, EventForm,
    AnnouncementFilterForm, EventFilterForm
)

User = get_user_model()


# ══════════════════════════════════════════════
#  ANNOUNCEMENTS
# ══════════════════════════════════════════════

@login_required
def announcement_list(request):
    form          = AnnouncementFilterForm(request.GET or None)
    now           = timezone.now()
    user          = request.user
    is_staff_role = user.role in (
        'super_admin', 'principal', 'admin_staff',
        'teacher', 'accountant', 'librarian'
    )

    if is_staff_role:
        # Staff see all announcements
        announcements = Announcement.objects.select_related(
            'created_by', 'target_grade', 'target_section'
        ).order_by('-created_at')
    else:
        # Students/parents see published, non-expired, matching audience
        role_map = {'student': 'students', 'parent': 'parents'}
        user_audience = role_map.get(user.role, 'all')
        announcements = Announcement.objects.filter(
            is_published=True,
        ).filter(
            Q(publish_date__isnull=True) | Q(publish_date__lte=now)
        ).filter(
            Q(expiry_date__isnull=True)  | Q(expiry_date__gte=now)
        ).filter(
            Q(audience='all') | Q(audience=user_audience)
        ).select_related(
            'created_by', 'target_grade', 'target_section'
        ).order_by('-created_at')

    # Apply filters (staff only)
    if is_staff_role and form.is_valid():
        q = form.cleaned_data.get('q', '').strip()
        if q:
            announcements = announcements.filter(
                Q(title__icontains=q) | Q(body__icontains=q)
            )
        if form.cleaned_data.get('audience'):
            announcements = announcements.filter(
                audience=form.cleaned_data['audience']
            )
        if form.cleaned_data.get('priority'):
            announcements = announcements.filter(
                priority=form.cleaned_data['priority']
            )
        status = form.cleaned_data.get('status')
        if status == 'draft':
            announcements = announcements.filter(is_published=False)
        elif status == 'active':
            announcements = announcements.filter(
                is_published=True,
            ).filter(
                Q(publish_date__isnull=True) | Q(publish_date__lte=now)
            ).filter(
                Q(expiry_date__isnull=True)  | Q(expiry_date__gte=now)
            )
        elif status == 'scheduled':
            announcements = announcements.filter(
                is_published=True, publish_date__gt=now
            )
        elif status == 'expired':
            announcements = announcements.filter(
                is_published=True, expiry_date__lt=now
            )

    paginator     = Paginator(announcements, 15)
    page          = request.GET.get('page', 1)
    announcements = paginator.get_page(page)

    return render(request, 'communication/announcement_list.html', {
        'announcements': announcements,
        'form':          form,
        'is_staff_role': is_staff_role,
        'page_title':    'Announcements',
    })


@login_required
def announcement_detail(request, pk):
    now          = timezone.now()
    announcement = get_object_or_404(
        Announcement.objects.select_related(
            'created_by', 'target_grade', 'target_section'
        ).prefetch_related('attachments'),
        pk=pk
    )
    # Non-staff can only view published, non-expired
    is_staff_role = request.user.role in (
        'super_admin', 'principal', 'admin_staff',
        'teacher', 'accountant', 'librarian'
    )
    if not is_staff_role and not announcement.is_active:
        messages.error(request, 'This announcement is not available.')
        return redirect('announcement_list')

    return render(request, 'communication/announcement_detail.html', {
        'announcement': announcement,
        'is_staff_role': is_staff_role,
        'page_title':   announcement.title,
    })


@admin_required
def announcement_create(request):
    form     = AnnouncementForm(request.POST or None)
    att_form = AnnouncementAttachmentForm(
        request.POST or None, request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        ann            = form.save(commit=False)
        ann.created_by = request.user
        ann.save()

        # Handle multiple file uploads
        for f in request.FILES.getlist('file'):
            AnnouncementAttachment.objects.create(
                announcement=ann, file=f
            )

        # Send notifications to audience
        _notify_announcement(ann)

        messages.success(
            request,
            f'Announcement "{ann.title}" '
            f'{"published" if ann.is_published else "saved as draft"}.'
        )
        return redirect('announcement_detail', pk=ann.pk)

    return render(request, 'communication/announcement_form.html', {
        'form':       form,
        'att_form':   att_form,
        'title':      'Create Announcement',
        'page_title': 'Create Announcement',
    })


@admin_required
def announcement_edit(request, pk):
    ann      = get_object_or_404(Announcement, pk=pk)
    form     = AnnouncementForm(request.POST or None, instance=ann)
    att_form = AnnouncementAttachmentForm(
        request.POST or None, request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        for f in request.FILES.getlist('file'):
            AnnouncementAttachment.objects.create(
                announcement=ann, file=f
            )
        messages.success(request, f'"{ann.title}" updated.')
        return redirect('announcement_detail', pk=ann.pk)

    return render(request, 'communication/announcement_form.html', {
        'form':         form,
        'att_form':     att_form,
        'announcement': ann,
        'title':        f'Edit — {ann.title}',
        'page_title':   'Edit Announcement',
    })


@admin_required
def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
        return redirect('announcement_list')
    return render(request, 'communication/confirm_delete.html', {
        'object':   ann,
        'title':    f'Delete — {ann.title}',
        'back_url': f'/communication/announcements/{pk}/',
    })


@admin_required
def announcement_publish_toggle(request, pk):
    ann             = get_object_or_404(Announcement, pk=pk)
    ann.is_published = not ann.is_published
    ann.save(update_fields=['is_published'])
    state = 'published' if ann.is_published else 'unpublished'
    messages.success(request, f'"{ann.title}" {state}.')
    return redirect('announcement_detail', pk=pk)


def _notify_announcement(announcement):
    """Send system notification to target audience"""
    audience = announcement.audience
    qs = User.objects.filter(is_active=True)
    if audience == 'students':
        qs = qs.filter(role='student')
    elif audience == 'parents':
        qs = qs.filter(role='parent')
    elif audience == 'teachers':
        qs = qs.filter(role='teacher')
    elif audience == 'staff':
        qs = qs.exclude(role__in=['student', 'parent'])
    elif audience == 'admin':
        qs = qs.filter(role__in=['super_admin', 'principal', 'admin_staff'])

    if announcement.is_published:
        Notification.broadcast(
            recipients=qs,
            title=announcement.title,
            body=announcement.body[:120],
            notif_type='announcement',
            link=f'/communication/announcements/{announcement.pk}/',
        )


# ══════════════════════════════════════════════
#  MESSAGES / THREADS
# ══════════════════════════════════════════════

@login_required
def inbox(request):
    user    = request.user
    threads = MessageThread.objects.filter(
        participants=user
    ).annotate(
        last_msg=Max('messages__sent_at'),
        msg_count=Count('messages'),
    ).order_by('-last_msg')

    # Unread counts per thread
    thread_data = []
    for t in threads:
        unread = t.unread_count(user)
        thread_data.append({'thread': t, 'unread': unread})

    total_unread = sum(d['unread'] for d in thread_data)

    return render(request, 'communication/inbox.html', {
        'thread_data':   thread_data,
        'total_unread':  total_unread,
        'page_title':    'Inbox',
    })


@login_required
def thread_detail(request, pk):
    user   = request.user
    thread = get_object_or_404(
        MessageThread.objects.prefetch_related(
            'participants', 'messages__sender', 'messages__read_by'
        ),
        pk=pk,
        participants=user
    )

    # Mark all unread messages as read
    for msg in thread.messages.all():
        if not msg.is_read_by(user):
            msg.mark_read(user)

    form = ReplyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        msg = Message.objects.create(
            thread=thread,
            sender=user,
            body=form.cleaned_data['body'],
        )
        msg.read_by.add(user)
        thread.save()  # bump updated_at

        # Notify other participants
        others = thread.participants.exclude(pk=user.pk)
        Notification.broadcast(
            recipients=others,
            title=f'New message from {user.get_full_name()}',
            body=msg.body[:100],
            notif_type='message',
            link=f'/communication/messages/{thread.pk}/',
        )
        messages.success(request, 'Reply sent.')
        return redirect('thread_detail', pk=thread.pk)

    return render(request, 'communication/thread_detail.html', {
        'thread':     thread,
        'form':       form,
        'user':       user,
        'page_title': thread.subject or f'Message Thread',
    })


@login_required
def new_thread(request):
    form = NewThreadForm(
        request.POST or None,
        current_user=request.user
    )
    if request.method == 'POST' and form.is_valid():
        recipients = form.cleaned_data['recipients']
        subject    = form.cleaned_data.get('subject', '')
        body       = form.cleaned_data['body']

        # Check if thread already exists between same participants
        thread = MessageThread.objects.create(subject=subject)
        thread.participants.add(request.user, *recipients)

        msg = Message.objects.create(
            thread=thread,
            sender=request.user,
            body=body,
        )
        msg.read_by.add(request.user)

        # Notify recipients
        Notification.broadcast(
            recipients=recipients,
            title=f'New message from {request.user.get_full_name()}',
            body=body[:100],
            notif_type='message',
            link=f'/communication/messages/{thread.pk}/',
        )
        messages.success(request, 'Message sent.')
        return redirect('thread_detail', pk=thread.pk)

    return render(request, 'communication/new_thread.html', {
        'form':       form,
        'page_title': 'New Message',
    })


@login_required
def thread_delete(request, pk):
    thread = get_object_or_404(
        MessageThread, pk=pk, participants=request.user
    )
    if request.method == 'POST':
        thread.participants.remove(request.user)
        # Delete thread if no participants left
        if not thread.participants.exists():
            thread.delete()
        messages.success(request, 'Conversation removed from your inbox.')
        return redirect('inbox')
    return render(request, 'communication/confirm_delete.html', {
        'object':    thread,
        'title':     'Remove Conversation',
        'back_url':  '/communication/messages/',
        'btn_label': 'Remove',
        'btn_class': 'btn-warning',
    })


# ══════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════

@login_required
def notification_list(request):
    notifs = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    unread_count = notifs.filter(is_read=False).count()

    paginator = Paginator(notifs, 20)
    page      = request.GET.get('page', 1)
    notifs    = paginator.get_page(page)

    return render(request, 'communication/notification_list.html', {
        'notifications': notifs,
        'unread_count':  unread_count,
        'page_title':    'Notifications',
    })


@login_required
def notification_mark_read(request, pk):
    notif = get_object_or_404(
        Notification, pk=pk, recipient=request.user
    )
    notif.mark_read()
    if notif.link:
        return redirect(notif.link)
    return redirect('notification_list')


@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(
        recipient=request.user, is_read=False
    ).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


@login_required
def notifications_json(request):
    """AJAX endpoint for notification bell in navbar"""
    notifs = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')[:10]

    data = {
        'count': notifs.count(),
        'items': [
            {
                'id':         n.pk,
                'title':      n.title,
                'body':       n.body[:80],
                'type':       n.notif_type,
                'link':       n.link,
                'created_at': n.created_at.strftime('%b %d, %H:%M'),
            }
            for n in notifs
        ]
    }
    return JsonResponse(data)


# ══════════════════════════════════════════════
#  EVENTS / CALENDAR
# ══════════════════════════════════════════════

@login_required
def event_list(request):
    form   = EventFilterForm(request.GET or None)
    now    = timezone.now()
    events = Event.objects.filter(is_published=True).order_by('start_date')

    # Non-admin: filter by audience
    is_staff_role = request.user.role in (
        'super_admin', 'principal', 'admin_staff', 'teacher'
    )
    if not is_staff_role:
        role_map = {'student': 'students', 'parent': 'parents'}
        user_audience = role_map.get(request.user.role, 'all')
        events = events.filter(
            Q(audience='all') | Q(audience=user_audience)
        )

    if form.is_valid():
        q = form.cleaned_data.get('q', '').strip()
        if q:
            events = events.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )
        if form.cleaned_data.get('category'):
            events = events.filter(category=form.cleaned_data['category'])
        period = form.cleaned_data.get('period')
        if period == 'upcoming':
            events = events.filter(start_date__gt=now)
        elif period == 'ongoing':
            events = events.filter(start_date__lte=now, end_date__gte=now)
        elif period == 'past':
            events = events.filter(end_date__lt=now)
        elif period == 'this_month':
            events = events.filter(
                start_date__year=now.year,
                start_date__month=now.month
            )

    # Upcoming events for sidebar widget
    upcoming = Event.objects.filter(
        is_published=True,
        start_date__gte=now
    ).order_by('start_date')[:5]

    paginator = Paginator(events, 12)
    page      = request.GET.get('page', 1)
    events    = paginator.get_page(page)

    return render(request, 'communication/event_list.html', {
        'events':         events,
        'form':           form,
        'upcoming':       upcoming,
        'is_staff_role':  is_staff_role,
        'page_title':     'Events & Calendar',
    })


@login_required
def event_detail(request, pk):
    event = get_object_or_404(
        Event.objects.select_related('created_by'), pk=pk
    )
    return render(request, 'communication/event_detail.html', {
        'event':      event,
        'page_title': event.title,
    })


@admin_required
def event_create(request):
    form = EventForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        event            = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, f'Event "{event.title}" created.')
        return redirect('event_detail', pk=event.pk)
    return render(request, 'communication/event_form.html', {
        'form':       form,
        'title':      'Create Event',
        'page_title': 'Create Event',
    })


@admin_required
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form  = EventForm(request.POST or None, instance=event)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{event.title}" updated.')
        return redirect('event_detail', pk=event.pk)
    return render(request, 'communication/event_form.html', {
        'form':       form,
        'event':      event,
        'title':      f'Edit — {event.title}',
        'page_title': 'Edit Event',
    })


@admin_required
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted.')
        return redirect('event_list')
    return render(request, 'communication/confirm_delete.html', {
        'object':   event,
        'title':    f'Delete — {event.title}',
        'back_url': f'/communication/events/{pk}/',
    })


# ══════════════════════════════════════════════
#  COMMUNICATION DASHBOARD
# ══════════════════════════════════════════════

@login_required
def comm_dashboard(request):
    user = request.user
    now  = timezone.now()

    # Announcements
    active_announcements = Announcement.objects.filter(
        is_published=True,
    ).filter(
        Q(publish_date__isnull=True) | Q(publish_date__lte=now)
    ).filter(
        Q(expiry_date__isnull=True)  | Q(expiry_date__gte=now)
    ).order_by('-created_at')[:5]

    # Unread notifications
    unread_notifs = Notification.objects.filter(
        recipient=user, is_read=False
    ).count()

    # Unread messages
    threads = MessageThread.objects.filter(participants=user)
    unread_messages = sum(t.unread_count(user) for t in threads)

    # Upcoming events
    upcoming_events = Event.objects.filter(
        is_published=True,
        start_date__gte=now,
    ).order_by('start_date')[:5]

    # Recent notifications
    recent_notifs = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:6]

    return render(request, 'communication/dashboard.html', {
        'active_announcements': active_announcements,
        'unread_notifs':        unread_notifs,
        'unread_messages':      unread_messages,
        'upcoming_events':      upcoming_events,
        'recent_notifs':        recent_notifs,
        'page_title':           'Communication',
    })