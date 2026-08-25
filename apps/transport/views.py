# apps/transport/views.py

from django.shortcuts        import render, redirect, get_object_or_404
from django.contrib          import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator   import Paginator
from django.db.models        import Q, Count, Sum
from django.utils            import timezone
from django.http             import JsonResponse

from apps.core.decorators    import admin_required, principal_or_above
from apps.core.models        import AcademicYear
from apps.students.models    import Student
from .models                 import (
    Vehicle, Route, RouteStop,
    StudentTransport, TransportAttendance
)
from .forms                  import (
    VehicleForm, RouteForm, RouteStopForm,
    StudentTransportForm, TransportAttendanceForm,
    RouteFilterForm, StudentTransportFilterForm
)


# ══════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════

@admin_required
def transport_dashboard(request):
    total_vehicles  = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status='active').count()
    total_routes    = Route.objects.filter(is_active=True).count()
    total_students  = StudentTransport.objects.filter(is_active=True).count()

    # Route capacity overview
    routes = Route.objects.filter(is_active=True).select_related(
        'vehicle'
    ).annotate(
        assigned=Count('student_transports',
            filter=Q(student_transports__is_active=True))
    ).order_by('name')

    # Vehicles under maintenance
    maintenance = Vehicle.objects.filter(status='maintenance')

    # Recent assignments
    recent = StudentTransport.objects.select_related(
        'student__user', 'route'
    ).order_by('-created_at')[:8]

    return render(request, 'transport/dashboard.html', {
        'total_vehicles':  total_vehicles,
        'active_vehicles': active_vehicles,
        'total_routes':    total_routes,
        'total_students':  total_students,
        'routes':          routes,
        'maintenance':     maintenance,
        'recent':          recent,
        'page_title':      'Transport Dashboard',
    })


# ══════════════════════════════════════════════
#  VEHICLE CRUD
# ══════════════════════════════════════════════

@admin_required
def vehicle_list(request):
    vehicles = Vehicle.objects.annotate(
        route_count=Count('routes', filter=Q(routes__is_active=True))
    ).order_by('name')
    return render(request, 'transport/vehicle_list.html', {
        'vehicles':   vehicles,
        'page_title': 'Vehicles',
    })


@admin_required
def vehicle_create(request):
    form = VehicleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        v = form.save()
        messages.success(request, f'Vehicle "{v.name}" added.')
        return redirect('vehicle_list')
    return render(request, 'transport/vehicle_form.html', {
        'form':       form,
        'title':      'Add Vehicle',
        'page_title': 'Add Vehicle',
    })


