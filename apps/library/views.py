# apps/library/views.py

from django.shortcuts        import render, redirect, get_object_or_404
from django.contrib          import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator   import Paginator
from django.db.models        import Q, Count, Sum
from django.utils            import timezone
from datetime                import timedelta

from apps.core.decorators    import librarian_required, admin_required
from .models                 import (
    BookCategory, Author, Publisher, Book,
    BookCopy, BookIssuance, Fine, Reservation
)
from .forms                  import (
    BookCategoryForm, AuthorForm, PublisherForm,
    BookForm, BookCopyForm, BookIssuanceForm,
    ReturnBookForm, FinePaymentForm, FineWaiverForm,
    ReservationForm, BookSearchForm, IssuanceFilterForm
)


# ══════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════

@librarian_required
def library_dashboard(request):
    today = timezone.now().date()

    total_books       = Book.objects.count()
    total_copies      = BookCopy.objects.count()
    available_copies  = BookCopy.objects.filter(status='available').count()
    issued_count      = BookIssuance.objects.filter(
        status__in=['issued', 'overdue']
    ).count()
    overdue_count     = BookIssuance.objects.filter(
        status__in=['issued', 'overdue'],
        due_date__lt=today
    ).count()
    pending_fines     = Fine.objects.filter(
        status='pending'
    ).aggregate(s=Sum('total_amount'))['s'] or 0
    reservations      = Reservation.objects.filter(
        status='pending'
    ).count()

    # Recent issuances
    recent_issuances = BookIssuance.objects.select_related(
        'book_copy__book', 'student__user', 'staff__user'
    ).order_by('-created_at')[:8]

    # Overdue list
    overdue = BookIssuance.objects.filter(
        status__in=['issued', 'overdue'],
        due_date__lt=today
    ).select_related(
        'book_copy__book', 'student__user', 'staff__user'
    ).order_by('due_date')[:8]

    # Most borrowed books
    popular = Book.objects.annotate(
        borrow_count=Count('copies__issuances')
    ).order_by('-borrow_count')[:5]

    # Auto-mark overdue
    BookIssuance.objects.filter(
        status='issued', due_date__lt=today
    ).update(status='overdue')

    return render(request, 'library/dashboard.html', {
        'total_books':      total_books,
        'total_copies':     total_copies,
        'available_copies': available_copies,
        'issued_count':     issued_count,
        'overdue_count':    overdue_count,
        'pending_fines':    pending_fines,
        'reservations':     reservations,
        'recent_issuances': recent_issuances,
        'overdue':          overdue,
        'popular':          popular,
        'page_title':       'Library Dashboard',
    })


# ══════════════════════════════════════════════
#  BOOK CATALOG
# ══════════════════════════════════════════════

@login_required
def book_list(request):
    form  = BookSearchForm(request.GET or None)
    books = Book.objects.select_related(
        'category', 'publisher'
    ).prefetch_related('authors').annotate(
        issued_count=Count('copies__issuances',
            filter=Q(copies__issuances__status__in=['issued', 'overdue']))
    ).order_by('title')

    if form.is_valid():
        q = form.cleaned_data.get('q', '').strip()
        if q:
            books = books.filter(
                Q(title__icontains=q)        |
                Q(isbn__icontains=q)         |
                Q(authors__first_name__icontains=q) |
                Q(authors__last_name__icontains=q)
            ).distinct()
        if form.cleaned_data.get('category'):
            books = books.filter(category=form.cleaned_data['category'])
        if form.cleaned_data.get('language'):
            books = books.filter(language=form.cleaned_data['language'])
        if form.cleaned_data.get('available_only'):
            books = books.filter(available_copies__gt=0)

    paginator = Paginator(books, 20)
    page      = request.GET.get('page', 1)
    books     = paginator.get_page(page)

    return render(request, 'library/book_list.html', {
        'books':      books,
        'form':       form,
        'page_title': 'Book Catalog',
    })


@login_required
def book_detail(request, pk):
    book   = get_object_or_404(
        Book.objects.select_related('category', 'publisher')
            .prefetch_related('authors', 'copies'),
        pk=pk
    )
    copies = book.copies.order_by('status', 'accession_number')

    # Active issuances for this book
    issuances = BookIssuance.objects.filter(
        book_copy__book=book,
        status__in=['issued', 'overdue']
    ).select_related('student__user', 'staff__user', 'book_copy')

    # Pending reservations
    reservations = book.reservations.filter(
        status='pending'
    ).select_related('student__user').order_by('reserved_date')

    return render(request, 'library/book_detail.html', {
        'book':         book,
        'copies':       copies,
        'issuances':    issuances,
        'reservations': reservations,
        'page_title':   book.title,
    })


