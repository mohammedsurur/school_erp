from django.urls import path
from . import views

urlpatterns = [

    # ── Dashboards ──────────────────────────────
    path('',                views.dashboard_redirect, name='dashboard'),
    path('admin/',          views.admin_dashboard,    name='admin_dashboard'),
    path('principal/',      views.admin_dashboard,    name='principal_dashboard'),
    path('teacher/',        views.teacher_dashboard,  name='teacher_dashboard'),
    path('student/',        views.student_dashboard,  name='student_dashboard'),
    path('parent/',         views.parent_dashboard,   name='parent_dashboard'),
    path('accountant/',     views.admin_dashboard,    name='accountant_dashboard'),
    path('librarian/',      views.admin_dashboard,    name='librarian_dashboard'),

    # ── School Setup ────────────────────────────
    path('school/setup/',   views.school_setup,       name='school_setup'),

    # ── Academic Year ───────────────────────────
    path('academic-years/',
         views.academic_year_list,           name='academic_year_list'),
    path('academic-years/create/',
         views.academic_year_create,         name='academic_year_create'),
    path('academic-years/<int:pk>/edit/',
         views.academic_year_edit,           name='academic_year_edit'),
    path('academic-years/<int:pk>/set-current/',
         views.academic_year_set_current,    name='academic_year_set_current'),
    path('academic-years/<int:pk>/delete/',
         views.academic_year_delete,         name='academic_year_delete'),

    # ── Term ────────────────────────────────────
    path('terms/', views.term_list, name='term_list'),
    path('terms/create/',views.term_create, name='term_create'),
    path('terms/<int:pk>/edit/', views.term_edit, name='term_edit'),
    path('terms/<int:pk>/set-current/', views.term_set_current, name='term_set_current'),
    path('terms/<int:pk>/delete/', views.term_delete, name='term_delete'),
    # ── Audit Log ───────────────────────────────
    path('audit-log/',      views.audit_log_list,     name='audit_log'),
]