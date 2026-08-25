from django import forms
from apps.accounts.models import User
from apps.academic.models  import Grade, Section
from apps.core.models      import AcademicYear
from .models               import Student, Parent, Enrollment


# ─────────────────────────────────────────────
#  Student Forms
# ─────────────────────────────────────────────

class StudentUserForm(forms.ModelForm):
    """Step 1 — Creates the login account for the student"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Set a password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat password'})
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'username':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login username'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords don't match.")
        return p2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user          = super().save(commit=False)
        user.role     = 'student'
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    """Step 2 — Student personal details"""

    class Meta:
        model  = Student
        fields = [
            'date_of_birth', 'gender', 'blood_group',
            'nationality', 'religion',
            'address', 'city',
            'previous_school', 'medical_notes', 'photo',
        ]
        widgets = {
            'date_of_birth':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender':          forms.Select(attrs={'class': 'form-select'}),
            'blood_group':     forms.Select(attrs={'class': 'form-select'}),
            'nationality':     forms.TextInput(attrs={'class': 'form-control'}),
            'religion':        forms.TextInput(attrs={'class': 'form-control'}),
            'address':         forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city':            forms.TextInput(attrs={'class': 'form-control'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_notes':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo':           forms.FileInput(attrs={'class': 'form-control'}),
        }


class StudentEditForm(forms.ModelForm):
    """Edit existing student — combines user + student fields"""

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
        model  = Student
        fields = [
            'date_of_birth', 'gender', 'blood_group',
            'nationality', 'religion',
            'address', 'city',
            'previous_school', 'medical_notes', 'photo',
            'is_active',
        ]
        widgets = {
            'date_of_birth':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender':          forms.Select(attrs={'class': 'form-select'}),
            'blood_group':     forms.Select(attrs={'class': 'form-select'}),
            'nationality':     forms.TextInput(attrs={'class': 'form-control'}),
            'religion':        forms.TextInput(attrs={'class': 'form-control'}),
            'address':         forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city':            forms.TextInput(attrs={'class': 'form-control'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_notes':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo':           forms.FileInput(attrs={'class': 'form-control'}),
            'is_active':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial  = self.instance.user.last_name
            self.fields['email'].initial      = self.instance.user.email
            self.fields['phone'].initial      = self.instance.user.phone

    def save(self, commit=True):
        student = super().save(commit=False)
        # also update the linked user
        user            = student.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.phone      = self.cleaned_data['phone']
        if commit:
            user.save()
            student.save()
        return student


# ─────────────────────────────────────────────
#  Parent Form
# ─────────────────────────────────────────────

class ParentForm(forms.ModelForm):
    """Creates parent account linked to student"""
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
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
    password = forms.CharField(
        initial='parent123',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Default password — parent can change later'
    )

    class Meta:
        model  = Parent
        fields = ['relation', 'occupation', 'work_phone', 'annual_income']
        widgets = {
            'relation':      forms.Select(attrs={'class': 'form-select'}),
            'occupation':    forms.TextInput(attrs={'class': 'form-control'}),
            'work_phone':    forms.TextInput(attrs={'class': 'form-control'}),
            'annual_income': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def save(self, student, commit=True):
        # Create parent user account
        user = User.objects.create_user(
            username   = self.cleaned_data['username'],
            first_name = self.cleaned_data['first_name'],
            last_name  = self.cleaned_data['last_name'],
            email      = self.cleaned_data.get('email', ''),
            phone      = self.cleaned_data.get('phone', ''),
            password   = self.cleaned_data['password'],
            role       = 'parent',
        )
        parent = super().save(commit=False)
        parent.user = user
        if commit:
            parent.save()
            parent.student.add(student)
        return parent


# ─────────────────────────────────────────────
#  Enrollment Form
# ─────────────────────────────────────────────

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model  = Enrollment
        fields = ['student', 'section', 'academic_year']
        widgets = {
            'student':       forms.Select(attrs={'class': 'form-select'}),
            'section':       forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active students not yet enrolled in current year
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            enrolled_ids = Enrollment.objects.filter(
                academic_year=current_year, is_active=True
            ).values_list('student_id', flat=True)
            self.fields['student'].queryset = Student.objects.filter(
                is_active=True
            ).exclude(id__in=enrolled_ids)
            self.fields['academic_year'].initial = current_year

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get('student')
        year    = cleaned.get('academic_year')
        if student and year:
            if Enrollment.objects.filter(
                student=student, academic_year=year, is_active=True
            ).exists():
                raise forms.ValidationError(
                    f'{student.user.get_full_name()} is already enrolled in {year}.'
                )
        return cleaned


class BulkEnrollmentForm(forms.Form):
    """Enroll all students of a grade into a section at once"""
    grade         = forms.ModelChoiceField(
        queryset=Grade.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    section       = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            self.fields['academic_year'].initial = current
        if 'grade' in self.data:
            try:
                grade_id = int(self.data.get('grade'))
                self.fields['section'].queryset = Section.objects.filter(grade_id=grade_id)
            except (ValueError, TypeError):
                pass