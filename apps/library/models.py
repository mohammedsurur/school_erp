# apps/library/models.py

from django.db         import models
from django.utils      import timezone
from django.core.validators import MinValueValidator


# ─────────────────────────────────────────────
#  Book Category
# ─────────────────────────────────────────────

class BookCategory(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Book Category'
        verbose_name_plural = 'Book Categories'
        ordering            = ['name']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
#  Author
# ─────────────────────────────────────────────

class Author(models.Model):
    first_name  = models.CharField(max_length=100)
    last_name   = models.CharField(max_length=100)
    bio         = models.TextField(blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


# ─────────────────────────────────────────────
#  Publisher
# ─────────────────────────────────────────────

class Publisher(models.Model):
    name    = models.CharField(max_length=200, unique=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ─────────────────────────────────────────────
#  Book  (catalog entry)
# ─────────────────────────────────────────────

class Book(models.Model):
    LANGUAGE = [
        ('amharic', 'Amharic'),
        ('english', 'English'),
        ('other',   'Other'),
    ]

    title           = models.CharField(max_length=255)
    isbn            = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        help_text='ISBN-10 or ISBN-13'
    )
    authors         = models.ManyToManyField(
        Author, blank=True, related_name='books'
    )
    category        = models.ForeignKey(
        BookCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='books'
    )
    publisher       = models.ForeignKey(
        Publisher, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='books'
    )
    publication_year= models.PositiveIntegerField(null=True, blank=True)
    edition         = models.CharField(max_length=50, blank=True)
    language        = models.CharField(
        max_length=20, choices=LANGUAGE, default='english'
    )
    description     = models.TextField(blank=True)
    cover_image     = models.ImageField(
        upload_to='library/covers/', null=True, blank=True
    )
    total_copies    = models.PositiveIntegerField(
        default=0,
        help_text='Auto-updated from BookCopy count'
    )
    available_copies= models.PositiveIntegerField(default=0)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title

    def update_copy_counts(self):
        """Recount total and available copies"""
        self.total_copies     = self.copies.count()
        self.available_copies = self.copies.filter(
            status='available'
        ).count()
        self.save(update_fields=['total_copies', 'available_copies'])

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def author_names(self):
        return ', '.join(a.full_name for a in self.authors.all())


# ─────────────────────────────────────────────
#  BookCopy  (physical copy of a book)
# ─────────────────────────────────────────────

class BookCopy(models.Model):
    CONDITION = [
        ('new',      'New'),
        ('good',     'Good'),
        ('fair',     'Fair'),
        ('poor',     'Poor'),
        ('damaged',  'Damaged'),
    ]
    STATUS = [
        ('available', 'Available'),
        ('issued',    'Issued'),
        ('reserved',  'Reserved'),
        ('lost',      'Lost'),
        ('damaged',   'Damaged'),
    ]

    book            = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name='copies'
    )
    accession_number= models.CharField(
        max_length=50, unique=True,
        help_text='Unique copy identifier e.g. LIB-0001'
    )
    condition       = models.CharField(
        max_length=10, choices=CONDITION, default='good'
    )
    status          = models.CharField(
        max_length=10, choices=STATUS, default='available'
    )
    acquired_date   = models.DateField(null=True, blank=True)
    notes           = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Book Copies'
        ordering            = ['accession_number']

    def __str__(self):
        return f"{self.book.title} [{self.accession_number}]"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.book.update_copy_counts()


# ─────────────────────────────────────────────
#  BookIssuance  (checkout + return)
# ─────────────────────────────────────────────

class BookIssuance(models.Model):
    BORROWER_TYPE = [
        ('student', 'Student'),
        ('staff',   'Staff'),
    ]
    STATUS = [
        ('issued',   'Issued'),
        ('returned', 'Returned'),
        ('overdue',  'Overdue'),
        ('lost',     'Lost'),
    ]

    book_copy       = models.ForeignKey(
        BookCopy, on_delete=models.PROTECT,
        related_name='issuances'
    )
    borrower_type   = models.CharField(
        max_length=10, choices=BORROWER_TYPE, default='student'
    )
    student         = models.ForeignKey(
        'students.Student', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='book_issuances'
    )
    staff           = models.ForeignKey(
        'staff.Staff', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='book_issuances'
    )
    issued_date     = models.DateField(default=timezone.now)
    due_date        = models.DateField()
    returned_date   = models.DateField(null=True, blank=True)
    status          = models.CharField(
        max_length=10, choices=STATUS, default='issued'
    )
    issued_by       = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='issued_books'
    )
    returned_to     = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='received_returns'
    )
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Book Issuance'
        ordering     = ['-issued_date']

    def __str__(self):
        borrower = self.student or self.staff
        return (
            f"{self.book_copy.book.title} → "
            f"{borrower} "
            f"({self.issued_date})"
        )

    @property
    def borrower(self):
        if self.student:
            return self.student.user.get_full_name()
        if self.staff:
            return self.staff.user.get_full_name()
        return '—'

    @property
    def is_overdue(self):
        if self.status == 'returned':
            return False
        return self.due_date < timezone.now().date()

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days

    @property
    def days_remaining(self):
        if self.status == 'returned':
            return 0
        delta = self.due_date - timezone.now().date()
        return delta.days

    def mark_returned(self, returned_to=None):
        self.returned_date = timezone.now().date()
        self.status        = 'returned'
        if returned_to:
            self.returned_to = returned_to
        self.save()
        # Free up the copy
        self.book_copy.status = 'available'
        self.book_copy.save()
        self.book_copy.book.update_copy_counts()

    def mark_lost(self):
        self.status           = 'lost'
        self.book_copy.status = 'lost'
        self.book_copy.save()
        self.book_copy.book.update_copy_counts()
        self.save()


