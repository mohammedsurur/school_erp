# apps/communication/models.py

from django.db        import models
from django.utils     import timezone


# ─────────────────────────────────────────────
#  Announcement
# ─────────────────────────────────────────────

class Announcement(models.Model):
    AUDIENCE = [
        ('all',          'Everyone'),
        ('students',     'Students Only'),
        ('parents',      'Parents Only'),
        ('teachers',     'Teachers Only'),
        ('staff',        'All Staff'),
        ('admin',        'Admin Only'),
    ]
    PRIORITY = [
        ('normal',  'Normal'),
        ('urgent',  'Urgent'),
        ('critical','Critical'),
    ]

    title       = models.CharField(max_length=255)
    body        = models.TextField()
    audience    = models.CharField(
        max_length=20, choices=AUDIENCE, default='all'
    )
    priority    = models.CharField(
        max_length=10, choices=PRIORITY, default='normal'
    )
    # Optionally target a specific grade/class
    target_grade = models.ForeignKey(
        'academic.Grade', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='announcements',
        help_text='Leave blank to target all grades'
    )
    target_section = models.ForeignKey(
        'academic.Section', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='announcements',
        help_text='Leave blank to target all sections'
    )
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(
        null=True, blank=True,
        help_text='Schedule for future publishing (leave blank to publish now)'
    )
    expiry_date  = models.DateTimeField(
        null=True, blank=True,
        help_text='Auto-hide after this date'
    )
    created_by   = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='announcements_created'
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        if not self.is_published:
            return False
        if self.publish_date and self.publish_date > now:
            return False
        if self.expiry_date and self.expiry_date < now:
            return False
        return True

    @property
    def status_label(self):
        now = timezone.now()
        if not self.is_published:
            return 'draft'
        if self.publish_date and self.publish_date > now:
            return 'scheduled'
        if self.expiry_date and self.expiry_date < now:
            return 'expired'
        return 'active'


class AnnouncementAttachment(models.Model):
    announcement = models.ForeignKey(
        Announcement, on_delete=models.CASCADE,
        related_name='attachments'
    )
    file        = models.FileField(upload_to='communication/attachments/')
    filename    = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename or self.file.name

    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name.split('/')[-1]
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
#  Direct Message Thread
# ─────────────────────────────────────────────

class MessageThread(models.Model):
    """A conversation between two or more participants"""
    subject      = models.CharField(max_length=255, blank=True)
    participants = models.ManyToManyField(
        'accounts.User', related_name='message_threads'
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.subject or f"Thread #{self.pk}"

    @property
    def last_message(self):
        return self.messages.order_by('-sent_at').first()

    def unread_count(self, user):
        return self.messages.exclude(
            read_by=user
        ).exclude(sender=user).count()


class Message(models.Model):
    thread   = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE,
        related_name='messages'
    )
    sender   = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    body     = models.TextField()
    read_by  = models.ManyToManyField(
        'accounts.User', blank=True,
        related_name='read_messages'
    )
    sent_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return (
            f"{self.sender.get_full_name()} → "
            f"{self.thread} ({self.sent_at:%Y-%m-%d})"
        )

    def mark_read(self, user):
        self.read_by.add(user)

    def is_read_by(self, user):
        return self.read_by.filter(pk=user.pk).exists()


# ─────────────────────────────────────────────
#  Notification  (system-generated)
# ─────────────────────────────────────────────

class Notification(models.Model):
    TYPE = [
        ('announcement', 'Announcement'),
        ('fee',          'Fee Due'),
        ('exam',         'Exam Result'),
        ('attendance',   'Attendance Alert'),
        ('library',      'Library'),
        ('transport',    'Transport'),
        ('message',      'New Message'),
        ('general',      'General'),
    ]

    recipient   = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='notifications'
    )
    notif_type  = models.CharField(
        max_length=20, choices=TYPE, default='general'
    )
    title       = models.CharField(max_length=255)
    body        = models.TextField(blank=True)
    link        = models.CharField(
        max_length=500, blank=True,
        help_text='Optional URL to redirect when notification is clicked'
    )
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.get_full_name()} — {self.title}"

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    @classmethod
    def send(cls, recipient, title, body='', notif_type='general', link=''):
        """Helper to create a notification in one call"""
        return cls.objects.create(
            recipient=recipient,
            title=title,
            body=body,
            notif_type=notif_type,
            link=link,
        )

    @classmethod
    def broadcast(cls, recipients, title, body='', notif_type='general', link=''):
        """Send same notification to multiple users"""
        notifs = [
            cls(
                recipient=r,
                title=title,
                body=body,
                notif_type=notif_type,
                link=link,
            )
            for r in recipients
        ]
        cls.objects.bulk_create(notifs)


# ─────────────────────────────────────────────
#  Event / Calendar
# ─────────────────────────────────────────────

class Event(models.Model):
    CATEGORY = [
        ('academic',    'Academic'),
        ('exam',        'Exam'),
        ('holiday',     'Holiday'),
        ('sport',       'Sports'),
        ('cultural',    'Cultural'),
        ('meeting',     'Meeting'),
        ('other',       'Other'),
    ]

    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    category     = models.CharField(
        max_length=15, choices=CATEGORY, default='other'
    )
    start_date   = models.DateTimeField()
    end_date     = models.DateTimeField()
    all_day      = models.BooleanField(default=False)
    location     = models.CharField(max_length=255, blank=True)
    audience     = models.CharField(
        max_length=20,
        choices=Announcement.AUDIENCE,
        default='all'
    )
    is_published = models.BooleanField(default=True)
    created_by   = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='events_created'
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.title} ({self.start_date:%Y-%m-%d})"

    @property
    def duration_days(self):
        return (self.end_date.date() - self.start_date.date()).days + 1

    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def is_past(self):
        return self.end_date < timezone.now()