from django import forms
from apps.accounts.models import User
from .models import Staff


# ─────────────────────────────────────────────
#  Step 1 — Staff Login Account
# ─────────────────────────────────────────────

class StaffUserForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Set a password'
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repeat password'
        })
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'username':   forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control'}),
            'role':       forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff-related roles
        self.fields['role'].choices = [
            ('teacher',    'Teacher'),
            ('admin_staff','Admin Staff'),
            ('librarian',  'Librarian'),
            ('accountant', 'Accountant'),
            ('principal',  'Principal'),
        ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
#  Step 2 — Staff Professional Profile
# ─────────────────────────────────────────────

class StaffProfileForm(forms.ModelForm):
    class Meta:
        model  = Staff
        fields = [
            'staff_type', 'department', 'qualification',
            'specialization', 'experience_years',
            'join_date', 'salary',
            'bank_name', 'bank_account',
            'emergency_contact_name', 'emergency_contact_phone',
            'photo',
        ]
        widgets = {
            'staff_type':               forms.Select(attrs={'class': 'form-select'}),
            'department':               forms.TextInput(attrs={'class': 'form-control'}),
            'qualification':            forms.Select(attrs={'class': 'form-select'}),
            'specialization':           forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years':         forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'join_date':                forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary':                   forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bank_name':                forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account':             forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone':  forms.TextInput(attrs={'class': 'form-control'}),
            'photo':                    forms.FileInput(attrs={'class': 'form-control'}),
        }


# ─────────────────────────────────────────────
#  Edit Staff — combined user + staff fields
# ─────────────────────────────────────────────

class StaffEditForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model  = Staff
        fields = [
            'staff_type', 'department', 'qualification',
            'specialization', 'experience_years',
            'join_date', 'salary',
            'bank_name', 'bank_account',
            'emergency_contact_name', 'emergency_contact_phone',
            'photo', 'is_active',
        ]
        widgets = {
            'staff_type':               forms.Select(attrs={'class': 'form-select'}),
            'department':               forms.TextInput(attrs={'class': 'form-control'}),
            'qualification':            forms.Select(attrs={'class': 'form-select'}),
            'specialization':           forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years':         forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'join_date':                forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary':                   forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bank_name':                forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account':             forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name':   forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone':  forms.TextInput(attrs={'class': 'form-control'}),
            'photo':                    forms.FileInput(attrs={'class': 'form-control'}),
            'is_active':                forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial  = self.instance.user.last_name
            self.fields['email'].initial      = self.instance.user.email
            self.fields['phone'].initial      = self.instance.user.phone

    def save(self, commit=True):
        staff = super().save(commit=False)
        user  = staff.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.phone      = self.cleaned_data['phone']
        user.is_active  = self.cleaned_data['is_active']
        if commit:
            user.save()
            staff.save()
        return staff