# ─────────────────────────────────────────────
#  Fine  (overdue fine per issuance)
# ─────────────────────────────────────────────

class Fine(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('paid',    'Paid'),
        ('waived',  'Waived'),
    ]

    issuance        = models.OneToOneField(
        BookIssuance, on_delete=models.CASCADE,
        related_name='fine'
    )
    days_overdue    = models.PositiveIntegerField(default=0)
    fine_per_day    = models.DecimalField(
        max_digits=6, decimal_places=2, default=2.00,
        validators=[MinValueValidator(0)],
        help_text='Fine amount per overdue day in ETB'
    )
    total_amount    = models.DecimalField(
        max_digits=8, decimal_places=2, default=0
    )
    status          = models.CharField(
        max_length=10, choices=STATUS, default='pending'
    )
    paid_date       = models.DateField(null=True, blank=True)
    waiver_reason   = models.CharField(max_length=255, blank=True)
    collected_by    = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='collected_fines'
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"Fine — {self.issuance.borrower} — "
            f"ETB {self.total_amount} ({self.status})"
        )

    def compute(self):
        """Recalculate fine from days overdue"""
        self.days_overdue = self.issuance.days_overdue
        self.total_amount = round(
            self.days_overdue * float(self.fine_per_day), 2
        )
        self.save(update_fields=['days_overdue', 'total_amount'])

    def mark_paid(self, collected_by=None):
        self.status     = 'paid'
        self.paid_date  = timezone.now().date()
        if collected_by:
            self.collected_by = collected_by
        self.save()

    def waive(self, reason=''):
        self.status        = 'waived'
        self.waiver_reason = reason
        self.save()


# ─────────────────────────────────────────────
#  Reservation
# ─────────────────────────────────────────────

class Reservation(models.Model):
    STATUS = [
        ('pending',   'Pending'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired',   'Expired'),
    ]

    book            = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name='reservations'
    )
    student         = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='reservations'
    )
    reserved_date   = models.DateField(default=timezone.now)
    expiry_date     = models.DateField(
        help_text='Reservation expires if not collected by this date'
    )
    status          = models.CharField(
        max_length=10, choices=STATUS, default='pending'
    )
    notes           = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-reserved_date']
        unique_together     = ('book', 'student', 'status')

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} → "
            f"{self.book.title} ({self.status})"
        )

    @property
    def is_expired(self):
        return (
            self.status == 'pending'
            and self.expiry_date < timezone.now().date()
        )