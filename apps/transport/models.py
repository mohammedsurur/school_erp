# apps/transport/models.py

from django.db        import models
from django.utils     import timezone
from django.core.validators import MinValueValidator


# ─────────────────────────────────────────────
#  Vehicle
# ─────────────────────────────────────────────

class Vehicle(models.Model):
    VEHICLE_TYPE = [
        ('bus',      'Bus'),
        ('minibus',  'Minibus'),
        ('van',      'Van'),
    ]
    STATUS = [
        ('active',      'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive',    'Inactive'),
    ]

    name            = models.CharField(
        max_length=100,
        help_text='e.g. Bus A, Minibus 1'
    )
    vehicle_type    = models.CharField(
        max_length=10, choices=VEHICLE_TYPE, default='bus'
    )
    plate_number    = models.CharField(
        max_length=20, unique=True,
        help_text='Vehicle licence plate number'
    )
    capacity        = models.PositiveIntegerField(
        default=30,
        help_text='Maximum number of students'
    )
    status          = models.CharField(
        max_length=15, choices=STATUS, default='active'
    )
    driver_name     = models.CharField(max_length=150, blank=True)
    driver_phone    = models.CharField(max_length=20, blank=True)
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.plate_number})"

    @property
    def assigned_students(self):
        return self.route_set.aggregate(
            total=models.Count('student_transports')
        )['total'] or 0


# ─────────────────────────────────────────────
#  Route
# ─────────────────────────────────────────────

class Route(models.Model):
    DIRECTION = [
        ('morning',   'Morning (Home → School)'),
        ('afternoon', 'Afternoon (School → Home)'),
        ('both',      'Both Directions'),
    ]

    name        = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    vehicle     = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='routes'
    )
    direction   = models.CharField(
        max_length=10, choices=DIRECTION, default='both'
    )
    start_point = models.CharField(
        max_length=150, help_text='Starting point / origin'
    )
    end_point   = models.CharField(
        max_length=150, help_text='End point / school'
    )
    departure_time = models.TimeField(
        null=True, blank=True,
        help_text='Morning departure time'
    )
    return_time    = models.TimeField(
        null=True, blank=True,
        help_text='Afternoon return time'
    )
    monthly_fee    = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        help_text='Monthly transport fee in ETB'
    )
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.start_point} → {self.end_point})"

    @property
    def student_count(self):
        return self.student_transports.filter(is_active=True).count()

    @property
    def available_seats(self):
        if self.vehicle:
            return max(0, self.vehicle.capacity - self.student_count)
        return 0


# ─────────────────────────────────────────────
#  RouteStop  (ordered stops along a route)
# ─────────────────────────────────────────────

class RouteStop(models.Model):
    route       = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name='stops'
    )
    stop_name   = models.CharField(max_length=150)
    stop_order  = models.PositiveIntegerField(
        help_text='Order of this stop along the route (1 = first)'
    )
    pickup_time = models.TimeField(
        null=True, blank=True,
        help_text='Expected pickup time at this stop'
    )
    landmark    = models.CharField(
        max_length=200, blank=True,
        help_text='Nearby landmark for identification'
    )

    class Meta:
        unique_together = ('route', 'stop_order')
        ordering        = ['stop_order']

    def __str__(self):
        return f"{self.route.name} — Stop {self.stop_order}: {self.stop_name}"


# ─────────────────────────────────────────────
#  StudentTransport  (student assigned to route)
# ─────────────────────────────────────────────

class StudentTransport(models.Model):
    student     = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='transport_assignments'
    )
    route       = models.ForeignKey(
        Route, on_delete=models.CASCADE,
        related_name='student_transports'
    )
    stop        = models.ForeignKey(
        RouteStop, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='student_transports',
        help_text='Pickup/drop-off stop for this student'
    )
    academic_year = models.ForeignKey(
        'core.AcademicYear', on_delete=models.CASCADE,
        related_name='student_transports'
    )
    start_date  = models.DateField(default=timezone.now)
    end_date    = models.DateField(null=True, blank=True)
    is_active   = models.BooleanField(default=True)
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'route', 'academic_year')
        ordering        = ['route__name', 'student__user__first_name']

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} → "
            f"{self.route.name}"
        )


# ─────────────────────────────────────────────
#  TransportAttendance  (daily trip log)
# ─────────────────────────────────────────────

class TransportAttendance(models.Model):
    STATUS = [
        ('present', 'Present'),
        ('absent',  'Absent'),
    ]
    TRIP = [
        ('morning',   'Morning'),
        ('afternoon', 'Afternoon'),
    ]

    student_transport = models.ForeignKey(
        StudentTransport, on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date        = models.DateField(default=timezone.now)
    trip        = models.CharField(
        max_length=10, choices=TRIP, default='morning'
    )
    status      = models.CharField(
        max_length=10, choices=STATUS, default='present'
    )
    notes       = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        unique_together = ('student_transport', 'date', 'trip')
        ordering        = ['-date', 'trip']

    def __str__(self):
        return (
            f"{self.student_transport.student.user.get_full_name()} — "
            f"{self.date} {self.get_trip_display()} — "
            f"{self.get_status_display()}"
        )