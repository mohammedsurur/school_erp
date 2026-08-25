# apps/exams/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # ── Exams ─────────────────────────────────
    path(
        '',
        views.exam_list,
        name='exam_list'
    ),
    path(
        'create/',
        views.exam_create,
        name='exam_create'
    ),
    path(
        '<int:pk>/',
        views.exam_detail,
        name='exam_detail'
    ),
    path(
        '<int:pk>/edit/',
        views.exam_edit,
        name='exam_edit'
    ),
    path(
        '<int:pk>/delete/',
        views.exam_delete,
        name='exam_delete'
    ),
    path(
        '<int:pk>/publish/',
        views.exam_publish_toggle,
        name='exam_publish_toggle'
    ),

    # ── Schedules ─────────────────────────────
    path(
        '<int:exam_pk>/schedule/add/',
        views.schedule_create,
        name='schedule_create'
    ),
    path(
        'schedule/<int:pk>/delete/',
        views.schedule_delete,
        name='schedule_delete'
    ),

    # ── Components ────────────────────────────
    path(
        'schedule/<int:schedule_pk>/components/',
        views.component_list,
        name='component_list'
    ),
    path(
        'schedule/<int:schedule_pk>/components/add/',
        views.component_add,
        name='component_add'
    ),
    path(
        'component/<int:pk>/delete/',
        views.component_delete,
        name='component_delete'
    ),

    # ── Results ───────────────────────────────
    path(
        'schedule/<int:schedule_pk>/enter/',
        views.result_entry,
        name='result_entry'
    ),
    path(
        'schedule/<int:schedule_pk>/results/',
        views.result_list,
        name='result_list'
    ),

    # ── Report Cards ──────────────────────────
    path(
        '<int:exam_pk>/report-cards/',
        views.report_card_list,
        name='report_card_list'
    ),
    path(
        'report-card/<int:pk>/',
        views.report_card_detail,
        name='report_card_detail'
    ),

    # ── Student ───────────────────────────────
    path(
        'my-results/',
        views.my_results,
        name='my_results'
    ),
]