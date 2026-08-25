from django.urls import path
from . import views

urlpatterns = [

    # ── Student CRUD ─────────────────────────
    path(
        '',
        views.student_list,
        name='student_list'
    ),
    path(
        'create/',
        views.student_create,
        name='student_create'
    ),
    path(
        '<int:pk>/',
        views.student_detail,
        name='student_detail'
    ),
    path(
        '<int:pk>/edit/',
        views.student_edit,
        name='student_edit'
    ),
    path(
        '<int:pk>/toggle-active/',
        views.student_toggle_active,
        name='student_toggle_active'
    ),

    # ── ID Card ───────────────────────────────
    path(
        '<int:pk>/id-card/',
        views.student_id_card,
        name='student_id_card'
    ),

    # ── Parent ────────────────────────────────
    path(
        'parents/',
        views.parent_list,
        name='parent_list'
    ),
    path(
        '<int:student_pk>/add-parent/',
        views.parent_add,
        name='parent_add'
    ),

    # ── Enrollment ───────────────────────────
    path(
        'enrollments/',
        views.enrollment_list,
        name='enrollment_list'
    ),
    path(
        'enrollments/enroll/',
        views.student_enroll,
        name='student_enroll'
    ),
    path(
        '<int:student_pk>/enroll/',
        views.student_enroll,
        name='student_enroll_direct'
    ),
    path(
        'enrollments/<int:pk>/cancel/',
        views.enrollment_cancel,
        name='enrollment_cancel'
    ),

    # ── Bulk Enrollment ───────────────────────
    path(
        'enrollments/bulk/',
        views.bulk_enroll,
        name='bulk_enroll'
    ),

    # ── Promotion ────────────────────────────
    path(
        'promote/',
        views.student_promote,
        name='student_promote'
    ),

    # ── AJAX ─────────────────────────────────
    path(
        'ajax/sections/',
        views.ajax_sections_by_grade,
        name='ajax_sections_by_grade'
    ),
]