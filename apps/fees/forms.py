# apps/fees/forms.py

from django              import forms
from django.core.exceptions import ValidationError
from django.utils        import timezone

from apps.core.models    import AcademicYear
from apps.academic.models import Grade
from apps.students.models import Student
from .models             import (
    FeeCategory, FeeStructure, StudentFee, Payment
)


# ─────────────────────────────────────────────
#  Fee Category Form
# ─────────────────────────────────────────────

class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model  = FeeCategory
        fields = ['name', 'description', 'is_mandatory']
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Tuition Fee, Library Fee',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
            'is_mandatory': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs   = FeeCategory.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                f'A fee category named "{name}" already exists.'
            )
        return name


# ─────────────────────────────────────────────
#  Fee Structure Form
# ─────────────────────────────────────────────

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model  = FeeStructure
        fields = [
            'academic_year', 'term', 'grade',
            'fee_category', 'amount', 'due_date',
        ]
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'term':          forms.Select(attrs={'class': 'form-select'}),
            'grade':         forms.Select(attrs={'class': 'form-select'}),
            'fee_category':  forms.Select(attrs={'class': 'form-select'}),
            'amount':        forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': 0,
                'placeholder': '0.00'
            }),
            'due_date':      forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['term'].required     = False
        self.fields['due_date'].required = False

        current = AcademicYear.objects.filter(is_current=True).first()
        if current and not self.instance.pk:
            self.fields['academic_year'].initial = current

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount < 0:
            raise ValidationError('Amount cannot be negative.')
        return amount

    def clean(self):
        cleaned       = super().clean()
        academic_year = cleaned.get('academic_year')
        grade         = cleaned.get('grade')
        fee_category  = cleaned.get('fee_category')
        term          = cleaned.get('term')
        due_date      = cleaned.get('due_date')

        # Duplicate check
        if academic_year and grade and fee_category:
            qs = FeeStructure.objects.filter(
                academic_year=academic_year,
                grade=grade,
                fee_category=fee_category,
                term=term,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'A fee structure for "{fee_category}" in '
                    f'{grade} — {academic_year} already exists.'
                )

        # Due date must be in the future for new records
        if due_date and not self.instance.pk:
            if due_date < timezone.now().date():
                raise ValidationError(
                    'Due date cannot be in the past for new fee structures.'
                )

        # Due date must fall within academic year dates
        if due_date and academic_year:
            if not (academic_year.start_date <= due_date <= academic_year.end_date):
                raise ValidationError(
                    f'Due date must fall within the academic year '
                    f'({academic_year.start_date} – {academic_year.end_date}).'
                )

        return cleaned


# ─────────────────────────────────────────────
#  Student Fee Form (assign fee to student)
# ─────────────────────────────────────────────

class StudentFeeForm(forms.ModelForm):
    class Meta:
        model  = StudentFee
        fields = [
            'student', 'fee_structure',
            'amount_due', 'discount',
            'due_date', 'waiver_reason',
        ]
        widgets = {
            'student':       forms.Select(attrs={'class': 'form-select'}),
            'fee_structure': forms.Select(attrs={'class': 'form-select'}),
            'amount_due':    forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': 0,
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': 0,
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'waiver_reason': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Reason for waiver or discount…',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['discount'].required      = False
        self.fields['due_date'].required      = False
        self.fields['waiver_reason'].required = False

    def clean(self):
        cleaned    = super().clean()
        amount_due = cleaned.get('amount_due')
        discount   = cleaned.get('discount') or 0
        student    = cleaned.get('student')
        fee_struct = cleaned.get('fee_structure')

        if amount_due is not None and amount_due < 0:
            raise ValidationError('Amount due cannot be negative.')

        if discount and amount_due and discount > amount_due:
            raise ValidationError(
                f'Discount ({discount}) cannot exceed '
                f'amount due ({amount_due}).'
            )

        # Prevent duplicate assignment
        if student and fee_struct:
            qs = StudentFee.objects.filter(
                student=student, fee_structure=fee_struct
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'This fee is already assigned to '
                    f'{student.user.get_full_name()}.'
                )

        return cleaned


# ─────────────────────────────────────────────
#  Bulk Assign Fee Structure to a Grade
# ─────────────────────────────────────────────

class BulkFeeAssignForm(forms.Form):
    """
    Assigns a fee structure to ALL active enrolled students
    in the selected grade and academic year.
    """
    fee_structure = forms.ModelChoiceField(
        queryset=FeeStructure.objects.select_related(
            'fee_category', 'grade', 'academic_year'
        ),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='— Select Fee Structure —',
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.order_by('-start_date'),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current


# ─────────────────────────────────────────────
#  Payment Form
# ─────────────────────────────────────────────

class PaymentForm(forms.ModelForm):
    class Meta:
        model  = Payment
        fields = [
            'amount', 'payment_method',
            'payment_date', 'reference_number', 'note',
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': 0.01,
                'placeholder': '0.00',
            }),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_date':   forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'reference_number': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Receipt / transaction no. (optional)',
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Optional note…',
            }),
        }

    def __init__(self, student_fee=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.student_fee = student_fee
        self.fields['reference_number'].required = False
        self.fields['note'].required             = False

        # Default to today
        if not self.instance.pk:
            self.fields['payment_date'].initial = timezone.now().date()

    def clean_payment_date(self):
        date = self.cleaned_data.get('payment_date')
        if date and date > timezone.now().date():
            raise ValidationError('Payment date cannot be in the future.')
        return date

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is None or amount <= 0:
            raise ValidationError('Payment amount must be greater than 0.')

        if self.student_fee:
            balance = self.student_fee.balance
            if float(amount) > balance:
                raise ValidationError(
                    f'Payment ({amount}) exceeds outstanding '
                    f'balance ({balance:.2f}). '
                    f'Maximum payable is {balance:.2f}.'
                )
        return amount


# ─────────────────────────────────────────────
#  Fee Report Filter Form
# ─────────────────────────────────────────────

class FeeReportForm(forms.Form):
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.order_by('-start_date'),
        required=False,
        empty_label='All Years',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.order_by('order'),
        required=False,
        empty_label='All Grades',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + StudentFee.STATUS,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fee_category = forms.ModelChoiceField(
        queryset=FeeCategory.objects.order_by('name'),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date'
        })
    )

    def clean(self):
        cleaned   = super().clean()
        date_from = cleaned.get('date_from')
        date_to   = cleaned.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise ValidationError('"Date From" cannot be after "Date To".')
        return cleaned