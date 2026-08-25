from django import forms
from .models import School, AcademicYear, Term


class SchoolForm(forms.ModelForm):
    class Meta:
        model  = School
        fields = [
            'name', 'logo', 'address', 'phone',
            'email', 'website', 'motto', 'established',
        ]
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School full name'}),
            'address':     forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+251...'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control'}),
            'website':     forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'motto':       forms.TextInput(attrs={'class': 'form-control'}),
            'established': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'logo':        forms.FileInput(attrs={'class': 'form-control'}),
        }


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model  = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'name':       forms.TextInput(attrs={
                              'class': 'form-control',
                              'placeholder': 'e.g. 2024-2025'
                          }),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        start   = cleaned.get('start_date')
        end     = cleaned.get('end_date')
        if start and end and end <= start:
            raise forms.ValidationError('End date must be after start date.')
        return cleaned


class TermForm(forms.ModelForm):
    class Meta:
        model  = Term
        fields = ['academic_year', 'name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'name':          forms.Select(attrs={'class': 'form-select'}),
            'start_date':    forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':      forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current':    forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        start   = cleaned.get('start_date')
        end     = cleaned.get('end_date')
        if start and end and end <= start:
            raise forms.ValidationError('End date must be after start date.')
        return cleaned