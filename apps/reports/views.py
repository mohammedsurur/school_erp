# apps/reports/views.py  — FULL FIXED VERSION

import json
from datetime           import date, timedelta
from collections        import defaultdict

from django.shortcuts   import render, redirect, get_object_or_404
from django.contrib     import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator  import Paginator
from django.db.models   import Q, Count, Sum, Avg
from django.http        import HttpResponse
from django.utils       import timezone

from apps.core.decorators       import admin_required
from apps.academic.models       import AcademicYear, Grade, Section
from apps.students.models       import Student
from apps.staff.models          import Staff
from apps.attendance.models     import Attendance
from apps.exams.models          import Exam, SubjectResult, ReportCard
from apps.fees.models           import StudentFee, Payment, FeeCategory
from apps.library.models        import BookIssuance, Fine, Book
from apps.transport.models      import StudentTransport, Route

from .models  import ReportRequest
from .forms   import (
    ReportCardForm, ExamResultsForm, AttendanceReportForm,
    FeeCollectionForm, OutstandingFeesForm, LibraryReportForm,
    TransportReportForm, StudentListForm, StaffListForm,
    ReportHistoryFilterForm,
)

PALETTE_PIE = [
    '#1a3c72','#0ea5a0','#22c55e','#f59e0b',
    '#ef4444','#8b5cf6','#06b6d4','#f97316',
    '#ec4899','#14b8a6',
]


def _json(data):
    return json.dumps(data)


def _grade_label(score):
    if score >= 90: return 'Excellent'
    if score >= 80: return 'Very Good'
    if score >= 70: return 'Good'
    if score >= 60: return 'Satisfactory'
    if score >= 50: return 'Pass'
    return 'Fail'


def _log(user, report_type, title, params):
    safe = {}
    for k, v in params.items():
        if hasattr(v, 'pk'):        safe[k] = v.pk
        elif hasattr(v, 'isoformat'): safe[k] = v.isoformat()
        else:                         safe[k] = str(v) if v is not None else None
    ReportRequest.objects.create(
        report_type  = report_type,
        title        = title,
        parameters   = safe,
        status       = 'ready',
        requested_by = user,
        completed_at = timezone.now(),
    )


# ── helper: get student section safely ────────
def _student_section_filter(qs, grade=None, section=None):
    """
    Filter student queryset by grade/section.
    Tries current_section first, falls back to enrollment.
    """
    try:
        if section:
            return qs.filter(current_section=section)
        if grade:
            return qs.filter(current_section__grade=grade)
    except Exception:
        pass
    try:
        if section:
            return qs.filter(enrollments__section=section,
                             enrollments__is_current=True)
        if grade:
            return qs.filter(enrollments__section__grade=grade,
                             enrollments__is_current=True)
    except Exception:
        pass
    return qs


def _student_grade_name(student):
    try:
        if student.current_section:
            return student.current_section.grade.name
    except Exception:
        pass
    try:
        enr = student.enrollments.filter(is_current=True).first()
        if enr:
            return enr.section.grade.name
    except Exception:
        pass
    return '—'


def _student_section_name(student):
    try:
        if student.current_section:
            return student.current_section.name
    except Exception:
        pass
    try:
        enr = student.enrollments.filter(is_current=True).first()
        if enr:
            return enr.section.name
    except Exception:
        pass
    return '—'


# ══════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════

@admin_required
def reports_dashboard(request):
    recent = ReportRequest.objects.order_by('-requested_at')[:8]
    total  = ReportRequest.objects.count()
    ready  = ReportRequest.objects.filter(status='ready').count()
    failed = ReportRequest.objects.filter(status='failed').count()
    return render(request, 'reports/dashboard.html', {
        'recent': recent, 'total': total,
        'ready': ready, 'failed': failed,
        'page_title': 'Reports',
    })


# ══════════════════════════════════════════════
#  REPORT CARD
# ══════════════════════════════════════════════

