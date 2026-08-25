# apps/attendance/views.py

from django.shortcuts       import render, redirect, get_object_or_404
from django.contrib         import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator  import Paginator
from django.db.models       import Q, Count
from django.utils           import timezone
from django.http            import JsonResponse

from apps.core.decorators   import (
    admin_required, teacher_required, role_required
)
from apps.core.models       import AcademicYear
from apps.academic.models   import Section
from apps.students.models   import Student, Enrollment
from .models                import Attendance, AttendanceSummary
from .forms                 import (
    AttendanceDateForm, BulkAttendanceForm, AttendanceReportForm
)


# ══════════════════════════════════════════════
#  MARK ATTENDANCE  — Step 1: pick date+section
# ══════════════════════════════════════════════

@teacher_required
def attendance_select(request):
    form = AttendanceDateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        section = form.cleaned_data['section']
        date    = form.cleaned_data['date']
        return redirect(
            'attendance_mark',
            section_pk=section.pk,
            date_str=date.strftime('%Y-%m-%d')
        )

    return render(request, 'attendance/attendance_select.html', {
        'form':       form,
        'page_title': 'Mark Attendance',
    })


# ══════════════════════════════════════════════
#  MARK ATTENDANCE  — Step 2: bulk mark
# ══════════════════════════════════════════════

@teacher_required
def attendance_mark(request, section_pk, date_str):
    from datetime import date as date_type
    section      = get_object_or_404(Section, pk=section_pk)
    current_year = AcademicYear.objects.filter(is_current=True).first()

    # Parse date string
    try:
        mark_date = date_type.fromisoformat(date_str)
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect('attendance_select')

    # Validate date not in future
    if mark_date > timezone.now().date():
        messages.error(request, 'Cannot mark attendance for a future date.')
        return redirect('attendance_select')

    # Get enrolled students for this section
    enrollments = Enrollment.objects.filter(
        section=section,
        academic_year=current_year,
        is_active=True
    ).select_related('student__user').order_by(
        'student__user__first_name'
    )

    if not enrollments.exists():
        messages.warning(
            request,
            f'No active students enrolled in {section} '
            f'for {current_year}.'
        )
        return redirect('attendance_select')

    # Existing records for this date
    existing = {
        att.student_id: att
        for att in Attendance.objects.filter(
            section=section,
            date=mark_date
        )
    }

    already_marked = len(existing) > 0

    if request.method == 'POST':
        saved   = 0
        updated = 0

        for enr in enrollments:
            student    = enr.student
            status_key = f'status_{student.pk}'
            note_key   = f'note_{student.pk}'
            status     = request.POST.get(status_key, 'present')
            note       = request.POST.get(note_key, '').strip()

            # Validate status value
            valid_statuses = [s[0] for s in Attendance.STATUS_CHOICES]
            if status not in valid_statuses:
                status = 'present'

            obj, created = Attendance.objects.update_or_create(
                student=student,
                section=section,
                date=mark_date,
                defaults={
                    'status':        status,
                    'note':          note,
                    'academic_year': current_year,
                    'marked_by':     request.user,
                }
            )
            if created:
                saved += 1
            else:
                updated += 1

        messages.success(
            request,
            f'Attendance saved for {section} on '
            f'{mark_date.strftime("%b %d, %Y")} — '
            f'{saved} new, {updated} updated.'
        )
        return redirect(
            'attendance_mark',
            section_pk=section.pk,
            date_str=date_str
        )

    # ── Flat dicts for template — avoids filter errors ──
    existing_statuses = {
        student_id: att.status
        for student_id, att in existing.items()
    }
    existing_notes = {
        student_id: att.note
        for student_id, att in existing.items()
    }

    return render(request, 'attendance/attendance_mark.html', {
        'section':           section,
        'mark_date':         mark_date,
        'enrollments':       enrollments,
        'existing':          existing,
        'existing_statuses': existing_statuses,   # ← added
        'existing_notes':    existing_notes,       # ← added
        'already_marked':    already_marked,
        'current_year':      current_year,
        'statuses':          Attendance.STATUS_CHOICES,
        'page_title':        f'Attendance — {section} — {mark_date}',
    })
# ══════════════════════════════════════════════
#  ATTENDANCE LIST  — view/search records
# ══════════════════════════════════════════════

