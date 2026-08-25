# apps/fees/views.py

from django.shortcuts      import render, redirect, get_object_or_404
from django.contrib        import messages
from django.core.paginator import Paginator
from django.db.models      import Q, Sum, Count
from django.utils          import timezone
from datetime import date
import calendar 

from apps.core.decorators  import (
    admin_required, principal_or_above, accountant_required
)
from apps.core.models      import AcademicYear
from apps.academic.models  import Grade
from apps.students.models  import Student, Enrollment
from .models               import (
    FeeCategory, FeeStructure, StudentFee, Payment
)
from .forms                import (
    FeeCategoryForm, FeeStructureForm, StudentFeeForm,
    BulkFeeAssignForm, PaymentForm, FeeReportForm
)


# ══════════════════════════════════════════════
#  FEE CATEGORY CRUD
# ══════════════════════════════════════════════

@accountant_required
def fee_category_list(request):
    categories = FeeCategory.objects.annotate(
        structure_count=Count('fee_structures')
    ).order_by('name')
    return render(request, 'fees/fee_category_list.html', {
        'categories': categories,
        'page_title': 'Fee Categories',
    })


@accountant_required
def fee_category_create(request):
    form = FeeCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cat = form.save()
        messages.success(request, f'Category "{cat.name}" created.')
        return redirect('fee_category_list')
    return render(request, 'fees/fee_category_form.html', {
        'form': form, 'title': 'Create Fee Category',
        'page_title': 'Create Fee Category',
    })


@accountant_required
def fee_category_edit(request, pk):
    cat  = get_object_or_404(FeeCategory, pk=pk)
    form = FeeCategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Category "{cat.name}" updated.')
        return redirect('fee_category_list')
    return render(request, 'fees/fee_category_form.html', {
        'form': form, 'title': f'Edit — {cat.name}',
        'page_title': 'Edit Fee Category', 'category': cat,
    })


@principal_or_above
def fee_category_delete(request, pk):
    cat = get_object_or_404(FeeCategory, pk=pk)
    if cat.fee_structures.exists():
        messages.error(
            request,
            f'Cannot delete "{cat.name}" — '
            f'it is used in fee structures.'
        )
        return redirect('fee_category_list')
    if request.method == 'POST':
        cat.delete()
        messages.success(request, f'Category deleted.')
        return redirect('fee_category_list')
    return render(request, 'fees/confirm_delete.html', {
    'object':   cat,
    'title':    f'Delete Category — {cat.name}',
    'back_url': '/fees/categories/',
})


# ══════════════════════════════════════════════
#  FEE STRUCTURE CRUD
# ══════════════════════════════════════════════

@accountant_required
def fee_structure_list(request):
    structures = FeeStructure.objects.select_related(
        'academic_year', 'grade', 'fee_category', 'term'
    ).order_by('academic_year', 'grade__order', 'fee_category__name')

    year_id  = request.GET.get('year',  '')
    grade_id = request.GET.get('grade', '')

    if year_id:
        structures = structures.filter(academic_year_id=year_id)
    else:
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            structures = structures.filter(academic_year=current)
            year_id    = str(current.pk)

    if grade_id:
        structures = structures.filter(grade_id=grade_id)

    years  = AcademicYear.objects.order_by('-start_date')
    grades = Grade.objects.order_by('order')
    today = date.today()
    this_month_end = date(
        today.year,
        today.month,
        calendar.monthrange(today.year, today.month)[1]
    )
    return render(request, 'fees/fee_structure_list.html', {
        'structures': structures,
        'years':      years,
        'grades':     grades,
        'year_id':    year_id,
        'grade_id':   grade_id,
        'page_title': 'Fee Structures',
        'today':          today,
        'this_month_end': this_month_end,
    })


@accountant_required
def fee_structure_create(request):
    form = FeeStructureForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        fs = form.save()
        messages.success(
            request,
            f'Fee structure for "{fs.fee_category}" '
            f'in {fs.grade} created.'
        )
        return redirect('fee_structure_list')
    return render(request, 'fees/fee_structure_form.html', {
        'form': form, 'title': 'Create Fee Structure',
        'page_title': 'Create Fee Structure',
    })


@accountant_required
def fee_structure_edit(request, pk):
    fs   = get_object_or_404(FeeStructure, pk=pk)
    form = FeeStructureForm(request.POST or None, instance=fs)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fee structure updated.')
        return redirect('fee_structure_list')
    return render(request, 'fees/fee_structure_form.html', {
        'form': form, 'title': 'Edit Fee Structure',
        'page_title': 'Edit Fee Structure', 'structure': fs,
    })


