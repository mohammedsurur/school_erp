# apps/library/admin.py

from django.contrib  import admin
from django.utils.html import format_html
from .models         import (
    BookCategory, Author, Publisher, Book,
    BookCopy, BookIssuance, Fine, Reservation
)


@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'book_count', 'created_at']
    search_fields = ['name']

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'book_count']
    search_fields = ['first_name', 'last_name']

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display  = ['name', 'book_count']
    search_fields = ['name']

    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


class BookCopyInline(admin.TabularInline):
    model  = BookCopy
    extra  = 0
    fields = ['accession_number', 'condition', 'status', 'acquired_date']
    show_change_link = True


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display  = [
        'title', 'isbn', 'category', 'language',
        'total_copies', 'available_copies', 'is_available'
    ]
    list_filter   = ['category', 'language', 'publisher']
    search_fields = ['title', 'isbn', 'authors__first_name', 'authors__last_name']
    filter_horizontal = ['authors']
    inlines       = [BookCopyInline]
    readonly_fields = ['total_copies', 'available_copies']

    def is_available(self, obj):
        if obj.is_available:
            return format_html('<span style="color:green">✅ Yes</span>')
        return format_html('<span style="color:red">❌ No</span>')
    is_available.short_description = 'Available'


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display  = [
        'accession_number', 'book', 'condition',
        'status', 'acquired_date'
    ]
    list_filter   = ['status', 'condition']
    search_fields = ['accession_number', 'book__title']


@admin.register(BookIssuance)
class BookIssuanceAdmin(admin.ModelAdmin):
    list_display  = [
        'book_copy', 'borrower_type', 'borrower',
        'issued_date', 'due_date', 'returned_date',
        'status', 'is_overdue_display'
    ]
    list_filter   = ['status', 'borrower_type', 'issued_date']
    search_fields = [
        'book_copy__book__title',
        'student__user__first_name',
        'student__user__last_name',
        'staff__user__first_name',
        'book_copy__accession_number',
    ]
    readonly_fields = ['created_at']
    date_hierarchy  = 'issued_date'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html(
                '<span style="color:red">⚠ {} days</span>',
                obj.days_overdue
            )
        return '—'
    is_overdue_display.short_description = 'Overdue'


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display  = [
        'issuance', 'days_overdue', 'fine_per_day',
        'total_amount', 'status', 'paid_date', 'collected_by'
    ]
    list_filter   = ['status']
    search_fields = [
        'issuance__book_copy__book__title',
        'issuance__student__user__first_name',
    ]
    readonly_fields = ['created_at', 'updated_at']
    actions         = ['recompute_fines']

    def recompute_fines(self, request, queryset):
        for fine in queryset:
            fine.compute()
        self.message_user(request, f'{queryset.count()} fine(s) recomputed.')
    recompute_fines.short_description = 'Recompute selected fines'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'book', 'reserved_date',
        'expiry_date', 'status', 'is_expired_display'
    ]
    list_filter   = ['status']
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'book__title',
    ]

    def is_expired_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color:orange">Expired</span>')
        return '—'
    is_expired_display.short_description = 'Expired?'