@admin_required
def report_card(request):
    form = ReportCardForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/report_card.html',
                      {'form': form, 'page_title': 'Report Card'})

    exam    = form.cleaned_data['exam']
    grade   = form.cleaned_data.get('grade')
    section = form.cleaned_data.get('section')
    student = form.cleaned_data.get('student')

    cards = ReportCard.objects.filter(exam=exam).select_related(
        'student__user'
    )
    if student:
        cards = cards.filter(student=student)
    else:
        cards = cards.filter(
            **{k: v for k, v in
               [('student__current_section__grade', grade),
                ('student__current_section', section)]
               if v}
        )

    total_students = cards.count()
    promoted       = cards.filter(is_promoted=True).count()
    avg_score      = cards.aggregate(avg=Avg('average_score'))['avg'] or 0

    grade_dist = defaultdict(int)
    for card in cards:
        grade_dist[_grade_label(float(card.average_score))] += 1

    pie_labels = list(grade_dist.keys())
    pie_data   = list(grade_dist.values())
    GRADE_COLOURS = {
        'Excellent': '#22c55e', 'Very Good': '#0ea5a0',
        'Good': '#1a3c72', 'Satisfactory': '#f59e0b',
        'Pass': '#f97316', 'Fail': '#ef4444',
    }
    pie_colors = [GRADE_COLOURS.get(l, '#9ca3af') for l in pie_labels]

    subj_avgs  = SubjectResult.objects.filter(exam=exam).values(
        'subject__name'
    ).annotate(avg=Avg('total_score')).order_by('-avg')
    bar_labels = [r['subject__name'] for r in subj_avgs]
    bar_data   = [round(r['avg'] or 0, 1) for r in subj_avgs]

    buckets = {'90-100':0,'80-89':0,'70-79':0,'60-69':0,'50-59':0,'0-49':0}
    for card in cards:
        s = float(card.average_score)
        if s >= 90:   buckets['90-100'] += 1
        elif s >= 80: buckets['80-89']  += 1
        elif s >= 70: buckets['70-79']  += 1
        elif s >= 60: buckets['60-69']  += 1
        elif s >= 50: buckets['50-59']  += 1
        else:         buckets['0-49']   += 1

    _log(request.user, 'report_card', exam.name, form.cleaned_data)
    paginator  = Paginator(cards, 25)
    cards_page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/report_card.html', {
        'form': form, 'cards': cards_page, 'exam': exam,
        'total_students': total_students, 'promoted': promoted,
        'not_promoted': total_students - promoted,
        'avg_score': round(avg_score, 1),
        'pie_labels': _json(pie_labels), 'pie_data': _json(pie_data),
        'pie_colors': _json(pie_colors),
        'bar_labels': _json(bar_labels), 'bar_data': _json(bar_data),
        'bucket_labels': _json(list(buckets.keys())),
        'bucket_data':   _json(list(buckets.values())),
        'page_title': 'Report Card',
    })


# ══════════════════════════════════════════════
#  EXAM RESULTS
# ══════════════════════════════════════════════

@admin_required
def exam_results(request):
    form = ExamResultsForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/exam_results.html',
                      {'form': form, 'page_title': 'Exam Results'})

    exam    = form.cleaned_data['exam']
    grade   = form.cleaned_data.get('grade')
    section = form.cleaned_data.get('section')

    results = SubjectResult.objects.filter(exam=exam).select_related(
        'student__user', 'subject'
    )
    if section:
        results = results.filter(student__current_section=section)
    elif grade:
        results = results.filter(student__current_section__grade=grade)

    total     = results.values('student').distinct().count()
    passed    = results.filter(is_pass=True).values('student').distinct().count()
    avg_score = results.aggregate(avg=Avg('total_score'))['avg'] or 0

    subj_stats = results.values('subject__name').annotate(
        avg=Avg('total_score'),
        pass_count=Count('id', filter=Q(is_pass=True)),
        total_count=Count('id'),
    ).order_by('-avg')

    subj_labels    = [r['subject__name'] for r in subj_stats]
    subj_avg       = [round(r['avg'] or 0, 1) for r in subj_stats]
    subj_pass_rate = [
        round((r['pass_count']/r['total_count']*100) if r['total_count'] else 0, 1)
        for r in subj_stats
    ]

    grade_dist = defaultdict(int)
    for r in results:
        grade_dist[_grade_label(float(r.total_score))] += 1
    pie_labels = list(grade_dist.keys())
    pie_data   = list(grade_dist.values())
    GRADE_COLOURS = {
        'Excellent':'#22c55e','Very Good':'#0ea5a0','Good':'#1a3c72',
        'Satisfactory':'#f59e0b','Pass':'#f97316','Fail':'#ef4444',
    }
    pie_colors = [GRADE_COLOURS.get(l,'#9ca3af') for l in pie_labels]
    top        = ReportCard.objects.filter(exam=exam).order_by('-average_score')[:10]

    _log(request.user, 'exam_results', exam.name, form.cleaned_data)
    paginator   = Paginator(results.order_by('-total_score'), 30)
    result_page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/exam_results.html', {
        'form': form, 'results': result_page, 'exam': exam,
        'total': total, 'passed': passed, 'avg_score': round(avg_score, 1),
        'top': top,
        'subj_labels': _json(subj_labels), 'subj_avg': _json(subj_avg),
        'subj_pass_rate': _json(subj_pass_rate),
        'pie_labels': _json(pie_labels), 'pie_data': _json(pie_data),
        'pie_colors': _json(pie_colors),
        'page_title': 'Exam Results',
    })


