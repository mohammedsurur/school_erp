# apps/library/forms.py

from django                 import forms
from django.core.exceptions import ValidationError
from django.utils           import timezone
from datetime               import timedelta

from apps.students.models   import Student
from apps.staff.models      import Staff
from .models                import (
    BookCategory, Author, Publisher, Book,
    BookCopy, BookIssuance, Fine, Reservation
)


# ─────────────────────────────────────────────
#  Book Category
# ─────────────────────────────────────────────

class BookCategoryForm(forms.ModelForm):
    class Meta:
        model  = BookCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Science, Mathematics, Fiction',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs   = BookCategory.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f'Category "{name}" already exists.')
        return name


# ─────────────────────────────────────────────
#  Author
# ─────────────────────────────────────────────

class AuthorForm(forms.ModelForm):
    class Meta:
        model  = Author
        fields = ['first_name', 'last_name', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'bio':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ─────────────────────────────────────────────
#  Publisher
# ─────────────────────────────────────────────

class PublisherForm(forms.ModelForm):
    class Meta:
        model  = Publisher
        fields = ['name', 'address']
        widgets = {
            'name':    forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs   = Publisher.objects.filter(name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f'Publisher "{name}" already exists.')
        return name


# ─────────────────────────────────────────────
#  Book
# ─────────────────────────────────────────────

class BookForm(forms.ModelForm):
    class Meta:
        model  = Book
        fields = [
            'title', 'isbn', 'authors', 'category',
            'publisher', 'publication_year', 'edition',
            'language', 'description', 'cover_image',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Book title',
            }),
            'isbn': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'ISBN-10 or ISBN-13',
            }),
            'authors': forms.SelectMultiple(attrs={
                'class': 'form-select', 'size': 5,
            }),
            'category':    forms.Select(attrs={'class': 'form-select'}),
            'publisher':   forms.Select(attrs={'class': 'form-select'}),
            'publication_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   1800,
                'max':   2100,
                'placeholder': 'e.g. 2022',
            }),
            'edition': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. 3rd Edition',
            }),
            'language':    forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Short description…',
            }),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['isbn'].required             = False
        self.fields['authors'].required          = False
        self.fields['category'].required         = False
        self.fields['publisher'].required        = False
        self.fields['publication_year'].required = False
        self.fields['edition'].required          = False
        self.fields['description'].required      = False
        self.fields['cover_image'].required      = False


# ─────────────────────────────────────────────
#  Book Copy
# ─────────────────────────────────────────────

class BookCopyForm(forms.ModelForm):
    class Meta:
        model  = BookCopy
        fields = ['accession_number', 'condition', 'status', 'acquired_date', 'notes']
        widgets = {
            'accession_number': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. LIB-0001',
            }),
            'condition':     forms.Select(attrs={'class': 'form-select'}),
            'status':        forms.Select(attrs={'class': 'form-select'}),
            'acquired_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['acquired_date'].required = False
        self.fields['notes'].required         = False

    def clean_accession_number(self):
        acc = self.cleaned_data.get('accession_number', '').strip().upper()
        qs  = BookCopy.objects.filter(accession_number=acc)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                f'Accession number "{acc}" already exists.'
            )
        return acc


# ─────────────────────────────────────────────
#  Book Issuance
# ─────────────────────────────────────────────