@librarian_required
def book_create(request):
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        book = form.save()
        messages.success(request, f'"{book.title}" added to catalog.')
        return redirect('book_detail', pk=book.pk)
    return render(request, 'library/book_form.html', {
        'form':       form,
        'title':      'Add Book',
        'page_title': 'Add Book',
    })


@librarian_required
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(
        request.POST or None,
        request.FILES or None,
        instance=book
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{book.title}" updated.')
        return redirect('book_detail', pk=book.pk)
    return render(request, 'library/book_form.html', {
        'form':       form,
        'book':       book,
        'title':      f'Edit — {book.title}',
        'page_title': 'Edit Book',
    })


@librarian_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if book.copies.filter(status='issued').exists():
        messages.error(
            request,
            f'Cannot delete "{book.title}" — copies are currently issued.'
        )
        return redirect('book_detail', pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted from catalog.')
        return redirect('book_list')
    return render(request, 'library/confirm_delete.html', {
        'object':   book,
        'title':    f'Delete — {book.title}',
        'back_url': f'/library/books/{pk}/',
    })


# ══════════════════════════════════════════════
#  BOOK COPIES
# ══════════════════════════════════════════════

@librarian_required
def copy_add(request, book_pk):
    book = get_object_or_404(Book, pk=book_pk)
    form = BookCopyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        copy      = form.save(commit=False)
        copy.book = book
        copy.save()
        messages.success(
            request,
            f'Copy [{copy.accession_number}] added to "{book.title}".'
        )
        return redirect('book_detail', pk=book.pk)
    return render(request, 'library/copy_form.html', {
        'form':       form,
        'book':       book,
        'title':      f'Add Copy — {book.title}',
        'page_title': 'Add Book Copy',
    })


@librarian_required
def copy_edit(request, pk):
    copy = get_object_or_404(BookCopy.objects.select_related('book'), pk=pk)
    form = BookCopyForm(request.POST or None, instance=copy)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Copy updated.')
        return redirect('book_detail', pk=copy.book.pk)
    return render(request, 'library/copy_form.html', {
        'form':       form,
        'book':       copy.book,
        'copy':       copy,
        'title':      f'Edit Copy [{copy.accession_number}]',
        'page_title': 'Edit Book Copy',
    })


@librarian_required
def copy_delete(request, pk):
    copy = get_object_or_404(BookCopy, pk=pk)
    if copy.status == 'issued':
        messages.error(request, 'Cannot delete — copy is currently issued.')
        return redirect('book_detail', pk=copy.book.pk)
    book_pk = copy.book.pk
    if request.method == 'POST':
        copy.delete()
        messages.success(request, 'Copy deleted.')
        return redirect('book_detail', pk=book_pk)
    return render(request, 'library/confirm_delete.html', {
        'object':   copy,
        'title':    f'Delete Copy [{copy.accession_number}]',
        'back_url': f'/library/books/{book_pk}/',
    })


# ══════════════════════════════════════════════
#  ISSUANCE (CHECKOUT)
# ══════════════════════════════════════════════

@librarian_required
def issuance_list(request):
    today    = timezone.now().date()
    form     = IssuanceFilterForm(request.GET or None)
    issuances = BookIssuance.objects.select_related(
        'book_copy__book',
        'student__user',
        'staff__user',
        'issued_by',
    ).order_by('-issued_date')

    # Auto-mark overdue
    BookIssuance.objects.filter(
        status='issued', due_date__lt=today
    ).update(status='overdue')

    if form.is_valid():
        if form.cleaned_data.get('status'):
            issuances = issuances.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('date_from'):
            issuances = issuances.filter(
                issued_date__gte=form.cleaned_data['date_from']
            )
        if form.cleaned_data.get('date_to'):
            issuances = issuances.filter(
                issued_date__lte=form.cleaned_data['date_to']
            )
        q = form.cleaned_data.get('q', '').strip()
        if q:
            issuances = issuances.filter(
                Q(book_copy__book__title__icontains=q)   |
                Q(student__user__first_name__icontains=q)|
                Q(student__user__last_name__icontains=q) |
                Q(staff__user__first_name__icontains=q)  |
                Q(staff__user__last_name__icontains=q)   |
                Q(book_copy__accession_number__icontains=q)
            )

    paginator = Paginator(issuances, 25)
    page      = request.GET.get('page', 1)
    issuances = paginator.get_page(page)

    return render(request, 'library/issuance_list.html', {
        'issuances':  issuances,
        'form':       form,
        'today':      today,
        'page_title': 'Book Issuances',
    })


@librarian_required
def issue_book(request):
    form = BookIssuanceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        issuance           = form.save(commit=False)
        issuance.issued_by = request.user
        issuance.save()

        # Mark copy as issued
        copy        = issuance.book_copy
        copy.status = 'issued'
        copy.save()
        copy.book.update_copy_counts()

        messages.success(
            request,
            f'"{copy.book.title}" issued to {issuance.borrower}. '
            f'Due: {issuance.due_date}'
        )
        return redirect('issuance_detail', pk=issuance.pk)
    return render(request, 'library/issue_form.html', {
        'form':       form,
        'title':      'Issue Book',
        'page_title': 'Issue Book',
    })


@librarian_required
def issuance_detail(request, pk):
    issuance = get_object_or_404(
        BookIssuance.objects.select_related(
            'book_copy__book', 'student__user',
            'staff__user', 'issued_by', 'returned_to'
        ),
        pk=pk
    )

    # Get or compute fine
    fine = None
    if issuance.is_overdue or issuance.status == 'overdue':
        fine, created = Fine.objects.get_or_create(
            issuance=issuance,
            defaults={'fine_per_day': 2.00}
        )
        fine.compute()

    return render(request, 'library/issuance_detail.html', {
        'issuance':   issuance,
        'fine':       fine,
        'today':      timezone.now().date(),
        'page_title': f'Issuance — {issuance.book_copy.book.title}',
    })


@librarian_required
def return_book(request, pk):
    issuance = get_object_or_404(
        BookIssuance.objects.select_related('book_copy__book'),
        pk=pk
    )
    if issuance.status == 'returned':
        messages.info(request, 'This book has already been returned.')
        return redirect('issuance_detail', pk=issuance.pk)

    form = ReturnBookForm(
        request.POST or None,
        initial={'condition': issuance.book_copy.condition}
    )
    if request.method == 'POST' and form.is_valid():
        if form.cleaned_data.get('mark_lost'):
            issuance.mark_lost()
            messages.warning(
                request,
                f'"{issuance.book_copy.book.title}" marked as lost.'
            )
        else:
            # Update copy condition
            issuance.book_copy.condition = form.cleaned_data['condition']
            issuance.book_copy.notes     = form.cleaned_data.get('notes', '')
            issuance.book_copy.save()
            issuance.mark_returned(returned_to=request.user)

            # Create fine if overdue
            if issuance.days_overdue > 0:
                fine, _ = Fine.objects.get_or_create(
                    issuance=issuance,
                    defaults={'fine_per_day': 2.00}
                )
                fine.compute()
                messages.warning(
                    request,
                    f'Book returned {issuance.days_overdue} day(s) late. '
                    f'Fine: ETB {fine.total_amount}'
                )
            else:
                messages.success(
                    request,
                    f'"{issuance.book_copy.book.title}" returned successfully.'
                )

        return redirect('issuance_detail', pk=issuance.pk)

    return render(request, 'library/return_form.html', {
        'issuance':   issuance,
        'form':       form,
        'page_title': 'Return Book',
    })


# ══════════════════════════════════════════════
#  FINES
# ══════════════════════════════════════════════

@librarian_required
def fine_list(request):
    fines = Fine.objects.select_related(
        'issuance__book_copy__book',
        'issuance__student__user',
        'issuance__staff__user',
        'collected_by',
    ).order_by('-created_at')

    status = request.GET.get('status', '')
    if status:
        fines = fines.filter(status=status)

    total_pending = Fine.objects.filter(
        status='pending'
    ).aggregate(s=Sum('total_amount'))['s'] or 0
    total_paid    = Fine.objects.filter(
        status='paid'
    ).aggregate(s=Sum('total_amount'))['s'] or 0

    paginator = Paginator(fines, 25)
    page      = request.GET.get('page', 1)
    fines     = paginator.get_page(page)

    return render(request, 'library/fine_list.html', {
        'fines':         fines,
        'status':        status,
        'total_pending': total_pending,
        'total_paid':    total_paid,
        'page_title':    'Library Fines',
    })


@librarian_required
def fine_pay(request, pk):
    fine = get_object_or_404(Fine, pk=pk)
    if fine.status != 'pending':
        messages.info(request, f'Fine is already {fine.get_status_display().lower()}.')
        return redirect('issuance_detail', pk=fine.issuance.pk)

    form = FinePaymentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        fine.mark_paid(collected_by=request.user)
        messages.success(
            request,
            f'Fine of ETB {fine.total_amount} marked as paid.'
        )
        return redirect('issuance_detail', pk=fine.issuance.pk)

    return render(request, 'library/fine_pay.html', {
        'fine':       fine,
        'form':       form,
        'page_title': 'Collect Fine',
    })


@librarian_required
def fine_waive(request, pk):
    fine = get_object_or_404(Fine, pk=pk)
    if fine.status != 'pending':
        messages.info(request, f'Fine is already {fine.get_status_display().lower()}.')
        return redirect('issuance_detail', pk=fine.issuance.pk)

    form = FineWaiverForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        fine.waive(reason=form.cleaned_data['reason'])
        messages.success(request, 'Fine waived.')
        return redirect('issuance_detail', pk=fine.issuance.pk)

    return render(request, 'library/fine_waive.html', {
        'fine':       fine,
        'form':       form,
        'page_title': 'Waive Fine',
    })


# ══════════════════════════════════════════════
#  RESERVATIONS
# ══════════════════════════════════════════════

@librarian_required
def reservation_list(request):
    today        = timezone.now().date()
    reservations = Reservation.objects.select_related(
        'book', 'student__user'
    ).order_by('-reserved_date')

    # Auto-expire
    Reservation.objects.filter(
        status='pending', expiry_date__lt=today
    ).update(status='expired')

    status = request.GET.get('status', 'pending')
    if status:
        reservations = reservations.filter(status=status)

    paginator    = Paginator(reservations, 25)
    page         = request.GET.get('page', 1)
    reservations = paginator.get_page(page)

    return render(request, 'library/reservation_list.html', {
        'reservations': reservations,
        'status':       status,
        'page_title':   'Reservations',
    })


@librarian_required
def reservation_create(request):
    form = ReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        res = form.save()
        messages.success(
            request,
            f'Reservation created for '
            f'{res.student.user.get_full_name()} — "{res.book.title}".'
        )
        return redirect('reservation_list')
    return render(request, 'library/reservation_form.html', {
        'form':       form,
        'title':      'New Reservation',
        'page_title': 'Create Reservation',
    })


@librarian_required
def reservation_cancel(request, pk):
    res = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        res.status = 'cancelled'
        res.save()
        messages.success(request, 'Reservation cancelled.')
        return redirect('reservation_list')
    return render(request, 'library/confirm_delete.html', {
        'object':   res,
        'title':    'Cancel Reservation',
        'back_url': '/library/reservations/',
        'btn_label': 'Yes, Cancel',
        'btn_class': 'btn-warning',
    })


@librarian_required
def reservation_fulfil(request, pk):
    """Convert a reservation into an issuance"""
    res = get_object_or_404(
        Reservation.objects.select_related('book', 'student__user'),
        pk=pk
    )
    if res.status != 'pending':
        messages.error(request, 'Reservation is not pending.')
        return redirect('reservation_list')

    # Pre-fill issuance form with reservation data
    initial = {
        'borrower_type': 'student',
        'student':       res.student,
        'issued_date':   timezone.now().date(),
        'due_date':      timezone.now().date() + timedelta(days=14),
    }
    form = BookIssuanceForm(request.POST or None, initial=initial)
    # Filter copies to this book only
    form.fields['book_copy'].queryset = BookCopy.objects.filter(
        book=res.book, status='available'
    )

    if request.method == 'POST' and form.is_valid():
        issuance           = form.save(commit=False)
        issuance.issued_by = request.user
        issuance.save()

        copy        = issuance.book_copy
        copy.status = 'issued'
        copy.save()
        copy.book.update_copy_counts()

        res.status = 'fulfilled'
        res.save()

        messages.success(
            request,
            f'Reservation fulfilled — "{res.book.title}" issued to '
            f'{res.student.user.get_full_name()}.'
        )
        return redirect('issuance_detail', pk=issuance.pk)

    return render(request, 'library/issue_form.html', {
        'form':        form,
        'reservation': res,
        'title':       f'Fulfil Reservation — {res.book.title}',
        'page_title':  'Fulfil Reservation',
    })


# ══════════════════════════════════════════════
#  STUDENT: MY BOOKS
# ══════════════════════════════════════════════

@login_required
def my_books(request):
    try:
        student = request.user.student
    except Exception:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    issuances = BookIssuance.objects.filter(
        student=student
    ).select_related(
        'book_copy__book'
    ).order_by('-issued_date')

    active    = issuances.filter(status__in=['issued', 'overdue'])
    history   = issuances.filter(status__in=['returned', 'lost'])
    reservations = Reservation.objects.filter(
        student=student, status='pending'
    ).select_related('book')

    return render(request, 'library/my_books.html', {
        'student':      student,
        'active':       active,
        'history':      history,
        'reservations': reservations,
        'today':        timezone.now().date(),
        'page_title':   'My Books',
    })


# ══════════════════════════════════════════════
#  CATEGORIES / AUTHORS / PUBLISHERS  (CRUD)
# ══════════════════════════════════════════════

@librarian_required
def category_list(request):
    categories = BookCategory.objects.annotate(
        book_count=Count('books')
    ).order_by('name')
    return render(request, 'library/category_list.html', {
        'categories': categories,
        'page_title': 'Book Categories',
    })


@librarian_required
def category_create(request):
    form = BookCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cat = form.save()
        messages.success(request, f'Category "{cat.name}" created.')
        return redirect('library_category_list')
    return render(request, 'library/category_form.html', {
        'form':       form,
        'title':      'Add Category',
        'page_title': 'Add Book Category',
    })


@librarian_required
def category_edit(request, pk):
    cat  = get_object_or_404(BookCategory, pk=pk)
    form = BookCategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Category "{cat.name}" updated.')
        return redirect('library_category_list')
    return render(request, 'library/category_form.html', {
        'form':       form,
        'title':      f'Edit — {cat.name}',
        'page_title': 'Edit Category',
    })


@librarian_required
def author_list(request):
    authors = Author.objects.annotate(
        book_count=Count('books')
    ).order_by('last_name')
    return render(request, 'library/author_list.html', {
        'authors':    authors,
        'page_title': 'Authors',
    })


@librarian_required
def author_create(request):
    form = AuthorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        a = form.save()
        messages.success(request, f'Author "{a.full_name}" added.')
        return redirect('library_author_list')
    return render(request, 'library/author_form.html', {
        'form':       form,
        'title':      'Add Author',
        'page_title': 'Add Author',
    })


@librarian_required
def author_edit(request, pk):
    author = get_object_or_404(Author, pk=pk)
    form   = AuthorForm(request.POST or None, instance=author)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Author "{author.full_name}" updated.')
        return redirect('library_author_list')
    return render(request, 'library/author_form.html', {
        'form':       form,
        'title':      f'Edit — {author.full_name}',
        'page_title': 'Edit Author',
    })


@librarian_required
def publisher_list(request):
    publishers = Publisher.objects.annotate(
        book_count=Count('books')
    ).order_by('name')
    return render(request, 'library/publisher_list.html', {
        'publishers': publishers,
        'page_title': 'Publishers',
    })


@librarian_required
def publisher_create(request):
    form = PublisherForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pub = form.save()
        messages.success(request, f'Publisher "{pub.name}" added.')
        return redirect('library_publisher_list')
    return render(request, 'library/publisher_form.html', {
        'form':       form,
        'title':      'Add Publisher',
        'page_title': 'Add Publisher',
    })


@librarian_required
def publisher_edit(request, pk):
    pub  = get_object_or_404(Publisher, pk=pk)
    form = PublisherForm(request.POST or None, instance=pub)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Publisher "{pub.name}" updated.')
        return redirect('library_publisher_list')
    return render(request, 'library/publisher_form.html', {
        'form':       form,
        'title':      f'Edit — {pub.name}',
        'page_title': 'Edit Publisher',
    })