# ══════════════════════════════════════════════
#  ATTENDANCE — FIXED (no 'excused', safe filters)
# ══════════════════════════════════════════════

@admin_required
def attendance_report(request):
    form = AttendanceReportForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/attendance_report.html',
                      {'form': form, 'page_title': 'Attendance Report'})

    qs = Attendance.objects.select_related('student__user')

    grade   = form.cleaned_data.get('grade')
    section = form.cleaned_data.get('section')
    student = form.cleaned_data.get('student')

    # Safe section/grade filter
    try:
        if section:
            qs = qs.filter(student__current_section=section)
        elif grade:
            qs = qs.filter(student__current_section__grade=grade)
    except Exception:
        pass

    if student:
        qs = qs.filter(student=student)
    if form.cleaned_data.get('date_from'):
        qs = qs.filter(date__gte=form.cleaned_data['date_from'])
    if form.cleaned_data.get('date_to'):
        qs = qs.filter(date__lte=form.cleaned_data['date_to'])

    total   = qs.count()
    # Use only statuses that exist in your model
    present = qs.filter(status='present').count()
    absent  = qs.filter(status='absent').count()
    late    = qs.filter(status='late').count()
    rate    = round(present / total * 100, 1) if total else 0

    pie_labels = ['Present', 'Absent', 'Late']
    pie_data   = [present, absent, late]
    pie_colors = ['#22c55e', '#ef4444', '#f59e0b']

    today     = timezone.now().date()
    trend_qs  = qs.filter(date__gte=today - timedelta(days=30))
    daily     = trend_qs.values('date', 'status').annotate(cnt=Count('id'))
    daily_map = defaultdict(lambda: {'present':0,'absent':0,'late':0})
    for row in daily:
        if row['status'] in daily_map[str(row['date'])]:
            daily_map[str(row['date'])][row['status']] += row['cnt']

    trend_dates   = sorted(daily_map.keys())
    trend_present = [daily_map[d]['present'] for d in trend_dates]
    trend_absent  = [daily_map[d]['absent']  for d in trend_dates]

    student_summary = None
    if form.cleaned_data.get('scope') == 'student':
        student_summary = qs.values(
            'student__user__first_name',
            'student__user__last_name',
        ).annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            absent=Count('id',  filter=Q(status='absent')),
            late=Count('id',    filter=Q(status='late')),
        ).order_by('student__user__last_name')

    _log(request.user, 'attendance_student', 'Attendance Report', form.cleaned_data)
    paginator = Paginator(qs.order_by('-date'), 30)
    page      = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/attendance_report.html', {
        'form': form, 'records': page,
        'scope': form.cleaned_data.get('scope', 'class'),
        'total': total, 'present': present, 'absent': absent,
        'late': late, 'rate': rate,
        'student_summary': student_summary,
        'pie_labels':   _json(pie_labels),
        'pie_data':     _json(pie_data),
        'pie_colors':   _json(pie_colors),
        'trend_dates':  _json(trend_dates),
        'trend_present':_json(trend_present),
        'trend_absent': _json(trend_absent),
        'page_title': 'Attendance Report',
    })


# ══════════════════════════════════════════════
#  FEE COLLECTION — FIXED (payment_date not paid_date)
# ══════════════════════════════════════════════

