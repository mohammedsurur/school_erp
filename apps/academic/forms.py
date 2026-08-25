from django import forms
from django.core.exceptions import ValidationError
from apps.core.models import AcademicYear
from apps.accounts.models import User
from .models import Grade, Section, Subject, SubjectTeacher
from .timetable_models import Period, Timetable


# ─────────────────────────────────────────────
#  Grade Form
# ─────────────────────────────────────────────

class GradeForm(forms.ModelForm):
    class Meta:
        model  = Grade
        fields = ['name', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Grade 1, Grade 9, KG',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows':  2,
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   1,
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('Grade name is required.')
        # Check duplicate — exclude self on edit
        qs = Grade.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f'A grade named "{name}" already exists.')
        return name

    def clean_order(self):
        order = self.cleaned_data.get('order')
        if order is None or order < 1:
            raise ValidationError('Order must be a positive number.')
        return order


# ─────────────────────────────────────────────
#  Section Form
# ─────────────────────────────────────────────

class SectionForm(forms.ModelForm):
    class Meta:
        model  = Section
        fields = [
            'grade', 'name', 'academic_year',
            'class_teacher', 'capacity',
        ]
        widgets = {
            'grade': forms.Select(attrs={
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. A, B, C or East, West',
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-select',
            }),
            'class_teacher': forms.Select(attrs={
                'class': 'form-select',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   1,
                'max':   100,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show teachers in the class_teacher dropdown
        self.fields['class_teacher'].queryset = User.objects.filter(
            role='teacher', is_active=True
        ).order_by('first_name')
        self.fields['class_teacher'].empty_label = '— No Class Teacher —'
        self.fields['class_teacher'].required = False

        # Default to current academic year
        current = AcademicYear.objects.filter(is_current=True).first()
        if current and not self.instance.pk:
            self.fields['academic_year'].initial = current

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip().upper()
        if not name:
            raise ValidationError('Section name is required.')
        return name

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity is None or capacity < 1:
            raise ValidationError('Capacity must be at least 1.')
        if capacity > 100:
            raise ValidationError('Capacity cannot exceed 100 students.')
        return capacity

    def clean(self):
        cleaned     = super().clean()
        grade       = cleaned.get('grade')
        name        = cleaned.get('name')
        academic_year = cleaned.get('academic_year')

        if grade and name and academic_year:
            # Prevent duplicate section in same grade + year
            qs = Section.objects.filter(
                grade=grade,
                name__iexact=name,
                academic_year=academic_year
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'{grade} — Section {name} already exists '
                    f'in {academic_year}.'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Subject Form
# ─────────────────────────────────────────────

class SubjectForm(forms.ModelForm):
    class Meta:
        model  = Subject
        fields = [
            'name', 'code', 'grade',
            'is_core', 'pass_mark', 'full_marks',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Mathematics, English',
            }),
            'code': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. MATH101',
            }),
            'grade': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_core': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'pass_mark': forms.NumberInput(attrs={
                'class': 'form-control',
                'step':  '0.5',
                'min':   0,
            }),
            'full_marks': forms.NumberInput(attrs={
                'class': 'form-control',
                'step':  '0.5',
                'min':   1,
            }),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError('Subject code is required.')
        qs = Subject.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                f'Subject code "{code}" is already used by another subject.'
            )
        return code

    def clean_pass_mark(self):
        mark = self.cleaned_data.get('pass_mark')
        if mark is None or mark < 0:
            raise ValidationError('Pass mark cannot be negative.')
        return mark

    def clean_full_marks(self):
        marks = self.cleaned_data.get('full_marks')
        if marks is None or marks < 1:
            raise ValidationError('Full marks must be at least 1.')
        return marks

    def clean(self):
        cleaned    = super().clean()
        pass_mark  = cleaned.get('pass_mark')
        full_marks = cleaned.get('full_marks')

        if pass_mark is not None and full_marks is not None:
            if pass_mark >= full_marks:
                raise ValidationError(
                    f'Pass mark ({pass_mark}) must be less than '
                    f'full marks ({full_marks}).'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Subject–Teacher Assignment Form
# ─────────────────────────────────────────────

class SubjectTeacherForm(forms.ModelForm):
    class Meta:
        model  = SubjectTeacher
        fields = ['subject', 'section', 'teacher', 'academic_year']
        widgets = {
            'subject':       forms.Select(attrs={'class': 'form-select'}),
            'section':       forms.Select(attrs={'class': 'form-select'}),
            'teacher':       forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only active teachers
        self.fields['teacher'].queryset = User.objects.filter(
            role='teacher', is_active=True
        ).order_by('first_name')

        # Default to current year
        current = AcademicYear.objects.filter(is_current=True).first()
        if current and not self.instance.pk:
            self.fields['academic_year'].initial = current

    def clean(self):
        cleaned       = super().clean()
        subject       = cleaned.get('subject')
        section       = cleaned.get('section')
        academic_year = cleaned.get('academic_year')

        if subject and section and academic_year:
            # Check if this subject is already assigned in this section/year
            qs = SubjectTeacher.objects.filter(
                subject=subject,
                section=section,
                academic_year=academic_year
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'"{subject}" is already assigned to a teacher '
                    f'in {section} for {academic_year}. '
                    f'Edit the existing assignment instead.'
                )

            # Validate subject belongs to section's grade
            if subject.grade != section.grade:
                raise ValidationError(
                    f'"{subject}" belongs to {subject.grade} '
                    f'but {section} is in {section.grade}. '
                    f'Subject and section must be in the same grade.'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Period Form
# ─────────────────────────────────────────────

class PeriodForm(forms.ModelForm):
    class Meta:
        model  = Period
        fields = ['name', 'start_time', 'end_time', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Period 1, Break, Lunch',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type':  'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type':  'time',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   1,
            }),
        }

    def clean(self):
        cleaned    = super().clean()
        start_time = cleaned.get('start_time')
        end_time   = cleaned.get('end_time')

        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError(
                    'End time must be after start time.'
                )
            # Check for overlapping periods
            qs = Period.objects.filter(
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                overlap = qs.first()
                raise ValidationError(
                    f'This period overlaps with "{overlap.name}" '
                    f'({overlap.start_time.strftime("%H:%M")} – '
                    f'{overlap.end_time.strftime("%H:%M")}). '
                    f'Please adjust the times.'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Timetable Form
# ─────────────────────────────────────────────

class TimetableForm(forms.ModelForm):
    class Meta:
        model  = Timetable
        fields = [
            'section', 'day', 'period',
            'subject', 'teacher', 'room',
            'academic_year',
        ]
        widgets = {
            'section':       forms.Select(attrs={'class': 'form-select'}),
            'day':           forms.Select(attrs={'class': 'form-select'}),
            'period':        forms.Select(attrs={'class': 'form-select'}),
            'subject':       forms.Select(attrs={'class': 'form-select'}),
            'teacher':       forms.Select(attrs={'class': 'form-select'}),
            'room':          forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Room 101 (optional)',
            }),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = User.objects.filter(
            role='teacher', is_active=True
        ).order_by('first_name')
        current = AcademicYear.objects.filter(is_current=True).first()
        if current and not self.instance.pk:
            self.fields['academic_year'].initial = current

    def clean(self):
        cleaned       = super().clean()
        section       = cleaned.get('section')
        day           = cleaned.get('day')
        period        = cleaned.get('period')
        teacher       = cleaned.get('teacher')
        subject       = cleaned.get('subject')
        academic_year = cleaned.get('academic_year')

        if section and day and period and academic_year:
            # 1 — Same slot already booked for this section
            qs = Timetable.objects.filter(
                section=section, day=day,
                period=period, academic_year=academic_year
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'{section} already has a class in this '
                    f'slot ({day} — {period}).'
                )

        if teacher and day and period and academic_year:
            # 2 — Teacher already teaching elsewhere at same time
            qs = Timetable.objects.filter(
                teacher=teacher, day=day,
                period=period, academic_year=academic_year
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                clash = qs.first()
                raise ValidationError(
                    f'{teacher.get_full_name()} is already '
                    f'teaching {clash.subject} in {clash.section} '
                    f'at this time.'
                )

        if subject and section:
            # 3 — Subject must match section's grade
            if subject.grade != section.grade:
                raise ValidationError(
                    f'"{subject}" belongs to {subject.grade} '
                    f'but {section} is in {section.grade}.'
                )

        return cleaned