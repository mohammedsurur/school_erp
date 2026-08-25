# apps/transport/forms.py

from django                  import forms
from django.core.exceptions  import ValidationError
from django.utils            import timezone

from apps.core.models        import AcademicYear
from apps.students.models    import Student
from .models                 import (
    Vehicle, Route, RouteStop,
    StudentTransport, TransportAttendance
)


# ─────────────────────────────────────────────
#  Vehicle Form
# ─────────────────────────────────────────────

class VehicleForm(forms.ModelForm):
    class Meta:
        model  = Vehicle
        fields = [
            'name', 'vehicle_type', 'plate_number',
            'capacity', 'status', 'driver_name',
            'driver_phone', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. School Bus A',
            }),
            'vehicle_type':  forms.Select(attrs={'class': 'form-select'}),
            'plate_number':  forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. AA-12345',
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 100,
            }),
            'status':       forms.Select(attrs={'class': 'form-select'}),
            'driver_name':  forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Driver full name',
            }),
            'driver_phone': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. +251 91 234 5678',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ['driver_name', 'driver_phone', 'notes']:
            self.fields[f].required = False

    def clean_plate_number(self):
        plate = self.cleaned_data.get('plate_number', '').strip().upper()
        qs    = Vehicle.objects.filter(plate_number=plate)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(
                f'A vehicle with plate number "{plate}" already exists.'
            )
        return plate


# ─────────────────────────────────────────────
#  Route Form
# ─────────────────────────────────────────────

class RouteForm(forms.ModelForm):
    class Meta:
        model  = Route
        fields = [
            'name', 'description', 'vehicle', 'direction',
            'start_point', 'end_point',
            'departure_time', 'return_time',
            'monthly_fee', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Route A — Bole',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
            'vehicle':    forms.Select(attrs={'class': 'form-select'}),
            'direction':  forms.Select(attrs={'class': 'form-select'}),
            'start_point': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Bole Medhanialem',
            }),
            'end_point': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. School Gate',
            }),
            'departure_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time',
            }),
            'return_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time',
            }),
            'monthly_fee': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': 0,
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in [
            'description', 'vehicle', 'departure_time',
            'return_time', 'description'
        ]:
            self.fields[f].required = False

        # Only active vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            status='active'
        ).order_by('name')


# ─────────────────────────────────────────────
#  Route Stop Form
# ─────────────────────────────────────────────

class RouteStopForm(forms.ModelForm):
    class Meta:
        model  = RouteStop
        fields = ['stop_name', 'stop_order', 'pickup_time', 'landmark']
        widgets = {
            'stop_name': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Bole Atlas',
            }),
            'stop_order': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1,
            }),
            'pickup_time': forms.TimeInput(attrs={
                'class': 'form-control', 'type': 'time',
            }),
            'landmark': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Near Total petrol station',
            }),
        }

    def __init__(self, *args, route=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.route = route
        self.fields['pickup_time'].required = False
        self.fields['landmark'].required    = False

    def clean_stop_order(self):
        order = self.cleaned_data.get('stop_order')
        if self.route and order:
            qs = RouteStop.objects.filter(
                route=self.route, stop_order=order
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'Stop order {order} already exists on this route.'
                )
        return order


# ─────────────────────────────────────────────
#  Student Transport Assignment Form
# ─────────────────────────────────────────────

class StudentTransportForm(forms.ModelForm):
    class Meta:
        model  = StudentTransport
        fields = [
            'student', 'route', 'stop',
            'academic_year', 'start_date', 'notes',
        ]
        widgets = {
            'student':      forms.Select(attrs={'class': 'form-select'}),
            'route':        forms.Select(attrs={'class': 'form-select'}),
            'stop':         forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control', 'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stop'].required  = False
        self.fields['notes'].required = False

        # Default to current year
        current = AcademicYear.objects.filter(is_current=True).first()
        if current and not self.instance.pk:
            self.fields['academic_year'].initial = current

        # Limit stop choices to selected route
        if self.data.get('route'):
            self.fields['stop'].queryset = RouteStop.objects.filter(
                route_id=self.data['route']
            ).order_by('stop_order')
        elif self.instance.pk and self.instance.route_id:
            self.fields['stop'].queryset = RouteStop.objects.filter(
                route=self.instance.route
            ).order_by('stop_order')
        else:
            self.fields['stop'].queryset = RouteStop.objects.none()

        # Only active routes
        self.fields['route'].queryset = Route.objects.filter(
            is_active=True
        ).order_by('name')

    def clean(self):
        cleaned       = super().clean()
        student       = cleaned.get('student')
        route         = cleaned.get('route')
        academic_year = cleaned.get('academic_year')

        if student and route and academic_year:
            # Check duplicate assignment
            qs = StudentTransport.objects.filter(
                student=student,
                route=route,
                academic_year=academic_year,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'{student.user.get_full_name()} is already '
                    f'assigned to "{route.name}" for this year.'
                )

            # Check vehicle capacity
            if route.vehicle:
                current_count = route.student_transports.filter(
                    is_active=True
                ).count()
                if not self.instance.pk:
                    if current_count >= route.vehicle.capacity:
                        raise ValidationError(
                            f'Route "{route.name}" is full. '
                            f'Vehicle capacity: {route.vehicle.capacity} students.'
                        )
        return cleaned


# ─────────────────────────────────────────────
#  Transport Attendance Form
# ─────────────────────────────────────────────

class TransportAttendanceForm(forms.Form):
    """Bulk attendance for all students on a route for a date/trip"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
        }),
        initial=timezone.now
    )
    trip = forms.ChoiceField(
        choices=TransportAttendance.TRIP,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > timezone.now().date():
            raise ValidationError('Date cannot be in the future.')
        return date


# ─────────────────────────────────────────────
#  Filter Forms
# ─────────────────────────────────────────────

class RouteFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Search route name…',
        })
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.filter(status='active'),
        required=False,
        empty_label='All Vehicles',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('1', 'Active'), ('0', 'Inactive')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class StudentTransportFilterForm(forms.Form):
    route = forms.ModelChoiceField(
        queryset=Route.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label='All Routes',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.order_by('-start_date'),
        required=False,
        empty_label='All Years',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'Search student name…',
        })
    )