@admin_required
def attendance_list(request):
    records = Attendance.objects.select_related(
        'student__user', 'section__grade',
        'academic_year', 'marked_by'
    ).order_by('-date', 'student__user__first_name')

    # Filters
    section_id = request.GET.get('section', '')
    date_str   = request.GET.get('date',    '')
    status     = request.GET.get('status',  '')
    q          = request.GET.get('q',       '').strip()

    if section_id:
        records = records.filter(section_id=section_id)
    if date_str:
        records = records.filter(date=date_str)
    if status:
        records = records.filter(status=status)
    if q:
        records = records.filter(
            Q(student__user__first_name__icontains=q) |
            Q(student__user__last_name__icontains=q)  |
            Q(student__admission_number__icontains=q)
        )

    # Default to today
    if not date_str and not section_id and not q:
        records = records.filter(date=timezone.now().date())

    paginator = Paginator(records, 30)
    page      = request.GET.get('page', 1)
    records   = paginator.get_page(page)

    sections = Section.objects.select_related('grade').filter(
        academic_year__is_current=True
    ).order_by('grade__order', 'name')

    return render(request, 'attendance/attendance_list.html', {
        'records':    records,
        'sections':   sections,
        'statuses':   Attendance.STATUS_CHOICES,
        'section_id': section_id,
        'date_str':   date_str,
        'status':     status,
        'q':          q,
        'today':      timezone.now().date(),
        'page_title': 'Attendance Records',
    })


# ══════════════════════════════════════════════
#  ATTENDANCE REPORT  — summary by student
# ══════════════════════════════════════════════

@admin_required
def attendance_report(request):
    form    = AttendanceReportForm(request.GET or None)
    records = None
    summary = {}

    if form.is_valid():
        qs = Attendance.objects.select_related(
            'student__user', 'section__grade'
        )

        section   = form.cleaned_data.get('section')
        student   = form.cleaned_data.get('student')
        date_from = form.cleaned_data.get('date_from')
        date_to   = form.cleaned_data.get('date_to')
        status    = form.cleaned_data.get('status')

        if section:
            qs = qs.filter(section=section)
        if student:
            qs = qs.filter(student=student)
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if status:
            qs = qs.filter(status=status)

        records = qs.order_by('student__user__first_name', 'date')

        # Build per-student summary
        for r in records:
            sid = r.student_id
            if sid not in summary:
                summary[sid] = {
                    'student':  r.student,
                    'present':  0,
                    'absent':   0,
                    'late':     0,
                    'excused':  0,
                    'total':    0,
                }
            summary[sid][r.status] += 1
            summary[sid]['total']  += 1

        # Add percentage
        for sid, data in summary.items():
            total = data['total']
            data['percentage'] = (
                round((data['present'] / total) * 100, 1)
                if total else 0
            )
            data['at_risk'] = data['percentage'] < 75

    sections = Section.objects.select_related('grade').filter(
        academic_year__is_current=True
    ).order_by('grade__order', 'name')

    return render(request, 'attendance/attendance_report.html', {
        'form':       form,
        'records':    records,
        'summary':    summary.values() if summary else [],
        'sections':   sections,
        'page_title': 'Attendance Report',
    })


# ══════════════════════════════════════════════
#  STUDENT ATTENDANCE  — view own attendance
# ══════════════════════════════════════════════

@login_required
def my_attendance(request):
    """For student role — view their own attendance"""
    try:
        student = request.user.student
    except Exception:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    current_year = AcademicYear.objects.filter(is_current=True).first()

    records = Attendance.objects.filter(
        student=student,
        academic_year=current_year
    ).order_by('-date')

    # Summary
    total   = records.count()
    present = records.filter(status='present').count()
    absent  = records.filter(status='absent').count()
    late    = records.filter(status='late').count()
    excused = records.filter(status='excused').count()
    percentage = round((present / total) * 100, 1) if total else 0

    paginator = Paginator(records, 20)
    page      = request.GET.get('page', 1)
    records   = paginator.get_page(page)

    return render(request, 'attendance/my_attendance.html', {
        'records':     records,
        'total':       total,
        'present':     present,
        'absent':      absent,
        'late':        late,
        'excused':     excused,
        'percentage':  percentage,
        'current_year': current_year,
        'page_title':  'My Attendance',
    })


# ══════════════════════════════════════════════
#  AJAX — attendance stats for dashboard widget
# ══════════════════════════════════════════════

@admin_required
def ajax_today_stats(request):
    """Returns today's attendance stats as JSON"""
    today        = timezone.now().date()
    current_year = AcademicYear.objects.filter(is_current=True).first()

    records = Attendance.objects.filter(
        date=today,
        academic_year=current_year
    )
    total   = records.count()
    present = records.filter(status='present').count()
    absent  = records.filter(status='absent').count()
    late    = records.filter(status='late').count()

    return JsonResponse({
        'date':       str(today),
        'total':      total,
        'present':    present,
        'absent':     absent,
        'late':       late,
        'percentage': round((present / total) * 100, 1) if total else 0,
    })