@admin_required
def vehicle_edit(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    form    = VehicleForm(request.POST or None, instance=vehicle)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Vehicle "{vehicle.name}" updated.')
        return redirect('vehicle_list')
    return render(request, 'transport/vehicle_form.html', {
        'form':       form,
        'vehicle':    vehicle,
        'title':      f'Edit — {vehicle.name}',
        'page_title': 'Edit Vehicle',
    })


@admin_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if vehicle.routes.exists():
        messages.error(
            request,
            f'Cannot delete "{vehicle.name}" — it is assigned to routes.'
        )
        return redirect('vehicle_list')
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted.')
        return redirect('vehicle_list')
    return render(request, 'transport/confirm_delete.html', {
        'object':   vehicle,
        'title':    f'Delete — {vehicle.name}',
        'back_url': '/transport/vehicles/',
    })


# ══════════════════════════════════════════════
#  ROUTE CRUD
# ══════════════════════════════════════════════

@admin_required
def route_list(request):
    form   = RouteFilterForm(request.GET or None)
    routes = Route.objects.select_related('vehicle').annotate(
        assigned=Count('student_transports',
            filter=Q(student_transports__is_active=True)),
        stop_count=Count('stops'),
    ).order_by('name')

    if form.is_valid():
        if form.cleaned_data.get('q'):
            routes = routes.filter(
                name__icontains=form.cleaned_data['q']
            )
        if form.cleaned_data.get('vehicle'):
            routes = routes.filter(vehicle=form.cleaned_data['vehicle'])
        if form.cleaned_data.get('is_active') == '1':
            routes = routes.filter(is_active=True)
        elif form.cleaned_data.get('is_active') == '0':
            routes = routes.filter(is_active=False)

    return render(request, 'transport/route_list.html', {
        'routes':     routes,
        'form':       form,
        'page_title': 'Routes',
    })


@admin_required
def route_detail(request, pk):
    route   = get_object_or_404(
        Route.objects.select_related('vehicle'),
        pk=pk
    )
    stops   = route.stops.order_by('stop_order')
    current = AcademicYear.objects.filter(is_current=True).first()
    students = StudentTransport.objects.filter(
        route=route,
        is_active=True,
        academic_year=current,
    ).select_related(
        'student__user', 'stop'
    ).order_by('stop__stop_order', 'student__user__first_name')

    return render(request, 'transport/route_detail.html', {
        'route':      route,
        'stops':      stops,
        'students':   students,
        'page_title': route.name,
    })


@admin_required
def route_create(request):
    form = RouteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        route = form.save()
        messages.success(request, f'Route "{route.name}" created.')
        return redirect('route_detail', pk=route.pk)
    return render(request, 'transport/route_form.html', {
        'form':       form,
        'title':      'Create Route',
        'page_title': 'Create Route',
    })


@admin_required
def route_edit(request, pk):
    route = get_object_or_404(Route, pk=pk)
    form  = RouteForm(request.POST or None, instance=route)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Route "{route.name}" updated.')
        return redirect('route_detail', pk=route.pk)
    return render(request, 'transport/route_form.html', {
        'form':       form,
        'route':      route,
        'title':      f'Edit — {route.name}',
        'page_title': 'Edit Route',
    })


@admin_required
def route_delete(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if route.student_transports.filter(is_active=True).exists():
        messages.error(
            request,
            f'Cannot delete "{route.name}" — '
            f'students are currently assigned to it.'
        )
        return redirect('route_detail', pk=route.pk)
    if request.method == 'POST':
        route.delete()
        messages.success(request, 'Route deleted.')
        return redirect('route_list')
    return render(request, 'transport/confirm_delete.html', {
        'object':   route,
        'title':    f'Delete Route — {route.name}',
        'back_url': f'/transport/routes/{pk}/',
    })


# ══════════════════════════════════════════════
#  ROUTE STOPS
# ══════════════════════════════════════════════

@admin_required
def stop_add(request, route_pk):
    route = get_object_or_404(Route, pk=route_pk)
    form  = RouteStopForm(request.POST or None, route=route)
    if request.method == 'POST' and form.is_valid():
        stop       = form.save(commit=False)
        stop.route = route
        stop.save()
        messages.success(
            request,
            f'Stop "{stop.stop_name}" added to {route.name}.'
        )
        return redirect('route_detail', pk=route.pk)
    return render(request, 'transport/stop_form.html', {
        'form':       form,
        'route':      route,
        'title':      f'Add Stop — {route.name}',
        'page_title': 'Add Route Stop',
    })


@admin_required
def stop_edit(request, pk):
    stop  = get_object_or_404(RouteStop.objects.select_related('route'), pk=pk)
    form  = RouteStopForm(request.POST or None, route=stop.route, instance=stop)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Stop "{stop.stop_name}" updated.')
        return redirect('route_detail', pk=stop.route.pk)
    return render(request, 'transport/stop_form.html', {
        'form':       form,
        'route':      stop.route,
        'stop':       stop,
        'title':      f'Edit Stop — {stop.stop_name}',
        'page_title': 'Edit Stop',
    })


@admin_required
def stop_delete(request, pk):
    stop = get_object_or_404(RouteStop, pk=pk)
    if stop.student_transports.exists():
        messages.error(
            request,
            f'Cannot delete stop "{stop.stop_name}" — '
            f'students are assigned to this stop.'
        )
        return redirect('route_detail', pk=stop.route.pk)
    route_pk = stop.route.pk
    if request.method == 'POST':
        stop.delete()
        messages.success(request, 'Stop deleted.')
        return redirect('route_detail', pk=route_pk)
    return render(request, 'transport/confirm_delete.html', {
        'object':   stop,
        'title':    f'Delete Stop — {stop.stop_name}',
        'back_url': f'/transport/routes/{route_pk}/',
    })


# ══════════════════════════════════════════════
#  STUDENT TRANSPORT ASSIGNMENTS
# ══════════════════════════════════════════════

@admin_required
def student_transport_list(request):
    form        = StudentTransportFilterForm(request.GET or None)
    assignments = StudentTransport.objects.select_related(
        'student__user', 'route', 'stop', 'academic_year'
    ).filter(is_active=True).order_by(
        'route__name', 'student__user__first_name'
    )

    if form.is_valid():
        if form.cleaned_data.get('route'):
            assignments = assignments.filter(route=form.cleaned_data['route'])
        if form.cleaned_data.get('academic_year'):
            assignments = assignments.filter(
                academic_year=form.cleaned_data['academic_year']
            )
        else:
            current = AcademicYear.objects.filter(is_current=True).first()
            if current:
                assignments = assignments.filter(academic_year=current)
        if form.cleaned_data.get('q'):
            assignments = assignments.filter(
                Q(student__user__first_name__icontains=form.cleaned_data['q']) |
                Q(student__user__last_name__icontains=form.cleaned_data['q'])  |
                Q(student__admission_number__icontains=form.cleaned_data['q'])
            )
    else:
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            assignments = assignments.filter(academic_year=current)

    paginator   = Paginator(assignments, 25)
    page        = request.GET.get('page', 1)
    assignments = paginator.get_page(page)

    return render(request, 'transport/student_transport_list.html', {
        'assignments': assignments,
        'form':        form,
        'page_title':  'Student Transport',
    })


@admin_required
def student_transport_assign(request):
    form = StudentTransportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        assignment = form.save()
        messages.success(
            request,
            f'{assignment.student.user.get_full_name()} assigned to '
            f'"{assignment.route.name}".'
        )
        return redirect('student_transport_list')
    return render(request, 'transport/student_transport_form.html', {
        'form':       form,
        'title':      'Assign Student to Route',
        'page_title': 'Assign Student',
    })


@admin_required
def student_transport_edit(request, pk):
    assignment = get_object_or_404(StudentTransport, pk=pk)
    form       = StudentTransportForm(
        request.POST or None, instance=assignment
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Assignment updated.')
        return redirect('student_transport_list')
    return render(request, 'transport/student_transport_form.html', {
        'form':        form,
        'assignment':  assignment,
        'title':       'Edit Assignment',
        'page_title':  'Edit Transport Assignment',
    })


@admin_required
def student_transport_remove(request, pk):
    assignment = get_object_or_404(StudentTransport, pk=pk)
    if request.method == 'POST':
        assignment.is_active = False
        assignment.end_date  = timezone.now().date()
        assignment.save()
        messages.success(
            request,
            f'{assignment.student.user.get_full_name()} removed from '
            f'"{assignment.route.name}".'
        )
        return redirect('student_transport_list')
    return render(request, 'transport/confirm_delete.html', {
        'object':    assignment,
        'title':     f'Remove — {assignment.student.user.get_full_name()}',
        'back_url':  '/transport/students/',
        'btn_label': 'Yes, Remove',
        'btn_class': 'btn-warning',
    })


# ══════════════════════════════════════════════
#  TRANSPORT ATTENDANCE
# ══════════════════════════════════════════════

@admin_required
def attendance_mark(request, route_pk):
    route = get_object_or_404(Route, pk=route_pk)
    form  = TransportAttendanceForm(request.POST or None)
    current = AcademicYear.objects.filter(is_current=True).first()

    students = StudentTransport.objects.filter(
        route=route,
        is_active=True,
        academic_year=current,
    ).select_related('student__user', 'stop')

    if request.method == 'POST' and form.is_valid():
        date = form.cleaned_data['date']
        trip = form.cleaned_data['trip']
        saved = 0

        for st in students:
            status = request.POST.get(f'status_{st.pk}', 'absent')
            TransportAttendance.objects.update_or_create(
                student_transport=st,
                date=date,
                trip=trip,
                defaults={
                    'status':      status,
                    'recorded_by': request.user,
                }
            )
            saved += 1

        messages.success(
            request,
            f'Attendance saved for {saved} students on '
            f'{route.name} — {date} ({trip}).'
        )
        return redirect('transport_dashboard')

    # Pre-load existing attendance
    existing = {}
    if form.is_valid() or request.method == 'GET':
        today = timezone.now().date()
        recs  = TransportAttendance.objects.filter(
            student_transport__route=route,
            date=today,
            trip='morning',
        )
        existing = {r.student_transport_id: r.status for r in recs}

    return render(request, 'transport/attendance_mark.html', {
        'route':      route,
        'form':       form,
        'students':   students,
        'existing':   existing,
        'page_title': f'Attendance — {route.name}',
    })


@admin_required
def attendance_report(request, route_pk):
    route   = get_object_or_404(Route, pk=route_pk)
    current = AcademicYear.objects.filter(is_current=True).first()

    records = TransportAttendance.objects.filter(
        student_transport__route=route,
    ).select_related(
        'student_transport__student__user'
    ).order_by('-date', 'trip')

    paginator = Paginator(records, 30)
    page      = request.GET.get('page', 1)
    records   = paginator.get_page(page)

    return render(request, 'transport/attendance_report.html', {
        'route':      route,
        'records':    records,
        'page_title': f'Attendance Report — {route.name}',
    })


# ══════════════════════════════════════════════
#  AJAX: Get stops for a route
# ══════════════════════════════════════════════

def ajax_route_stops(request):
    route_id = request.GET.get('route_id')
    if not route_id:
        return JsonResponse({'stops': []})
    stops = RouteStop.objects.filter(
        route_id=route_id
    ).order_by('stop_order').values('id', 'stop_name', 'stop_order')
    return JsonResponse({'stops': list(stops)})


# ══════════════════════════════════════════════
#  STUDENT: my transport
# ══════════════════════════════════════════════

@login_required
def my_transport(request):
    try:
        student = request.user.student
    except Exception:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    current = AcademicYear.objects.filter(is_current=True).first()
    assignment = StudentTransport.objects.filter(
        student=student,
        is_active=True,
        academic_year=current,
    ).select_related('route__vehicle', 'stop').first()

    return render(request, 'transport/my_transport.html', {
        'student':    student,
        'assignment': assignment,
        'page_title': 'My Transport',
    })