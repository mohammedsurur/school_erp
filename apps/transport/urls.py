# apps/transport/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # ── Dashboard ─────────────────────────────
    path(
        '',
        views.transport_dashboard,
        name='transport_dashboard'
    ),

    # ── Vehicles ──────────────────────────────
    path(
        'vehicles/',
        views.vehicle_list,
        name='vehicle_list'
    ),
    path(
        'vehicles/add/',
        views.vehicle_create,
        name='vehicle_create'
    ),
    path(
        'vehicles/<int:pk>/edit/',
        views.vehicle_edit,
        name='vehicle_edit'
    ),
    path(
        'vehicles/<int:pk>/delete/',
        views.vehicle_delete,
        name='vehicle_delete'
    ),

    # ── Routes ────────────────────────────────
    path(
        'routes/',
        views.route_list,
        name='route_list'
    ),
    path(
        'routes/add/',
        views.route_create,
        name='route_create'
    ),
    path(
        'routes/<int:pk>/',
        views.route_detail,
        name='route_detail'
    ),
    path(
        'routes/<int:pk>/edit/',
        views.route_edit,
        name='route_edit'
    ),
    path(
        'routes/<int:pk>/delete/',
        views.route_delete,
        name='route_delete'
    ),

    # ── Route Stops ───────────────────────────
    path(
        'routes/<int:route_pk>/stops/add/',
        views.stop_add,
        name='stop_add'
    ),
    path(
        'stops/<int:pk>/edit/',
        views.stop_edit,
        name='stop_edit'
    ),
    path(
        'stops/<int:pk>/delete/',
        views.stop_delete,
        name='stop_delete'
    ),

    # ── Student Assignments ───────────────────
    path(
        'students/',
        views.student_transport_list,
        name='student_transport_list'
    ),
    path(
        'students/assign/',
        views.student_transport_assign,
        name='student_transport_assign'
    ),
    path(
        'students/<int:pk>/edit/',
        views.student_transport_edit,
        name='student_transport_edit'
    ),
    path(
        'students/<int:pk>/remove/',
        views.student_transport_remove,
        name='student_transport_remove'
    ),

    # ── Attendance ────────────────────────────
    path(
        'routes/<int:route_pk>/attendance/',
        views.attendance_mark,
        name='transport_attendance_mark'
    ),
    path(
        'routes/<int:route_pk>/attendance/report/',
        views.attendance_report,
        name='transport_attendance_report'
    ),

    # ── AJAX ──────────────────────────────────
    path(
        'ajax/stops/',
        views.ajax_route_stops,
        name='ajax_route_stops'
    ),

    # ── Student: my transport ─────────────────
    path(
        'my/',
        views.my_transport,
        name='my_transport'
    ),
]