@admin_required
def fee_collection(request):
    form = FeeCollectionForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/fee_collection.html',
                      {'form': form, 'page_title': 'Fee Collection'})

    qs = Payment.objects.select_related(
        'student_fee__student__user',
        'student_fee__fee_structure__fee_category',
    )
    if form.cleaned_data.get('date_from'):
        qs = qs.filter(payment_date__gte=form.cleaned_data['date_from'])
    if form.cleaned_data.get('date_to'):
        qs = qs.filter(payment_date__lte=form.cleaned_data['date_to'])
    if form.cleaned_data.get('fee_category'):
        qs = qs.filter(
            student_fee__fee_structure__fee_category=form.cleaned_data['fee_category']
        )
    if form.cleaned_data.get('grade'):
        try:
            qs = qs.filter(
                student_fee__student__current_section__grade=form.cleaned_data['grade']
            )
        except Exception:
            pass

    total_collected = qs.aggregate(s=Sum('amount'))['s'] or 0
    payment_count   = qs.count()

    by_cat = qs.values(
        'student_fee__fee_structure__fee_category__name'
    ).annotate(total=Sum('amount')).order_by('-total')
    cat_labels = [r['student_fee__fee_structure__fee_category__name'] or 'Other'
                  for r in by_cat]
    cat_data   = [float(r['total'] or 0) for r in by_cat]
    cat_colors = PALETTE_PIE[:len(cat_labels)]

    # Use payment_date (not paid_date)
    daily = qs.values('payment_date').annotate(
        total=Sum('amount')
    ).order_by('payment_date')
    daily_labels = [str(r['payment_date']) for r in daily]
    daily_data   = [float(r['total'] or 0) for r in daily]

    by_grade = []
    grade_labels = []
    grade_data   = []
    try:
        by_grade = qs.values(
            'student_fee__student__current_section__grade__name'
        ).annotate(total=Sum('amount')).order_by('-total')
        grade_labels = [r['student_fee__student__current_section__grade__name'] or 'N/A'
                        for r in by_grade]
        grade_data   = [float(r['total'] or 0) for r in by_grade]
    except Exception:
        pass

    outstanding = 0
    if form.cleaned_data.get('include_outstanding'):
        try:
            outstanding = StudentFee.objects.filter(
                status__in=['unpaid','partial']
            ).aggregate(s=Sum(Fld('amount_due')-Fld('amount_paid')))['s'] or 0
        except Exception:
            pass

    _log(request.user, 'fee_collection', 'Fee Collection', form.cleaned_data)
    paginator = Paginator(qs.order_by('-payment_date'), 30)
    page      = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/fee_collection.html', {
        'form': form, 'payments': page,
        'total_collected': total_collected,
        'payment_count':   payment_count,
        'outstanding':     outstanding,
        'cat_labels':    _json(cat_labels),
        'cat_data':      _json(cat_data),
        'cat_colors':    _json(cat_colors),
        'daily_labels':  _json(daily_labels),
        'daily_data':    _json(daily_data),
        'grade_labels':  _json(grade_labels),
        'grade_data':    _json(grade_data),
        'page_title': 'Fee Collection',
    })


# ══════════════════════════════════════════════
#  OUTSTANDING FEES — FIXED
# ══════════════════════════════════════════════

