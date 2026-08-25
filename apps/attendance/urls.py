# apps/attendance/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # ── Mark Attendance ───────────────────────
    path(
        '',
        views.attendance_select,
        name='attendance_select'
    ),
    path(
        'mark/<int:section_pk>/<str:date_str>/',
        views.attendance_mark,
        name='attendance_mark'
    ),

    # ── View Records ──────────────────────────
    path(
        'records/',
        views.attendance_list,
        name='attendance_list'
    ),

    # ── Report ────────────────────────────────
    path(
        'report/',
        views.attendance_report,
        name='attendance_report'
    ),

    # ── Student: my attendance ─────────────────
    path(
        'my/',
        views.my_attendance,
        name='my_attendance'
    ),

    # ── AJAX ──────────────────────────────────
    path(
        'ajax/today-stats/',
        views.ajax_today_stats,
        name='attendance_today_stats'
    ),
]