@principal_or_above
def fee_structure_delete(request, pk):
    fs = get_object_or_404(FeeStructure, pk=pk)
    if fs.student_fees.exists():
        messages.error(
            request,
            'Cannot delete — student fees are already '
            'assigned from this structure.'
        )
        return redirect('fee_structure_list')
    if request.method == 'POST':
        fs.delete()
        messages.success(request, 'Fee structure deleted.')
        return redirect('fee_structure_list')
    return render(request, 'fees/confirm_delete.html', {
    'object':   fs,
    'title':    'Delete Fee Structure',
    'back_url': '/fees/structures/',
})


# ══════════════════════════════════════════════
#  BULK FEE ASSIGNMENT
# ══════════════════════════════════════════════

@accountant_required
def bulk_assign_fees(request):
    """
    Assign a fee structure to all enrolled students
    in a grade for the current academic year.
    Skips students who already have the fee assigned.
    """
    form = BulkFeeAssignForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        fee_structure = form.cleaned_data['fee_structure']
        academic_year = form.cleaned_data['academic_year']

        enrollments = Enrollment.objects.filter(
            section__grade=fee_structure.grade,
            academic_year=academic_year,
            is_active=True
        ).select_related('student')

        created  = 0
        skipped  = 0

        for enr in enrollments:
            _, was_created = StudentFee.objects.get_or_create(
                student=enr.student,
                fee_structure=fee_structure,
                defaults={
                    'academic_year': academic_year,
                    'amount_due':    fee_structure.amount,
                    'due_date':      fee_structure.due_date,
                }
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        messages.success(
            request,
            f'Bulk assignment complete — '
            f'{created} assigned, {skipped} skipped (already existed).'
        )
        return redirect('student_fee_list')

    return render(request, 'fees/bulk_assign_fees.html', {
        'form': form, 'page_title': 'Bulk Assign Fees',
    })


# ══════════════════════════════════════════════
#  STUDENT FEE LIST
# ══════════════════════════════════════════════

@accountant_required
def student_fee_list(request):
    fees = StudentFee.objects.select_related(
        'student__user',
        'fee_structure__fee_category',
        'fee_structure__grade',
        'academic_year',
    ).order_by('student__user__first_name')

    # Auto-update overdue statuses
    today = timezone.now().date()
    fees.filter(
        status='pending',
        due_date__lt=today
    ).update(status='overdue')

    # Filters
    year_id  = request.GET.get('year',   '')
    status   = request.GET.get('status', '')
    grade_id = request.GET.get('grade',  '')
    q        = request.GET.get('q',      '').strip()

    if year_id:
        fees = fees.filter(academic_year_id=year_id)
    else:
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            fees    = fees.filter(academic_year=current)
            year_id = str(current.pk)

    if status:
        fees = fees.filter(status=status)
    if grade_id:
        fees = fees.filter(fee_structure__grade_id=grade_id)
    if q:
        fees = fees.filter(
            Q(student__user__first_name__icontains=q) |
            Q(student__user__last_name__icontains=q)  |
            Q(student__admission_number__icontains=q)
        )

    # Summary
    total_due  = fees.aggregate(s=Sum('amount_due'))['s']  or 0
    total_paid = fees.aggregate(s=Sum('amount_paid'))['s'] or 0
    total_disc = fees.aggregate(s=Sum('discount'))['s']    or 0
    outstanding= float(total_due) - float(total_disc) - float(total_paid)

    paginator  = Paginator(fees, 25)
    page       = request.GET.get('page', 1)
    fees       = paginator.get_page(page)

    years  = AcademicYear.objects.order_by('-start_date')
    grades = Grade.objects.order_by('order')

    return render(request, 'fees/student_fee_list.html', {
        'fees':        fees,
        'years':       years,
        'grades':      grades,
        'year_id':     year_id,
        'status':      status,
        'grade_id':    grade_id,
        'q':           q,
        'total_due':   total_due,
        'total_paid':  total_paid,
        'outstanding': outstanding,
        'page_title':  'Student Fees',
    })


# ══════════════════════════════════════════════
#  STUDENT FEE DETAIL + COLLECT PAYMENT
# ══════════════════════════════════════════════

@accountant_required
def student_fee_detail(request, pk):
    sf       = get_object_or_404(
        StudentFee.objects.select_related(
            'student__user',
            'fee_structure__fee_category',
            'fee_structure__grade',
            'academic_year',
        ),
        pk=pk
    )
    payments = sf.payments.select_related('collected_by').order_by('-payment_date')
    form     = PaymentForm(sf, request.POST or None)

    if request.method == 'POST':
        if sf.status in ['paid', 'waived']:
            messages.error(
                request,
                f'This fee is already {sf.get_status_display().lower()}. '
                f'No further payment accepted.'
            )
            return redirect('student_fee_detail', pk=sf.pk)

        if form.is_valid():
            payment               = form.save(commit=False)
            payment.student_fee   = sf
            payment.collected_by  = request.user
            payment.save()           # triggers StudentFee.amount_paid update

            messages.success(
                request,
                f'Payment of {payment.amount} recorded. '
                f'Balance: {sf.balance:.2f}'
            )
            return redirect('student_fee_detail', pk=sf.pk)

    return render(request, 'fees/student_fee_detail.html', {
        'sf':         sf,
        'payments':   payments,
        'form':       form,
        'page_title': f'Fee — {sf.student.user.get_full_name()}',
    })


# ══════════════════════════════════════════════
#  WAIVE FEE
# ══════════════════════════════════════════════

@principal_or_above
def waive_fee(request, pk):
    sf = get_object_or_404(StudentFee, pk=pk)
    if request.method == 'POST':
        reason      = request.POST.get('reason', '').strip()
        sf.status   = 'waived'
        sf.waiver_reason = reason
        sf.save()
        messages.success(
            request,
            f'Fee waived for {sf.student.user.get_full_name()}.'
        )
        return redirect('student_fee_detail', pk=sf.pk)
    return render(request, 'fees/waive_fee_confirm.html', {
        'sf': sf, 'page_title': 'Waive Fee',
    })


# ══════════════════════════════════════════════
#  STUDENT: my fees
# ══════════════════════════════════════════════

def my_fees(request):
    """Student views their own fees"""
    try:
        student = request.user.student
    except Exception:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    current_year = AcademicYear.objects.filter(is_current=True).first()
    fees = StudentFee.objects.filter(
        student=student,
        academic_year=current_year,
    ).select_related(
        'fee_structure__fee_category'
    ).order_by('status')

    total_due     = sum(float(f.effective_amount) for f in fees)
    total_paid    = sum(float(f.amount_paid)       for f in fees)
    outstanding   = total_due - total_paid

    return render(request, 'fees/my_fees.html', {
        'fees':         fees,
        'total_due':    total_due,
        'total_paid':   total_paid,
        'outstanding':  outstanding,
        'current_year': current_year,
        'page_title':   'My Fees',
        'today': timezone.now().date(),
    })


# ══════════════════════════════════════════════
#  FEE REPORT
# ══════════════════════════════════════════════

@accountant_required
def fee_report(request):
    form    = FeeReportForm(request.GET or None)
    fees    = None
    summary = {}

    if form.is_valid():
        fees = StudentFee.objects.select_related(
            'student__user',
            'fee_structure__fee_category',
            'fee_structure__grade',
            'academic_year',
        )

        if form.cleaned_data.get('academic_year'):
            fees = fees.filter(
                academic_year=form.cleaned_data['academic_year']
            )
        if form.cleaned_data.get('grade'):
            fees = fees.filter(
                fee_structure__grade=form.cleaned_data['grade']
            )
        if form.cleaned_data.get('status'):
            fees = fees.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('fee_category'):
            fees = fees.filter(
                fee_structure__fee_category=form.cleaned_data['fee_category']
            )
        if form.cleaned_data.get('date_from'):
            fees = fees.filter(
                created_at__date__gte=form.cleaned_data['date_from']
            )
        if form.cleaned_data.get('date_to'):
            fees = fees.filter(
                created_at__date__lte=form.cleaned_data['date_to']
            )

        # Summary
        summary = fees.aggregate(
            total_due=Sum('amount_due'),
            total_paid=Sum('amount_paid'),
            total_discount=Sum('discount'),
            total_count=Count('id'),
        )
        summary['outstanding'] = (
            float(summary['total_due']      or 0) -
            float(summary['total_discount'] or 0) -
            float(summary['total_paid']     or 0)
        )

        fees = fees.order_by(
            'fee_structure__grade__order',
            'student__user__first_name'
        )

    return render(request, 'fees/fee_report.html', {
        'form':       form,
        'fees':       fees,
        'summary':    summary,
        'page_title': 'Fee Report',
    })


# ══════════════════════════════════════════════
#  DAILY COLLECTION
# ══════════════════════════════════════════════

@accountant_required
def daily_collection(request):
    """Today's payment summary"""
    date_str = request.GET.get('date', '')
    try:
        from datetime import date as date_type
        report_date = date_type.fromisoformat(date_str) if date_str else timezone.now().date()
    except ValueError:
        report_date = timezone.now().date()

    payments = Payment.objects.filter(
        payment_date=report_date
    ).select_related(
        'student_fee__student__user',
        'student_fee__fee_structure__fee_category',
        'collected_by',
    ).order_by('created_at')

    total = payments.aggregate(s=Sum('amount'))['s'] or 0

    return render(request, 'fees/daily_collection.html', {
        'payments':    payments,
        'report_date': report_date,
        'total':       total,
        'page_title':  'Daily Collection',
        'today': timezone.now().date(),
    })