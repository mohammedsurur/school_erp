# apps/reports/forms.py

from django          import forms
from django.utils    import timezone
from apps.core.models   import *

from apps.academic.models   import *
from apps.students.models   import Student
from apps.staff.models      import Staff
from apps.exams.models      import Exam
from apps.fees.models       import FeeCategory
from apps.transport.models  import Route


# ─────────────────────────────────────────────
#  Shared widgets / helpers
# ─────────────────────────────────────────────

DATE_W = forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})

def SEL_W():
    return forms.Select(attrs={'class': 'form-select'})

def _year_qs():
    return AcademicYear.objects.order_by('-start_date')

def _term_qs():
    return Term.objects.select_related('academic_year').order_by(
        '-academic_year__start_date', 'start_date'
    )

def _grade_qs():
    return Grade.objects.order_by('name')

def _section_qs():
    return Section.objects.select_related('grade').order_by(
        'grade__name', 'name'
    )


# ─────────────────────────────────────────────
#  1. Report Card
# ─────────────────────────────────────────────

class ReportCardForm(forms.Form):
    academic_year = forms.ModelChoiceField(
        queryset=_year_qs(),
        widget=SEL_W(),
        help_text='Academic year for this report card'
    )
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.filter(
            is_published=True
        ).order_by('-created_at'),
        widget=SEL_W(),
    )
    grade = forms.ModelChoiceField(
        queryset=_grade_qs(),
        required=False,
        empty_label='All Grades',
        widget=SEL_W(),
    )
    section = forms.ModelChoiceField(
        queryset=_section_qs(),
        required=False,
        empty_label='All Sections',
        widget=SEL_W(),
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.select_related('user').order_by(
            'user__first_name'
        ),
        required=False,
        empty_label='All Students (bulk)',
        widget=SEL_W(),
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF')],
        widget=SEL_W(),
        initial='pdf'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set label_from_instance AFTER field creation
        self.fields['section'].label_from_instance = (
            lambda obj: f"{obj.grade.name} — {obj.name}"
        )
        self.fields['student'].label_from_instance = (
            lambda obj: obj.user.get_full_name()
        )
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current.pk


# ─────────────────────────────────────────────
#  2. Exam Results
# ─────────────────────────────────────────────

class ExamResultsForm(forms.Form):
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.order_by('-created_at'),
        widget=SEL_W(),
    )
    grade = forms.ModelChoiceField(
        queryset=_grade_qs(),
        required=False,
        empty_label='All Grades',
        widget=SEL_W(),
    )
    section = forms.ModelChoiceField(
        queryset=_section_qs(),
        required=False,
        empty_label='All Sections',
        widget=SEL_W(),
    )
    include_rank = forms.BooleanField(
        required=False,
        initial=True,
        label='Include class rank',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].label_from_instance = (
            lambda obj: f"{obj.grade.name} — {obj.name}"
        )


# ─────────────────────────────────────────────
#  3. Attendance Report
# ─────────────────────────────────────────────

class AttendanceReportForm(forms.Form):
    SCOPE = [
        ('student', 'Single Student'),
        ('class',   'Entire Class'),
        ('summary', 'School Summary'),
    ]

    scope = forms.ChoiceField(
        choices=SCOPE,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='class',
    )
    academic_year = forms.ModelChoiceField(
        queryset=_year_qs(),
        widget=SEL_W(),
    )
    term = forms.ModelChoiceField(
        queryset=_term_qs(),
        required=False,
        empty_label='All Terms',
        widget=SEL_W(),
    )
    grade = forms.ModelChoiceField(
        queryset=_grade_qs(),
        required=False,
        empty_label='All Grades',
        widget=SEL_W(),
    )
    section = forms.ModelChoiceField(
        queryset=_section_qs(),
        required=False,
        empty_label='All Sections',
        widget=SEL_W(),
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.select_related('user').order_by(
            'user__first_name'
        ),
        required=False,
        empty_label='Select student…',
        widget=SEL_W(),
    )
    date_from = forms.DateField(
        required=False,
        widget=DATE_W,
        label='From Date',
    )
    date_to = forms.DateField(
        required=False,
        widget=DATE_W,
        label='To Date',
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].label_from_instance = (
            lambda obj: f"{obj.grade.name} — {obj.name}"
        )
        self.fields['student'].label_from_instance = (
            lambda obj: obj.user.get_full_name()
        )
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current.pk


# ─────────────────────────────────────────────
#  4. Fee Collection Report
# ─────────────────────────────────────────────