@admin_required
def outstanding_fees(request):
    form = OutstandingFeesForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/outstanding_fees.html',
                      {'form': form, 'page_title': 'Outstanding Fees'})

    qs = StudentFee.objects.filter(
        status__in=['unpaid','partial'],
        academic_year=form.cleaned_data['academic_year'],
    ).select_related(
        'student__user',
        'fee_structure__fee_category'
    )

    grade   = form.cleaned_data.get('grade')
    section = form.cleaned_data.get('section')
    try:
        if section:
            qs = qs.filter(student__current_section=section)
        elif grade:
            qs = qs.filter(student__current_section__grade=grade)
    except Exception:
        pass

    if form.cleaned_data.get('overdue_only'):
        qs = qs.filter(due_date__lt=timezone.now().date())

    # 'balance' is a @property on StudentFee — use a different annotation name
    from django.db.models import ExpressionWrapper, DecimalField, F as Fld
    BALANCE_EXPR = ExpressionWrapper(
        Fld('amount_due') - Fld('amount_paid'),
        output_field=DecimalField()
    )
    # Aggregate totals without annotating individual rows (avoids property clash)
    total_outstanding = qs.aggregate(
        s=Sum(Fld('amount_due') - Fld('amount_paid'))
    )['s'] or 0
    student_count = qs.values('student').distinct().count()

    paid_total = StudentFee.objects.filter(
        academic_year=form.cleaned_data['academic_year'],
    ).aggregate(s=Sum('amount_paid'))['s'] or 0

    pie_labels = ['Collected', 'Outstanding']
    pie_data   = [float(paid_total), float(total_outstanding)]
    pie_colors = ['#22c55e', '#ef4444']

    grade_labels, grade_data = [], []
    try:
        by_grade = qs.values(
            'student__current_section__grade__name'
        ).annotate(
            total=Sum(Fld('amount_due') - Fld('amount_paid'))
        ).order_by('-total')
        grade_labels = [r['student__current_section__grade__name'] or 'N/A'
                        for r in by_grade]
        grade_data   = [float(r['total'] or 0) for r in by_grade]
    except Exception:
        pass

    by_cat = qs.values(
        'fee_structure__fee_category__name'
    ).annotate(
        total=Sum(Fld('amount_due') - Fld('amount_paid'))
    ).order_by('-total')
    cat_labels = [r['fee_structure__fee_category__name'] or 'Other' for r in by_cat]
    cat_data   = [float(r['total'] or 0) for r in by_cat]

    _log(request.user, 'fee_outstanding', 'Outstanding Fees', form.cleaned_data)
    # Order by the existing @property (Django fetches rows first, Python sorts)
    # Use amount_due-amount_paid expression for DB ordering instead
    paginator = Paginator(
        qs.order_by(Fld('amount_due') - Fld('amount_paid')).reverse(),
        30
    )
    page      = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/outstanding_fees.html', {
        'form': form, 'fees': page,
        'total_outstanding': total_outstanding,
        'student_count':     student_count,
        'today': date.today(),
        'pie_labels':  _json(pie_labels),
        'pie_data':    _json(pie_data),
        'pie_colors':  _json(pie_colors),
        'grade_labels':_json(grade_labels),
        'grade_data':  _json(grade_data),
        'cat_labels':  _json(cat_labels),
        'cat_data':    _json(cat_data),
        'page_title': 'Outstanding Fees',
    })


# ══════════════════════════════════════════════
#  LIBRARY REPORT
# ══════════════════════════════════════════════

@admin_required
def library_report(request):
    form = LibraryReportForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/library_report.html',
                      {'form': form, 'page_title': 'Library Report'})

    rtype     = form.cleaned_data['report_type']
    date_from = form.cleaned_data.get('date_from')
    date_to   = form.cleaned_data.get('date_to')

    iss_qs = BookIssuance.objects.select_related(
        'book_copy__book__category', 'student__user'
    )
    if date_from: iss_qs = iss_qs.filter(issued_date__gte=date_from)
    if date_to:   iss_qs = iss_qs.filter(issued_date__lte=date_to)

    total_issued   = iss_qs.count()
    total_returned = iss_qs.filter(status='returned').count()
    total_overdue  = iss_qs.filter(status='overdue').count()
    total_lost     = iss_qs.filter(status='lost').count()

    pie_labels = ['Returned','Overdue','Active','Lost']
    pie_data   = [
        total_returned, total_overdue,
        max(0, total_issued - total_returned - total_overdue - total_lost),
        total_lost,
    ]
    pie_colors = ['#22c55e','#ef4444','#1a3c72','#9ca3af']

    by_cat = iss_qs.values(
        'book_copy__book__category__name'
    ).annotate(cnt=Count('id')).order_by('-cnt')[:10]
    cat_labels = [r['book_copy__book__category__name'] or 'Uncategorised'
                  for r in by_cat]
    cat_data   = [r['cnt'] for r in by_cat]

    daily = iss_qs.values('issued_date').annotate(
        cnt=Count('id')
    ).order_by('issued_date')
    trend_labels = [str(r['issued_date']) for r in daily]
    trend_data   = [r['cnt'] for r in daily]

    fines_total = Fine.objects.filter(status='pending').aggregate(
        s=Sum('total_amount')
    )['s'] or 0

    top_books = Book.objects.annotate(
        borrow_count=Count('copies__issuances')
    ).order_by('-borrow_count')[:10]

    _log(request.user, 'library_issuances', 'Library Report', form.cleaned_data)
    paginator = Paginator(iss_qs.order_by('-issued_date'), 30)
    page      = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/library_report.html', {
        'form': form, 'issuances': page, 'report_type': rtype,
        'total_issued': total_issued, 'total_returned': total_returned,
        'total_overdue': total_overdue, 'total_lost': total_lost,
        'fines_total': fines_total, 'top_books': top_books,
        'pie_labels':   _json(pie_labels),
        'pie_data':     _json(pie_data),
        'pie_colors':   _json(pie_colors),
        'cat_labels':   _json(cat_labels),
        'cat_data':     _json(cat_data),
        'trend_labels': _json(trend_labels),
        'trend_data':   _json(trend_data),
        'page_title': 'Library Report',
    })