class BookIssuanceForm(forms.ModelForm):
    class Meta:
        model  = BookIssuance
        fields = [
            'book_copy', 'borrower_type',
            'student', 'staff',
            'issued_date', 'due_date', 'notes',
        ]
        widgets = {
            'book_copy':     forms.Select(attrs={'class': 'form-select'}),
            'borrower_type': forms.Select(attrs={
                'class':    'form-select',
                'onchange': 'toggleBorrower(this.value)',
            }),
            'student':    forms.Select(attrs={'class': 'form-select'}),
            'staff':      forms.Select(attrs={'class': 'form-select'}),
            'issued_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
                'placeholder': 'Optional notes…',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only available copies
        self.fields['book_copy'].queryset = BookCopy.objects.filter(
            status='available'
        ).select_related('book').order_by('book__title')
        self.fields['book_copy'].label_from_instance = (
            lambda obj: f"{obj.book.title} [{obj.accession_number}]"
        )
        self.fields['student'].required = False
        self.fields['staff'].required   = False
        self.fields['notes'].required   = False

        # Default due date = 14 days from today
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['issued_date'].initial = today
            self.fields['due_date'].initial    = today + timedelta(days=14)

    def clean(self):
        cleaned       = super().clean()
        borrower_type = cleaned.get('borrower_type')
        student       = cleaned.get('student')
        staff         = cleaned.get('staff')
        issued_date   = cleaned.get('issued_date')
        due_date      = cleaned.get('due_date')
        book_copy     = cleaned.get('book_copy')

        # Borrower validation
        if borrower_type == 'student' and not student:
            raise ValidationError('Please select a student.')
        if borrower_type == 'staff' and not staff:
            raise ValidationError('Please select a staff member.')

        # Date validation
        if issued_date and due_date:
            if due_date <= issued_date:
                raise ValidationError('Due date must be after issued date.')
            if (due_date - issued_date).days > 30:
                raise ValidationError(
                    'Loan period cannot exceed 30 days.'
                )

        # Check copy is still available
        if book_copy and book_copy.status != 'available':
            raise ValidationError(
                f'Copy [{book_copy.accession_number}] is not available '
                f'(status: {book_copy.get_status_display()}).'
            )

        # Check student/staff doesn't already have same book issued
        if borrower_type == 'student' and student and book_copy:
            active = BookIssuance.objects.filter(
                student=student,
                book_copy__book=book_copy.book,
                status__in=['issued', 'overdue'],
            )
            if self.instance.pk:
                active = active.exclude(pk=self.instance.pk)
            if active.exists():
                raise ValidationError(
                    f'{student.user.get_full_name()} already has '
                    f'"{book_copy.book.title}" issued.'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Return Form
# ─────────────────────────────────────────────

class ReturnBookForm(forms.Form):
    """Quick return — just confirm condition and notes"""
    condition = forms.ChoiceField(
        choices=BookCopy.CONDITION,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Update copy condition on return',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Any notes about the return…',
        })
    )
    mark_lost = forms.BooleanField(
        required=False,
        label='Mark as Lost (cannot be returned)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


# ─────────────────────────────────────────────
#  Fine Form
# ─────────────────────────────────────────────

class FineForm(forms.ModelForm):
    class Meta:
        model  = Fine
        fields = ['fine_per_day']
        widgets = {
            'fine_per_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'step':  '0.50',
                'min':   0,
            }),
        }


class FinePaymentForm(forms.Form):
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Payment notes…',
        })
    )


class FineWaiverForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': 'Reason for waiving the fine…',
        })
    )


# ─────────────────────────────────────────────
#  Reservation Form
# ─────────────────────────────────────────────

class ReservationForm(forms.ModelForm):
    class Meta:
        model  = Reservation
        fields = ['book', 'student', 'expiry_date', 'notes']
        widgets = {
            'book':        forms.Select(attrs={'class': 'form-select'}),
            'student':     forms.Select(attrs={'class': 'form-select'}),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False
        if not self.instance.pk:
            self.fields['expiry_date'].initial = (
                timezone.now().date() + timedelta(days=7)
            )

    def clean(self):
        cleaned     = super().clean()
        book        = cleaned.get('book')
        student     = cleaned.get('student')
        expiry_date = cleaned.get('expiry_date')

        if expiry_date and expiry_date <= timezone.now().date():
            raise ValidationError('Expiry date must be in the future.')

        if book and student:
            # Prevent duplicate active reservation
            dup = Reservation.objects.filter(
                book=book, student=student, status='pending'
            )
            if self.instance.pk:
                dup = dup.exclude(pk=self.instance.pk)
            if dup.exists():
                raise ValidationError(
                    f'{student.user.get_full_name()} already has '
                    f'a pending reservation for "{book.title}".'
                )
        return cleaned


# ─────────────────────────────────────────────
#  Search / Filter Form
# ─────────────────────────────────────────────

class BookSearchForm(forms.Form):
    q        = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Search by title, ISBN, author…',
        })
    )
    category = forms.ModelChoiceField(
        queryset=BookCategory.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    language = forms.ChoiceField(
        required=False,
        choices=[('', 'All Languages')] + Book.LANGUAGE,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    available_only = forms.BooleanField(
        required=False,
        label='Available only',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


class IssuanceFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('issued',   'Issued'),
        ('overdue',  'Overdue'),
        ('returned', 'Returned'),
        ('lost',     'Lost'),
    ]
    status    = forms.ChoiceField(
        choices=STATUS_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    date_to   = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search borrower name or book…',
        }),
    )