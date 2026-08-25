# apps/attendance/forms.py

from django              import forms
from django.core.exceptions import ValidationError
from django.utils        import timezone

from apps.core.models    import AcademicYear
from apps.academic.models import Section
from apps.students.models import Student, Enrollment
from .models             import Attendance


# ─────────────────────────────────────────────
#  Select date + section — step 1
# ─────────────────────────────────────────────

class AttendanceDateForm(forms.Form):
    section = forms.ModelChoiceField(
        queryset=Section.objects.select_related('grade', 'academic_year'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Select Section —',
    )
    date = forms.DateField(
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type':  'date',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only sections in the current academic year
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['section'].queryset = Section.objects.filter(
                academic_year=current
            ).select_related('grade', 'academic_year').order_by(
                'grade__order', 'name'
            )

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError(
                'Cannot mark attendance for a future date.'
            )
        return date


# ─────────────────────────────────────────────
#  Single student attendance record
# ─────────────────────────────────────────────

class AttendanceForm(forms.ModelForm):
    class Meta:
        model  = Attendance
        fields = ['status', 'note']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'note':   forms.TextInput(attrs={
                'class':       'form-control form-control-sm',
                'placeholder': 'Optional note (e.g. medical)',
            }),
        }


# ─────────────────────────────────────────────
#  Bulk attendance — one row per student
#  Used with formset_factory in the view
# ─────────────────────────────────────────────

class BulkAttendanceForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput())
    status     = forms.ChoiceField(
        choices=Attendance.STATUS_CHOICES,
        initial='present',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    note = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control form-control-sm',
            'placeholder': 'Note…',
        })
    )


# ─────────────────────────────────────────────
#  Attendance Report filter form
# ─────────────────────────────────────────────

class AttendanceReportForm(forms.Form):
    section = forms.ModelChoiceField(
        queryset=Section.objects.select_related('grade'),
        empty_label='— All Sections —',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.select_related('user'),
        empty_label='— All Students —',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type':  'date',
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type':  'date',
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Attendance.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean(self):
        cleaned   = super().clean()
        date_from = cleaned.get('date_from')
        date_to   = cleaned.get('date_to')

        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError(
                    '"Date From" cannot be after "Date To".'
                )
            # Limit report range to 90 days to avoid huge queries
            delta = (date_to - date_from).days
            if delta > 90:
                raise ValidationError(
                    'Date range cannot exceed 90 days. '
                    'Please narrow your selection.'
                )
        return cleaned