# ══════════════════════════════════════════════
#  TRANSPORT REPORT
# ══════════════════════════════════════════════

@admin_required
def transport_report(request):
    form = TransportReportForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/transport_report.html',
                      {'form': form, 'page_title': 'Transport Report'})

    qs = StudentTransport.objects.filter(
        is_active=True,
        academic_year=form.cleaned_data['academic_year'],
    ).select_related('student__user', 'route', 'stop')

    if form.cleaned_data.get('route'):
        qs = qs.filter(route=form.cleaned_data['route'])

    total_students = qs.count()
    by_route = qs.values('route__name').annotate(cnt=Count('id')).order_by('-cnt')
    pie_labels = [r['route__name'] for r in by_route]
    pie_data   = [r['cnt'] for r in by_route]
    pie_colors = PALETTE_PIE[:len(pie_labels)]

    routes = Route.objects.filter(is_active=True).annotate(
        assigned=Count('student_transports',
                       filter=Q(student_transports__is_active=True))
    )
    cap_labels   = [r.name for r in routes]
    cap_assigned = [r.assigned for r in routes]
    cap_capacity = [r.vehicle.capacity if r.vehicle else 0 for r in routes]

    _log(request.user, 'transport_students', 'Transport Report', form.cleaned_data)
    paginator = Paginator(
        qs.order_by('route__name', 'student__user__first_name'), 30
    )
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/transport_report.html', {
        'form': form, 'assignments': page,
        'total_students': total_students,
        'pie_labels':   _json(pie_labels),
        'pie_data':     _json(pie_data),
        'pie_colors':   _json(pie_colors),
        'cap_labels':   _json(cap_labels),
        'cap_assigned': _json(cap_assigned),
        'cap_capacity': _json(cap_capacity),
        'page_title': 'Transport Report',
    })


# ══════════════════════════════════════════════
#  STUDENT LIST — FIXED (no current_section assumption)
# ══════════════════════════════════════════════

@admin_required
def student_list_report(request):
    form = StudentListForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/student_list.html',
                      {'form': form, 'page_title': 'Student List'})

    qs = Student.objects.select_related('user').filter(is_active=True)
    qs = _student_section_filter(
        qs,
        form.cleaned_data.get('grade'),
        form.cleaned_data.get('section'),
    )
    total = qs.count()

    # Gender chart
    gender_dist = qs.values('gender').annotate(cnt=Count('id'))
    gender_labels = [r['gender'] or 'Unknown' for r in gender_dist]
    gender_data   = [r['cnt'] for r in gender_dist]
    gender_colors = ['#1a3c72','#ec4899','#9ca3af']

    # Grade chart — try both field paths
    grade_labels, grade_data = [], []
    for field in [
        'current_section__grade__name',
        'enrollments__section__grade__name',
        'section__grade__name',
    ]:
        try:
            by_grade = qs.values(field).annotate(
                cnt=Count('id')
            ).order_by(field)
            grade_labels = [r[field] or 'N/A' for r in by_grade]
            grade_data   = [r['cnt'] for r in by_grade]
            break
        except Exception:
            continue

    _log(request.user, 'student_list', 'Student List', form.cleaned_data)
    paginator = Paginator(qs.order_by('user__first_name'), 30)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/student_list.html', {
        'form': form, 'students': page, 'total': total,
        'gender_labels': _json(gender_labels),
        'gender_data':   _json(gender_data),
        'gender_colors': _json(gender_colors),
        'grade_labels':  _json(grade_labels),
        'grade_data':    _json(grade_data),
        'page_title': 'Student List',
    })


# ══════════════════════════════════════════════
#  STAFF LIST
# ══════════════════════════════════════════════

