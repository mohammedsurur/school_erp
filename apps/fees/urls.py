# apps/fees/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # ── Fee Categories ────────────────────────
    path(
        'categories/',
        views.fee_category_list,
        name='fee_category_list'
    ),
    path(
        'categories/create/',
        views.fee_category_create,
        name='fee_category_create'
    ),
    path(
        'categories/<int:pk>/edit/',
        views.fee_category_edit,
        name='fee_category_edit'
    ),
    path(
        'categories/<int:pk>/delete/',
        views.fee_category_delete,
        name='fee_category_delete'
    ),

    # ── Fee Structures ────────────────────────
    path(
        'structures/',
        views.fee_structure_list,
        name='fee_structure_list'
    ),
    path(
        'structures/create/',
        views.fee_structure_create,
        name='fee_structure_create'
    ),
    path(
        'structures/<int:pk>/edit/',
        views.fee_structure_edit,
        name='fee_structure_edit'
    ),
    path(
        'structures/<int:pk>/delete/',
        views.fee_structure_delete,
        name='fee_structure_delete'
    ),

    # ── Bulk Assign ───────────────────────────
    path(
        'bulk-assign/',
        views.bulk_assign_fees,
        name='bulk_assign_fees'
    ),

    # ── Student Fees ──────────────────────────
    path(
        '',
        views.student_fee_list,
        name='student_fee_list'
    ),
    path(
        '<int:pk>/',
        views.student_fee_detail,
        name='student_fee_detail'
    ),
    path(
        '<int:pk>/waive/',
        views.waive_fee,
        name='waive_fee'
    ),

    # ── Student: my fees ──────────────────────
    path(
        'my/',
        views.my_fees,
        name='my_fees'
    ),

    # ── Reports ───────────────────────────────
    path(
        'report/',
        views.fee_report,
        name='fee_report'
    ),
    path(
        'daily-collection/',
        views.daily_collection,
        name='daily_collection'
    ),
]