# apps/library/urls.py

from django.urls import path
from . import views

urlpatterns = [

    # ── Dashboard ─────────────────────────────
    path(
        '',
        views.library_dashboard,
        name='library_dashboard'
    ),

    # ── Book Catalog ──────────────────────────
    path(
        'books/',
        views.book_list,
        name='book_list'
    ),
    path(
        'books/add/',
        views.book_create,
        name='book_create'
    ),
    path(
        'books/<int:pk>/',
        views.book_detail,
        name='book_detail'
    ),
    path(
        'books/<int:pk>/edit/',
        views.book_edit,
        name='book_edit'
    ),
    path(
        'books/<int:pk>/delete/',
        views.book_delete,
        name='book_delete'
    ),

    # ── Book Copies ───────────────────────────
    path(
        'books/<int:book_pk>/copies/add/',
        views.copy_add,
        name='copy_add'
    ),
    path(
        'copies/<int:pk>/edit/',
        views.copy_edit,
        name='copy_edit'
    ),
    path(
        'copies/<int:pk>/delete/',
        views.copy_delete,
        name='copy_delete'
    ),

    # ── Issuances ─────────────────────────────
    path(
        'issuances/',
        views.issuance_list,
        name='issuance_list'
    ),
    path(
        'issuances/issue/',
        views.issue_book,
        name='issue_book'
    ),
    path(
        'issuances/<int:pk>/',
        views.issuance_detail,
        name='issuance_detail'
    ),
    path(
        'issuances/<int:pk>/return/',
        views.return_book,
        name='return_book'
    ),

    # ── Fines ─────────────────────────────────
    path(
        'fines/',
        views.fine_list,
        name='fine_list'
    ),
    path(
        'fines/<int:pk>/pay/',
        views.fine_pay,
        name='fine_pay'
    ),
    path(
        'fines/<int:pk>/waive/',
        views.fine_waive,
        name='fine_waive'
    ),

    # ── Reservations ──────────────────────────
    path(
        'reservations/',
        views.reservation_list,
        name='reservation_list'
    ),
    path(
        'reservations/create/',
        views.reservation_create,
        name='reservation_create'
    ),
    path(
        'reservations/<int:pk>/cancel/',
        views.reservation_cancel,
        name='reservation_cancel'
    ),
    path(
        'reservations/<int:pk>/fulfil/',
        views.reservation_fulfil,
        name='reservation_fulfil'
    ),

    # ── Student: My Books ─────────────────────
    path(
        'my-books/',
        views.my_books,
        name='my_books'
    ),

    # ── Categories ───────────────────────────
    path(
        'categories/',
        views.category_list,
        name='library_category_list'
    ),
    path(
        'categories/add/',
        views.category_create,
        name='library_category_create'
    ),
    path(
        'categories/<int:pk>/edit/',
        views.category_edit,
        name='library_category_edit'
    ),

    # ── Authors ───────────────────────────────
    path(
        'authors/',
        views.author_list,
        name='library_author_list'
    ),
    path(
        'authors/add/',
        views.author_create,
        name='library_author_create'
    ),
    path(
        'authors/<int:pk>/edit/',
        views.author_edit,
        name='library_author_edit'
    ),

    # ── Publishers ────────────────────────────
    path(
        'publishers/',
        views.publisher_list,
        name='library_publisher_list'
    ),
    path(
        'publishers/add/',
        views.publisher_create,
        name='library_publisher_create'
    ),
    path(
        'publishers/<int:pk>/edit/',
        views.publisher_edit,
        name='library_publisher_edit'
    ),
]