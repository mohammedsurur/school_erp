# apps/fees/models.py

from django.db        import models
from django.utils     import timezone
from django.core.validators import MinValueValidator


class FeeCategory(models.Model):
    """
    Type of fee — e.g. Tuition, Library, Transport, Uniform.
    Each category can be mandatory or optional.
    """
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_mandatory= models.BooleanField(
        default=True,
        help_text='Mandatory fees are auto-assigned to all students'
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Fee Category'
        verbose_name_plural = 'Fee Categories'
        ordering            = ['name']

    def __str__(self):
        return self.name


class FeeStructure(models.Model):
    """
    Defines how much a specific fee category costs
    for a specific grade in a specific academic year.
    """
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    grade         = models.ForeignKey(
        'academic.Grade',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    fee_category  = models.ForeignKey(
        FeeCategory,
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    amount        = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    due_date      = models.DateField(
        null=True, blank=True,
        help_text='Optional deadline for this fee'
    )
    term          = models.ForeignKey(
        'core.Term',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='fee_structures',
        help_text='Leave blank for annual fee'
    )

    class Meta:
        verbose_name    = 'Fee Structure'
        unique_together = ('academic_year', 'grade', 'fee_category', 'term')
        ordering        = ['grade__order', 'fee_category__name']

    def __str__(self):
        return (
            f"{self.fee_category} — {self.grade} — "
            f"{self.academic_year} — {self.amount}"
        )


class StudentFee(models.Model):
    """
    An individual fee invoice assigned to a student.
    Auto-created from FeeStructure when student enrolls.
    """
    STATUS = [
        ('pending',   'Pending'),
        ('partial',   'Partially Paid'),
        ('paid',      'Paid'),
        ('waived',    'Waived'),
        ('overdue',   'Overdue'),
    ]

    student       = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='fees'
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name='student_fees'
    )
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.CASCADE,
        related_name='student_fees'
    )
    amount_due    = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    amount_paid   = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    discount      = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Scholarship or discount amount'
    )
    status        = models.CharField(
        max_length=10,
        choices=STATUS,
        default='pending'
    )
    due_date      = models.DateField(null=True, blank=True)
    waiver_reason = models.CharField(max_length=255, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name    = 'Student Fee'
        unique_together = ('student', 'fee_structure')
        ordering        = ['student__user__first_name', 'fee_structure__fee_category__name']

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} — "
            f"{self.fee_structure.fee_category} — "
            f"{self.status}"
        )

    # ── Computed properties ──────────────────

    @property
    def effective_amount(self):
        """Amount after discount"""
        return max(0, float(self.amount_due) - float(self.discount))

    @property
    def balance(self):
        """Remaining balance"""
        return max(0, self.effective_amount - float(self.amount_paid))

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['paid', 'waived']:
            return self.due_date < timezone.now().date()
        return False

    def update_status(self):
        """Auto-update status based on payments"""
        paid  = float(self.amount_paid)
        eff   = self.effective_amount

        if self.status == 'waived':
            return
        if paid <= 0:
            self.status = 'overdue' if self.is_overdue else 'pending'
        elif paid >= eff:
            self.status = 'paid'
        else:
            self.status = 'partial'
        self.save(update_fields=['status'])


class Payment(models.Model):
    """
    A single payment transaction against a StudentFee.
    Multiple payments can exist per StudentFee (partial payments).
    """
    PAYMENT_METHOD = [
        ('cash',          'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque',        'Cheque'),
        ('mobile_money',  'Mobile Money'),
        ('online',        'Online'),
    ]

    student_fee     = models.ForeignKey(
        StudentFee,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount          = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    payment_method  = models.CharField(
        max_length=20, choices=PAYMENT_METHOD, default='cash'
    )
    payment_date    = models.DateField(default=timezone.now)
    reference_number= models.CharField(
        max_length=100, blank=True,
        help_text='Receipt / transaction reference'
    )
    note            = models.TextField(blank=True)
    collected_by    = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='collected_payments'
    )
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Payment'
        ordering     = ['-payment_date', '-created_at']

    def __str__(self):
        return (
            f"{self.student_fee.student.user.get_full_name()} — "
            f"{self.amount} — {self.payment_date}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate total paid on the parent StudentFee
        sf              = self.student_fee
        sf.amount_paid  = sum(
            p.amount for p in sf.payments.all()
        )
        sf.save(update_fields=['amount_paid'])
        sf.update_status()