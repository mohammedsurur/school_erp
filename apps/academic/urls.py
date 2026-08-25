from django.urls import path
from . import views

urlpatterns = [

    # ══════════════════════════════════════════
    #  GRADE
    # ══════════════════════════════════════════
    path(
        'grades/',
        views.grade_list,
        name='grade_list'
    ),
    path(
        'grades/create/',
        views.grade_create,
        name='grade_create'
    ),
    path(
        'grades/<int:pk>/edit/',
        views.grade_edit,
        name='grade_edit'
    ),
    path(
        'grades/<int:pk>/delete/',
        views.grade_delete,
        name='grade_delete'
    ),

    # ══════════════════════════════════════════
    #  SECTION
    # ══════════════════════════════════════════
    path(
        'sections/',
        views.section_list,
        name='section_list'
    ),
    path(
        'sections/create/',
        views.section_create,
        name='section_create'
    ),
    path(
        'sections/<int:pk>/edit/',
        views.section_edit,
        name='section_edit'
    ),
    path(
        'sections/<int:pk>/delete/',
        views.section_delete,
        name='section_delete'
    ),

    # ══════════════════════════════════════════
    #  SUBJECT
    # ══════════════════════════════════════════
    path(
        'subjects/',
        views.subject_list,
        name='subject_list'
    ),
    path(
        'subjects/create/',
        views.subject_create,
        name='subject_create'
    ),
    path(
        'subjects/<int:pk>/edit/',
        views.subject_edit,
        name='subject_edit'
    ),
    path(
        'subjects/<int:pk>/delete/',
        views.subject_delete,
        name='subject_delete'
    ),

    # ══════════════════════════════════════════
    #  SUBJECT–TEACHER ASSIGNMENT
    # ══════════════════════════════════════════
    path(
        'subject-teachers/',
        views.subject_teacher_list,
        name='subject_teacher_list'
    ),
    path(
        'subject-teachers/assign/',
        views.subject_teacher_assign,
        name='subject_teacher_assign'
    ),
    path(
        'subject-teachers/<int:pk>/edit/',
        views.subject_teacher_edit,
        name='subject_teacher_edit'
    ),
    path(
        'subject-teachers/<int:pk>/delete/',
        views.subject_teacher_delete,
        name='subject_teacher_delete'
    ),

    # ══════════════════════════════════════════
    #  PERIOD
    # ══════════════════════════════════════════
    path(
        'periods/',
        views.period_list,
        name='period_list'
    ),
    path(
        'periods/create/',
        views.period_create,
        name='period_create'
    ),
    path(
        'periods/<int:pk>/edit/',
        views.period_edit,
        name='period_edit'
    ),
    path(
        'periods/<int:pk>/delete/',
        views.period_delete,
        name='period_delete'
    ),

    # ══════════════════════════════════════════
    #  TIMETABLE
    # ══════════════════════════════════════════
    path(
        'timetable/',
        views.timetable_view,
        name='timetable_view'
    ),
    path(
        'timetable/entry/create/',
        views.timetable_entry_create,
        name='timetable_entry_create'
    ),
    path(
        'timetable/entry/<int:pk>/delete/',
        views.timetable_entry_delete,
        name='timetable_entry_delete'
    ),

    # ══════════════════════════════════════════
    #  AJAX
    # ══════════════════════════════════════════
    path(
        'ajax/subjects/',
        views.ajax_subjects_by_grade,
        name='ajax_subjects_by_grade'
    ),
    path(
        'ajax/sections/',
        views.ajax_sections_by_grade,
        name='ajax_sections_by_grade'
    ),
]