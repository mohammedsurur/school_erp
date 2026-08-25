# apps/communication/forms.py

from django                  import forms
from django.core.exceptions  import ValidationError
from django.utils            import timezone
from django.contrib.auth     import get_user_model

from apps.academic.models    import Grade, Section
from .models                 import (
    Announcement, AnnouncementAttachment,
    MessageThread, Message, Event
)

User = get_user_model()


# ─────────────────────────────────────────────
#  Announcement Form
# ─────────────────────────────────────────────

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model  = Announcement
        fields = [
            'title', 'body', 'audience',
            'priority', 'target_grade', 'target_section',
            'is_published', 'publish_date', 'expiry_date',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Announcement title…',
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 6,
                'placeholder': 'Write your announcement here…',
            }),
            'audience':       forms.Select(attrs={'class': 'form-select'}),
            'priority':       forms.Select(attrs={'class': 'form-select'}),
            'target_grade':   forms.Select(attrs={'class': 'form-select'}),
            'target_section': forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'publish_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type':  'datetime-local',
            }),
            'expiry_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type':  'datetime-local',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_grade'].required   = False
        self.fields['target_section'].required = False
        self.fields['publish_date'].required   = False
        self.fields['expiry_date'].required    = False

        self.fields['target_grade'].queryset = Grade.objects.order_by('name')
        self.fields['target_section'].queryset = Section.objects.select_related(
            'grade'
        ).order_by('grade__name', 'name')
        self.fields['target_section'].label_from_instance = (
            lambda obj: f"{obj.grade.name} — {obj.name}"
        )

    def clean(self):
        cleaned      = super().clean()
        publish_date = cleaned.get('publish_date')
        expiry_date  = cleaned.get('expiry_date')

        if publish_date and publish_date < timezone.now():
            raise ValidationError(
                'Scheduled publish date cannot be in the past.'
            )
        if publish_date and expiry_date and expiry_date <= publish_date:
            raise ValidationError(
                'Expiry date must be after the publish date.'
            )
        if expiry_date and not publish_date:
            if expiry_date < timezone.now():
                raise ValidationError(
                    'Expiry date cannot be in the past.'
                )
        return cleaned


class AnnouncementAttachmentForm(forms.ModelForm):
    class Meta:
        model  = AnnouncementAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


# ─────────────────────────────────────────────
#  Message / Thread Forms
# ─────────────────────────────────────────────

class NewThreadForm(forms.Form):
    """Start a new message thread"""
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by(
            'first_name', 'last_name'
        ),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select', 'size': 6,
        }),
        help_text='Hold Ctrl to select multiple recipients'
    )
    subject = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Subject (optional)…',
        })
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 4,
            'placeholder': 'Write your message…',
        })
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_user = current_user
        if current_user:
            self.fields['recipients'].queryset = User.objects.filter(
                is_active=True
            ).exclude(pk=current_user.pk).order_by('first_name', 'last_name')

        self.fields['recipients'].label_from_instance = (
            lambda u: f"{u.get_full_name()} ({u.get_role_display() if hasattr(u, 'get_role_display') else u.role})"
        )

    def clean_recipients(self):
        recipients = self.cleaned_data.get('recipients')
        if not recipients:
            raise ValidationError('Please select at least one recipient.')
        return recipients


class ReplyForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class':       'form-control',
            'rows':        3,
            'placeholder': 'Write your reply…',
        })
    )

    def clean_body(self):
        body = self.cleaned_data.get('body', '').strip()
        if not body:
            raise ValidationError('Message cannot be empty.')
        return body


# ─────────────────────────────────────────────
#  Event Form
# ─────────────────────────────────────────────

class EventForm(forms.ModelForm):
    class Meta:
        model  = Event
        fields = [
            'title', 'description', 'category',
            'start_date', 'end_date', 'all_day',
            'location', 'audience', 'is_published',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Event title…',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Event description…',
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local',
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local',
            }),
            'all_day': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'location': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. School Hall, Grade 8 Classroom…',
            }),
            'audience':     forms.Select(attrs={'class': 'form-select'}),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['location'].required    = False

    def clean(self):
        cleaned    = super().clean()
        start_date = cleaned.get('start_date')
        end_date   = cleaned.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise ValidationError('End date must be after start date.')
        return cleaned


# ─────────────────────────────────────────────
#  Filter Forms
# ─────────────────────────────────────────────

class AnnouncementFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('',          'All Status'),
        ('active',    'Active'),
        ('draft',     'Draft'),
        ('scheduled', 'Scheduled'),
        ('expired',   'Expired'),
    ]
    PRIORITY_CHOICES = [
        ('', 'All Priorities'),
        ('normal',   'Normal'),
        ('urgent',   'Urgent'),
        ('critical', 'Critical'),
    ]

    q        = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Search announcements…',
        })
    )
    audience = forms.ChoiceField(
        required=False,
        choices=[('', 'All Audiences')] + Announcement.AUDIENCE,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status   = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class EventFilterForm(forms.Form):
    PERIOD = [
        ('',           'All Events'),
        ('upcoming',   'Upcoming'),
        ('ongoing',    'Ongoing'),
        ('past',       'Past'),
        ('this_month', 'This Month'),
    ]
    q        = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Search events…',
        })
    )
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + Event.CATEGORY,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    period   = forms.ChoiceField(
        required=False,
        choices=PERIOD,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )