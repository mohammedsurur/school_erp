# apps/transport/admin.py

from django.contrib    import admin
from django.utils.html import format_html
from .models           import (
    Vehicle, Route, RouteStop,
    StudentTransport, TransportAttendance
)


# ─────────────────────────────────────────────
#  Inline: RouteStop inside Route
# ─────────────────────────────────────────────

class RouteStopInline(admin.TabularInline):
    model   = RouteStop
    extra   = 0
    fields  = ['stop_order', 'stop_name', 'pickup_time', 'landmark']
    ordering= ['stop_order']


# ─────────────────────────────────────────────
#  Inline: StudentTransport inside Route
# ─────────────────────────────────────────────

class StudentTransportInline(admin.TabularInline):
    model         = StudentTransport
    extra         = 0
    fields        = ['student', 'stop', 'academic_year', 'is_active']
    raw_id_fields = ['student']
    show_change_link = True


# ─────────────────────────────────────────────
#  Vehicle Admin
# ─────────────────────────────────────────────

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display  = [
        'name', 'vehicle_type', 'plate_number',
        'capacity', 'driver_name', 'driver_phone',
        'status', 'route_count'
    ]
    list_filter   = ['status', 'vehicle_type']
    search_fields = ['name', 'plate_number', 'driver_name']
    ordering      = ['name']

    def route_count(self, obj):
        return obj.routes.filter(is_active=True).count()
    route_count.short_description = 'Active Routes'


# ─────────────────────────────────────────────
#  Route Admin
# ─────────────────────────────────────────────

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display  = [
        'name', 'vehicle', 'direction',
        'start_point', 'end_point',
        'departure_time', 'monthly_fee',
        'student_count', 'available_seats_display',
        'is_active'
    ]
    list_filter   = ['is_active', 'direction', 'vehicle']
    search_fields = ['name', 'start_point', 'end_point']
    ordering      = ['name']
    inlines       = [RouteStopInline, StudentTransportInline]
    actions       = ['activate_routes', 'deactivate_routes']

    def available_seats_display(self, obj):
        seats = obj.available_seats
        colour = 'green' if seats > 5 else 'orange' if seats > 0 else 'red'
        return format_html(
            '<span style="color:{};font-weight:700">{}</span>',
            colour, seats
        )
    available_seats_display.short_description = 'Free Seats'

    def activate_routes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} route(s) activated.')
    activate_routes.short_description = 'Activate selected routes'

    def deactivate_routes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} route(s) deactivated.')
    deactivate_routes.short_description = 'Deactivate selected routes'


# ─────────────────────────────────────────────
#  RouteStop Admin
# ─────────────────────────────────────────────

@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display  = [
        'route', 'stop_order', 'stop_name',
        'pickup_time', 'landmark', 'student_count'
    ]
    list_filter   = ['route']
    search_fields = ['stop_name', 'route__name', 'landmark']
    ordering      = ['route', 'stop_order']

    def student_count(self, obj):
        return obj.student_transports.filter(is_active=True).count()
    student_count.short_description = 'Students'


# ─────────────────────────────────────────────
#  StudentTransport Admin
# ─────────────────────────────────────────────

@admin.register(StudentTransport)
class StudentTransportAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'route', 'stop',
        'academic_year', 'start_date',
        'end_date', 'is_active'
    ]
    list_filter   = [
        'is_active', 'route', 'academic_year'
    ]
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__admission_number',
        'route__name',
    ]
    raw_id_fields = ['student']
    ordering      = ['route__name', 'student__user__first_name']
    date_hierarchy = 'start_date'
    actions        = ['deactivate_assignments']

    def deactivate_assignments(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            is_active=False,
            end_date=timezone.now().date()
        )
        self.message_user(request, f'{updated} assignment(s) deactivated.')
    deactivate_assignments.short_description = 'Deactivate selected assignments'


# ─────────────────────────────────────────────
#  TransportAttendance Admin
# ─────────────────────────────────────────────

@admin.register(TransportAttendance)
class TransportAttendanceAdmin(admin.ModelAdmin):
    list_display  = [
        'student_name', 'route_name',
        'date', 'trip', 'status', 'recorded_by'
    ]
    list_filter   = [
        'status', 'trip', 'date',
        'student_transport__route'
    ]
    search_fields = [
        'student_transport__student__user__first_name',
        'student_transport__student__user__last_name',
        'student_transport__route__name',
    ]
    date_hierarchy = 'date'
    ordering       = ['-date', 'trip']

    def student_name(self, obj):
        return obj.student_transport.student.user.get_full_name()
    student_name.short_description = 'Student'

    def route_name(self, obj):
        return obj.student_transport.route.name
    route_name.short_description = 'Route'