class FeeCollectionForm(forms.Form):
    PERIOD = [
        ('daily',   'Daily'),
        ('monthly', 'Monthly'),
        ('term',    'By Term'),
        ('annual',  'Annual'),
        ('custom',  'Custom Range'),
    ]

    period = forms.ChoiceField(
        choices=PERIOD,
        widget=SEL_W(),
        initial='monthly',
    )
    academic_year = forms.ModelChoiceField(
        queryset=_year_qs(),
        widget=SEL_W(),
    )
    date_from = forms.DateField(
        required=False,
        widget=DATE_W,
        label='From Date',
    )
    date_to = forms.DateField(
        required=False,
        widget=DATE_W,
        label='To Date',
    )
    fee_category = forms.ModelChoiceField(
        queryset=FeeCategory.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=SEL_W(),
    )
    grade = forms.ModelChoiceField(
        queryset=_grade_qs(),
        required=False,
        empty_label='All Grades',
        widget=SEL_W(),
    )
    include_outstanding = forms.BooleanField(
        required=False,
        initial=True,
        label='Include outstanding balances',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current.pk

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('period') == 'custom':
            if not cleaned.get('date_from') or not cleaned.get('date_to'):
                raise forms.ValidationError(
                    'Please set both From and To dates for a custom range.'
                )
        return cleaned


# ─────────────────────────────────────────────
#  5. Outstanding Fees Report
# ─────────────────────────────────────────────

class OutstandingFeesForm(forms.Form):
    academic_year = forms.ModelChoiceField(
        queryset=_year_qs(),
        widget=SEL_W(),
    )
    grade = forms.ModelChoiceField(
        queryset=_grade_qs(),
        required=False,
        empty_label='All Grades',
        widget=SEL_W(),
    )
    section = forms.ModelChoiceField(
        queryset=_section_qs(),
        required=False,
        empty_label='All Sections',
        widget=SEL_W(),
    )
    overdue_only = forms.BooleanField(
        required=False,
        label='Overdue only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].label_from_instance = (
            lambda obj: f"{obj.grade.name} — {obj.name}"
        )
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current.pk


# ─────────────────────────────────────────────
#  6. Library Report
# ─────────────────────────────────────────────

class LibraryReportForm(forms.Form):
    REPORT_TYPE = [
        ('issuances', 'Book Issuances'),
        ('overdue',   'Overdue Books'),
        ('fines',     'Fines Summary'),
        ('catalog',   'Book Catalog'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPE,
        widget=SEL_W(),
        initial='issuances',
    )
    date_from = forms.DateField(
        required=False,
        widget=DATE_W,
        label='From Date',
    )
    date_to = forms.DateField(
        required=False,
        widget=DATE_W,
        label='To Date',
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['date_from'].initial = today.replace(day=1)
        self.fields['date_to'].initial   = today


# ─────────────────────────────────────────────
#  7. Transport Report
# ─────────────────────────────────────────────

class TransportReportForm(forms.Form):
    REPORT_TYPE = [
        ('assignments', 'Student Assignments'),
        ('attendance',  'Transport Attendance'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPE,
        widget=SEL_W(),
        initial='assignments',
    )
    route = forms.ModelChoiceField(
        queryset=Route.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='All Routes',
        widget=SEL_W(),
    )
    academic_year = forms.ModelChoiceField(
        queryset=_year_qs(),
        widget=SEL_W(),
    )
    date_from = forms.DateField(
        required=False,
        widget=DATE_W,
        label='From Date (attendance only)',
    )
    date_to = forms.DateField(
        required=False,
        widget=DATE_W,
        label='To Date (attendance only)',
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current.pk


# ─────────────────────────────────────────────
#  8. Student List Report
# ─────────────────────────────────────────────

class StudentListForm(forms.Form):
    INCLUDE = [
        ('basic',   'Basic Info (name, ID, grade)'),
        ('contact', 'With Contact Details'),
        ('full',    'Full Profile'),
    ]

    academic_year = forms.ModelChoiceField(
        queryset=_year_qs(),
        widget=SEL_W(),
    )
    grade = forms.ModelChoiceField(
        queryset=_grade_qs(),
        required=False,
        empty_label='All Grades',
        widget=SEL_W(),
    )
    section = forms.ModelChoiceField(
        queryset=_section_qs(),
        required=False,
        empty_label='All Sections',
        widget=SEL_W(),
    )
    include_fields = forms.ChoiceField(
        choices=INCLUDE,
        widget=SEL_W(),
        initial='basic',
        label='Information to Include',
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].label_from_instance = (
            lambda obj: f"{obj.grade.name} — {obj.name}"
        )
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current.pk


# ─────────────────────────────────────────────
#  9. Staff List Report
# ─────────────────────────────────────────────

class StaffListForm(forms.Form):
    DEPARTMENT = [
        ('',         'All Departments'),
        ('teaching', 'Teaching Staff'),
        ('admin',    'Administrative'),
        ('support',  'Support Staff'),
    ]

    department = forms.ChoiceField(
        choices=DEPARTMENT,
        required=False,
        widget=SEL_W(),
    )
    include_contact = forms.BooleanField(
        required=False,
        initial=True,
        label='Include contact details',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    format = forms.ChoiceField(
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        widget=SEL_W(),
    )


# ─────────────────────────────────────────────
#  10. Report History Filter
# ─────────────────────────────────────────────

class ReportHistoryFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('',        'All Status'),
        ('ready',   'Ready'),
        ('pending', 'Pending'),
        ('failed',  'Failed'),
    ]

    report_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + [
            ('report_card',        'Student Report Card'),
            ('exam_results',       'Exam Results'),
            ('class_results',      'Class Results Summary'),
            ('attendance_student', 'Student Attendance'),
            ('attendance_class',   'Class Attendance'),
            ('attendance_summary', 'Attendance Summary'),
            ('fee_collection',     'Fee Collection'),
            ('fee_outstanding',    'Outstanding Fees'),
            ('fee_daily',          'Daily Collection'),
            ('library_issuances',  'Library Issuances'),
            ('library_overdue',    'Overdue Books'),
            ('library_fines',      'Library Fines'),
            ('transport_students', 'Transport Assignments'),
            ('student_list',       'Student List'),
            ('staff_list',         'Staff List'),
        ],
        widget=SEL_W(),
    )
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=SEL_W(),
    )
    date_from = forms.DateField(
        required=False,
        widget=DATE_W,
    )
    date_to = forms.DateField(
        required=False,
        widget=DATE_W,
    )