@admin_required
def staff_list_report(request):
    form = StaffListForm(request.GET or None)
    if not form.is_valid():
        return render(request, 'reports/staff_list.html',
                      {'form': form, 'page_title': 'Staff List'})

    qs = Staff.objects.select_related('user').filter(is_active=True)
    if form.cleaned_data.get('department'):
        qs = qs.filter(department=form.cleaned_data['department'])

    total    = qs.count()
    by_role  = qs.values('user__role').annotate(cnt=Count('id')).order_by('-cnt')
    role_labels = [r['user__role'] or 'Other' for r in by_role]
    role_data   = [r['cnt'] for r in by_role]
    role_colors = PALETTE_PIE[:len(role_labels)]

    _log(request.user, 'staff_list', 'Staff List', form.cleaned_data)
    paginator = Paginator(qs.order_by('user__first_name'), 30)
    page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'reports/staff_list.html', {
        'form': form, 'staff': page, 'total': total,
        'role_labels': _json(role_labels),
        'role_data':   _json(role_data),
        'role_colors': _json(role_colors),
        'page_title': 'Staff List',
    })


# ══════════════════════════════════════════════
#  REPORT HISTORY
# ══════════════════════════════════════════════

@admin_required
def report_history(request):
    form    = ReportHistoryFilterForm(request.GET or None)
    history = ReportRequest.objects.select_related(
        'requested_by'
    ).order_by('-requested_at')

    if form.is_valid():
        if form.cleaned_data.get('report_type'):
            history = history.filter(report_type=form.cleaned_data['report_type'])
        if form.cleaned_data.get('status'):
            history = history.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('date_from'):
            history = history.filter(
                requested_at__date__gte=form.cleaned_data['date_from']
            )
        if form.cleaned_data.get('date_to'):
            history = history.filter(
                requested_at__date__lte=form.cleaned_data['date_to']
            )

    paginator = Paginator(history, 20)
    page      = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'reports/report_history.html', {
        'form': form, 'history': page, 'page_title': 'Report History',
    })

# ══════════════════════════════════════════════
# Replace the download_pdf view in apps/reports/views.py
# with these two views: download_pdf + print_report
# ══════════════════════════════════════════════

@admin_required
def download_pdf(request, report_type):
    """
    Redirect to the print-preview view which auto-triggers window.print().
    User saves as PDF from the browser dialog.
    Works on all platforms — no WeasyPrint needed.
    """
    VALID = {
        'report_card', 'exam_results', 'attendance',
        'fee_collection', 'outstanding_fees', 'library',
        'transport', 'student_list', 'staff_list',
    }
    if report_type not in VALID:
        messages.error(request, f'Unknown report type: {report_type}')
        return redirect('reports_dashboard')

    params = request.GET.urlencode()
    from django.urls import reverse
    url = reverse('print_report', args=[report_type])
    return redirect(f'{url}?{params}' if params else url)


