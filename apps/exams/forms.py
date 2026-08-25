# apps/exams/forms.py

from django                  import forms
from django.core.exceptions  import ValidationError
from django.utils            import timezone

from apps.core.models        import AcademicYear
from apps.academic.models    import Grade, Section, Subject
from .models                 import (
    Exam, ExamSchedule, ExamComponent,
    ComponentResult, SubjectResult, ReportCard
)


# ─────────────────────────────────────────────
#  Exam Form
# ─────────────────────────────────────────────

class ExamForm(forms.ModelForm):
    class Meta:
        model  = Exam
        fields = [
            'name', 'exam_type', 'academic_year',
            'term', 'grade', 'start_date', 'end_date',
            'description',
        ]
        widgets = {
            'name':          forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. First Semester Exam 2024'
            }),
            'exam_type':     forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'term':          forms.Select(attrs={'class': 'form-select'}),
            'grade':         forms.Select(attrs={'class': 'form-select'}),
            'start_date':    forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'end_date':      forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'description':   forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3
            }),
        }

    def clean(self):
        cleaned    = super().clean()
        start_date = cleaned.get('start_date')
        end_date   = cleaned.get('end_date')
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('End date cannot be before start date.')
            if (end_date - start_date).days > 30:
                raise ValidationError('Exam period cannot exceed 30 days.')
        return cleaned


# ─────────────────────────────────────────────
#  Exam Schedule Form
# ─────────────────────────────────────────────

class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model  = ExamSchedule
        fields = ['subject', 'section', 'exam_date', 'start_time', 'end_time', 'room']
        widgets = {
            'subject':    forms.Select(attrs={'class': 'form-select'}),
            'section':    forms.Select(attrs={'class': 'form-select'}),
            'exam_date':  forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'end_time':   forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time'
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Hall A'
            }),
        }

    def __init__(self, *args, exam=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam = exam
        if exam:
            self.fields['subject'].queryset = Subject.objects.filter(
                grade=exam.grade
            ).order_by('name')
            self.fields['section'].queryset = Section.objects.filter(
                grade=exam.grade,
                academic_year=exam.academic_year
            ).order_by('name')

    def clean(self):
        cleaned    = super().clean()
        start_time = cleaned.get('start_time')
        end_time   = cleaned.get('end_time')
        exam_date  = cleaned.get('exam_date')
        subject    = cleaned.get('subject')
        section    = cleaned.get('section')

        if start_time and end_time and end_time <= start_time:
            raise ValidationError('End time must be after start time.')

        if self.exam and exam_date:
            if not (self.exam.start_date <= exam_date <= self.exam.end_date):
                raise ValidationError(
                    f'Exam date must be between '
                    f'{self.exam.start_date} and {self.exam.end_date}.'
                )

        # Duplicate check
        if self.exam and subject and section:
            qs = ExamSchedule.objects.filter(
                exam=self.exam, subject=subject, section=section
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'"{subject.name}" is already scheduled '
                    f'for {section.grade} — {section.name} in this exam.'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Exam Component Form
#  Defines one component (Quiz/Mid/Final/etc.)
#  with its max marks
# ─────────────────────────────────────────────

class ExamComponentForm(forms.ModelForm):
    class Meta:
        model  = ExamComponent
        fields = ['component_type', 'max_marks', 'order']
        widgets = {
            'component_type': forms.Select(attrs={'class': 'form-select'}),
            'max_marks':      forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 100
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1
            }),
        }

    def __init__(self, *args, exam_schedule=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.exam_schedule = exam_schedule

    def clean(self):
        cleaned        = super().clean()
        component_type = cleaned.get('component_type')
        max_marks      = cleaned.get('max_marks')

        # Recommended range check
        if component_type and max_marks:
            ranges = ExamComponent.COMPONENT_RANGES.get(component_type)
            if ranges:
                lo, hi = ranges
                if not (lo <= max_marks <= hi):
                    raise ValidationError(
                        f'{ExamComponent(component_type=component_type).get_component_type_display()} '
                        f'should be between {lo} and {hi} marks '
                        f'(you entered {max_marks}).'
                    )

        # Total must not exceed 100
        if self.exam_schedule and max_marks:
            existing = ExamComponent.objects.filter(
                exam_schedule=self.exam_schedule
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            # Check duplicate component type
            if component_type:
                dup = existing.filter(component_type=component_type)
                if dup.exists():
                    raise ValidationError(
                        f'A "{self.instance.get_component_type_display()}" '
                        f'component already exists for this schedule.'
                    )

            current_total = sum(c.max_marks for c in existing)
            if current_total + max_marks > 100:
                raise ValidationError(
                    f'Adding {max_marks} marks would make the total '
                    f'{current_total + max_marks}/100. '
                    f'All components must sum to exactly 100. '
                    f'Remaining: {100 - current_total} marks.'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Bulk Component Result Entry
#  One row per student, per component
# ─────────────────────────────────────────────

class ComponentResultEntryForm(forms.Form):
    """
    Used in the bulk result entry view.
    One form per student — marks for each component
    displayed as a row in the table.
    Ethiopian system: marks out of component.max_marks.
    No individual pass/fail — only total matters.
    """
    student_id = forms.IntegerField(widget=forms.HiddenInput())
    is_absent  = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input absent-check'})
    )

    def __init__(self, *args, components=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.components = components or []
        for comp in self.components:
            self.fields[f'marks_{comp.pk}'] = forms.DecimalField(
                max_digits=5, decimal_places=2,
                min_value=0,
                max_value=comp.max_marks,
                required=False,
                widget=forms.NumberInput(attrs={
                    'class':         f'form-control form-control-sm marks-input',
                    'step':          '0.5',
                    'min':           0,
                    'max':           comp.max_marks,
                    'placeholder':   f'/{comp.max_marks}',
                    'data-max':      comp.max_marks,
                    'data-comp':     comp.pk,
                })
            )

    def clean(self):
        cleaned   = super().clean()
        is_absent = cleaned.get('is_absent')
        if is_absent:
            # Zero out all marks if absent
            for comp in self.components:
                cleaned[f'marks_{comp.pk}'] = 0
            return cleaned

        # Validate each component
        for comp in self.components:
            marks = cleaned.get(f'marks_{comp.pk}')
            if marks is None:
                raise ValidationError(
                    f'Please enter marks for '
                    f'{comp.get_component_type_display()} '
                    f'or mark student as absent.'
                )
            if marks < 0:
                raise ValidationError(
                    f'{comp.get_component_type_display()}: '
                    f'marks cannot be negative.'
                )
            if marks > comp.max_marks:
                raise ValidationError(
                    f'{comp.get_component_type_display()}: '
                    f'marks ({marks}) exceed maximum ({comp.max_marks}).'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Report Card Remarks
# ─────────────────────────────────────────────

class ReportCardRemarksForm(forms.ModelForm):
    class Meta:
        model  = ReportCard
        fields = ['teacher_remarks']
        widgets = {
            'teacher_remarks': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Add remarks for this student…',
            })
        }