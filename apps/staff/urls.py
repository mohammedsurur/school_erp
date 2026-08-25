from django.urls import path
from . import views

urlpatterns = [

    # ── Staff CRUD ───────────────────────────
    path(
        '',
        views.staff_list,
        name='staff_list'
    ),
    path(
        'create/',
        views.staff_create,
        name='staff_create'
    ),
    path(
        '<int:pk>/',
        views.staff_detail,
        name='staff_detail'
    ),
    path(
        '<int:pk>/edit/',
        views.staff_edit,
        name='staff_edit'
    ),
    path(
        '<int:pk>/toggle-active/',
        views.staff_toggle_active,
        name='staff_toggle_active'
    ),
]