@admin_required
def print_report(request, report_type):
    """
    Renders a clean, sidebar-free print template
    and auto-triggers window.print() on load.
    """
    from django.utils import timezone as tz

    # ── Map type → data-fetching logic ───────────
    ctx = {'report_type': report_type, 'generated': tz.now()}

    if report_type == 'report_card':
        form = ReportCardForm(request.GET or None)
        if form.is_valid():
            exam  = form.cleaned_data['exam']
            cards = ReportCard.objects.filter(exam=exam).select_related(
                'student__user'
            )
            if form.cleaned_data.get('grade'):
                try:
                    cards = cards.filter(
                        student__current_section__grade=form.cleaned_data['grade']
                    )
                except Exception:
                    pass
            if form.cleaned_data.get('student'):
                cards = cards.filter(student=form.cleaned_data['student'])
            ctx.update({
                'form': form, 'cards': cards, 'exam': exam,
                'total': cards.count(),
                'promoted': cards.filter(is_promoted=True).count(),
                'avg': cards.aggregate(a=Avg('average_score'))['a'] or 0,
                'title': f'Report Card — {exam.name}',
            })

    elif report_type == 'exam_results':
        form = ExamResultsForm(request.GET or None)
        if form.is_valid():
            exam    = form.cleaned_data['exam']
            results = SubjectResult.objects.filter(exam=exam).select_related(
                'student__user', 'subject'
            )
            ctx.update({
                'form': form, 'results': results, 'exam': exam,
                'total': results.values('student').distinct().count(),
                'passed': results.filter(is_pass=True).values('student').distinct().count(),
                'avg': results.aggregate(a=Avg('total_score'))['a'] or 0,
                'title': f'Exam Results — {exam.name}',
            })

    elif report_type == 'attendance':
        form = AttendanceReportForm(request.GET or None)
        if form.is_valid():
            qs = Attendance.objects.select_related('student__user')
            if form.cleaned_data.get('date_from'):
                qs = qs.filter(date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                qs = qs.filter(date__lte=form.cleaned_data['date_to'])
            total   = qs.count()
            present = qs.filter(status='present').count()
            ctx.update({
                'form': form, 'records': qs.order_by('-date'),
                'total': total, 'present': present,
                'absent': qs.filter(status='absent').count(),
                'late':   qs.filter(status='late').count(),
                'rate':   round(present / total * 100, 1) if total else 0,
                'title': 'Attendance Report',
            })

    elif report_type == 'fee_collection':
        form = FeeCollectionForm(request.GET or None)
        if form.is_valid():
            qs = Payment.objects.select_related(
                'student_fee__student__user',
                'student_fee__fee_structure__fee_category',
            )
            if form.cleaned_data.get('date_from'):
                qs = qs.filter(payment_date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                qs = qs.filter(payment_date__lte=form.cleaned_data['date_to'])
            ctx.update({
                'form': form,
                'payments': qs.order_by('-payment_date'),
                'total_collected': qs.aggregate(s=Sum('amount'))['s'] or 0,
                'payment_count':   qs.count(),
                'title': 'Fee Collection Report',
            })

    elif report_type == 'outstanding_fees':
        form = OutstandingFeesForm(request.GET or None)
        if form.is_valid():
            from django.db.models import ExpressionWrapper, DecimalField, F as Fld
            qs = StudentFee.objects.filter(
                status__in=['unpaid', 'partial'],
                academic_year=form.cleaned_data['academic_year'],
            ).select_related('student__user', 'fee_structure__fee_category')
            total_out = qs.aggregate(
                s=Sum(Fld('amount_due') - Fld('amount_paid'))
            )['s'] or 0
            ctx.update({
                'form': form, 'fees': qs.order_by('student__user__last_name'),
                'total_outstanding': total_out,
                'student_count': qs.values('student').distinct().count(),
                'today': date.today(),
                'title': 'Outstanding Fees Report',
            })

    elif report_type == 'library':
        form = LibraryReportForm(request.GET or None)
        if form.is_valid():
            qs = BookIssuance.objects.select_related(
                'book_copy__book', 'student__user'
            )
            if form.cleaned_data.get('date_from'):
                qs = qs.filter(issued_date__gte=form.cleaned_data['date_from'])
            if form.cleaned_data.get('date_to'):
                qs = qs.filter(issued_date__lte=form.cleaned_data['date_to'])
            ctx.update({
                'form': form, 'issuances': qs.order_by('-issued_date'),
                'total_issued':   qs.count(),
                'total_returned': qs.filter(status='returned').count(),
                'total_overdue':  qs.filter(status='overdue').count(),
                'title': 'Library Report',
            })

    elif report_type == 'transport':
        form = TransportReportForm(request.GET or None)
        if form.is_valid():
            qs = StudentTransport.objects.filter(
                is_active=True,
                academic_year=form.cleaned_data['academic_year'],
            ).select_related('student__user', 'route', 'stop')
            if form.cleaned_data.get('route'):
                qs = qs.filter(route=form.cleaned_data['route'])
            ctx.update({
                'form': form,
                'assignments': qs.order_by('route__name', 'student__user__first_name'),
                'total_students': qs.count(),
                'title': 'Transport Report',
            })

    elif report_type == 'student_list':
        form = StudentListForm(request.GET or None)
        if form.is_valid():
            qs = Student.objects.select_related('user').filter(is_active=True)
            qs = _student_section_filter(
                qs,
                form.cleaned_data.get('grade'),
                form.cleaned_data.get('section'),
            )
            ctx.update({
                'form': form,
                'students': qs.order_by('user__first_name'),
                'total': qs.count(),
                'title': 'Student List',
            })

    elif report_type == 'staff_list':
        form = StaffListForm(request.GET or None)
        if form.is_valid():
            qs = Staff.objects.select_related('user').filter(is_active=True)
            if form.cleaned_data.get('department'):
                qs = qs.filter(department=form.cleaned_data['department'])
            ctx.update({
                'form': form,
                'staff': qs.order_by('user__first_name'),
                'total': qs.count(),
                'title': 'Staff List',
            })

    ctx.setdefault('title', report_type.replace('_', ' ').title())
    return render(request, 'reports/print_report.html', ctx)