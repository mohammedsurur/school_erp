from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .models import School, AcademicYear, Term, AuditLog
from .forms  import SchoolForm, AcademicYearForm, TermForm
from .decorators import admin_required, role_required


# ──────────────────────────────────────────────
#  Dashboard redirect
# ──────────────────────────────────────────────

@login_required
def dashboard_redirect(request):
    return redirect(request.user.get_dashboard_url())


# ──────────────────────────────────────────────
#  Role dashboards (shell — filled later)
# ──────────────────────────────────────────────

@login_required
@role_required('super_admin', 'principal', 'admin_staff', 'accountant', 'librarian')
def admin_dashboard(request):
    from apps.accounts.models import User
    context = {
        'page_title':      'Admin Dashboard',
        'total_students':  User.objects.filter(role='student').count(),
        'total_teachers':  User.objects.filter(role='teacher').count(),
        'total_classes':   0,   # filled after academic module
        'total_subjects':  0,
        'today_attendance': 0,
        'total_fees_collected': 0,
        'fees_pending':    0,
        'total_exams':     0,
        'recent_activities': [],
        'present_today':   0,
        'absent_today':    0,
        'late_today':      0,
        'absent_percent':  0,
        'late_percent':    0,
        'notices':         [],
    }
    return render(request, 'dashboard/admin.html', context)


@login_required
@role_required('teacher')
def teacher_dashboard(request):
    context = {
        'page_title':       'Teacher Dashboard',
        'greeting':         _greeting(),
        'classes_today':    0,
        'pending_marks':    0,
        'total_students':   0,
        'total_classes':    0,
        'attendance_today': 0,
        'my_classes':       [],
        'todays_timetable': [],
        'pending_tasks':    0,
        'attendance_done':  False,
        'notices':          [],
    }
    return render(request, 'dashboard/teacher.html', context)


@login_required
@role_required('student')
def student_dashboard(request):
    context = {
        'page_title':        'Student Dashboard',
        'student':           None,
        'total_subjects':    0,
        'attendance_percent': 0,
        'average_marks':     0,
        'fees_due':          0,
        'todays_timetable':  [],
        'recent_results':    [],
        'present_days':      0,
        'absent_days':       0,
        'late_days':         0,
        'fee_status':        [],
        'notices':           [],
    }
    return render(request, 'dashboard/student.html', context)


@login_required
@role_required('parent')
def parent_dashboard(request):
    context = {
        'page_title':        'Parent Dashboard',
        'children':          [],
        'selected_child':    None,
        'attendance_percent': 0,
        'average_marks':     0,
        'fees_due':          0,
        'total_subjects':    0,
        'present_days':      0,
        'absent_days':       0,
        'late_days':         0,
        'recent_results':    [],
        'todays_timetable':  [],
        'fee_status':        [],
        'notices':           [],
    }
    return render(request, 'dashboard/parent.html', context)


# ──────────────────────────────────────────────
#  School Info
# ──────────────────────────────────────────────

@admin_required
def school_setup(request):
    school = School.objects.first()
    form   = SchoolForm(
        request.POST  or None,
        request.FILES or None,
        instance=school
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'School information saved successfully.')
        return redirect('school_setup')

    return render(request, 'core/school_setup.html', {
        'form':        form,
        'school':      school,
        'page_title':  'School Setup',
    })


# ──────────────────────────────────────────────
#  Academic Year
# ──────────────────────────────────────────────

@admin_required
def academic_year_list(request):
    years = AcademicYear.objects.all().order_by('-start_date')
    return render(request, 'core/academic_year_list.html', {
        'years':      years,
        'page_title': 'Academic Years',
    })


@admin_required
def academic_year_create(request):
    form = AcademicYearForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        year = form.save()
        messages.success(request, f'Academic year "{year.name}" created.')
        return redirect('academic_year_list')

    return render(request, 'core/academic_year_form.html', {
        'form':       form,
        'title':      'Create Academic Year',
        'page_title': 'Create Academic Year',
    })


@admin_required
def academic_year_edit(request, pk):
    year = get_object_or_404(AcademicYear, pk=pk)
    form = AcademicYearForm(request.POST or None, instance=year)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Academic year "{year.name}" updated.')
        return redirect('academic_year_list')

    return render(request, 'core/academic_year_form.html', {
        'form':       form,
        'title':      f'Edit — {year.name}',
        'page_title': f'Edit — {year.name}',
        'year':       year,
    })


@admin_required
def academic_year_set_current(request, pk):
    year = get_object_or_404(AcademicYear, pk=pk)
    AcademicYear.objects.update(is_current=False)
    year.is_current = True
    year.save()
    messages.success(request, f'"{year.name}" is now the current academic year.')
    return redirect('academic_year_list')


@admin_required
def academic_year_delete(request, pk):
    year = get_object_or_404(AcademicYear, pk=pk)
    if year.is_current:
        messages.error(request, 'Cannot delete the current academic year.')
        return redirect('academic_year_list')
    if request.method == 'POST':
        name = year.name
        year.delete()
        messages.success(request, f'Academic year "{name}" deleted.')
        return redirect('academic_year_list')
    return render(request, 'core/confirm_delete.html', {
        'object':     year,
        'title':      f'Delete Academic Year — {year.name}',
        'page_title': 'Confirm Delete',
        'cancel_url': 'academic_year_list',
    })


# ──────────────────────────────────────────────
#  Term
# ──────────────────────────────────────────────

@admin_required
def term_list(request):
    # Filter by academic year if passed
    year_id = request.GET.get('year', '')
    terms   = Term.objects.select_related('academic_year').order_by(
                  '-academic_year__start_date', 'name'
              )
    years   = AcademicYear.objects.all().order_by('-start_date')

    if year_id:
        terms = terms.filter(academic_year_id=year_id)

    return render(request, 'core/term_list.html', {
        'terms':        terms,
        'years':        years,
        'selected_year': year_id,
        'page_title':   'Terms',
    })


@admin_required
def term_create(request):
    form = TermForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        term = form.save()
        messages.success(request, f'Term "{term}" created.')
        return redirect('term_list')

    return render(request, 'core/term_form.html', {
        'form':       form,
        'title':      'Create Term',
        'page_title': 'Create Term',
    })


@admin_required
def term_edit(request, pk):
    term = get_object_or_404(Term, pk=pk)
    form = TermForm(request.POST or None, instance=term)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Term "{term}" updated.')
        return redirect('term_list')

    return render(request, 'core/term_form.html', {
        'form':       form,
        'title':      f'Edit — {term}',
        'page_title': f'Edit — {term}',
        'term':       term,
    })


@admin_required
def term_set_current(request, pk):
    term = get_object_or_404(Term, pk=pk)
    Term.objects.filter(
        academic_year=term.academic_year
    ).update(is_current=False)
    term.is_current = True
    term.save()
    messages.success(request, f'"{term}" is now the current term.')
    return redirect('term_list')


@admin_required
def term_delete(request, pk):
    term = get_object_or_404(Term, pk=pk)
    if term.is_current:
        messages.error(request, 'Cannot delete the current term.')
        return redirect('term_list')
    if request.method == 'POST':
        label = str(term)
        term.delete()
        messages.success(request, f'Term "{label}" deleted.')
        return redirect('term_list')
    return render(request, 'core/confirm_delete.html', {
        'object':     term,
        'title':      f'Delete Term — {term}',
        'page_title': 'Confirm Delete',
        'cancel_url': 'term_list',
    })


# ──────────────────────────────────────────────
#  Audit Log
# ──────────────────────────────────────────────

@admin_required
def audit_log_list(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')

    # Filters
    action     = request.GET.get('action', '')
    model_name = request.GET.get('model', '')
    q          = request.GET.get('q', '')

    if action:
        logs = logs.filter(action=action)
    if model_name:
        logs = logs.filter(model_name__icontains=model_name)
    if q:
        logs = logs.filter(user__username__icontains=q)

    paginator = Paginator(logs, 30)
    page      = request.GET.get('page', 1)
    logs      = paginator.get_page(page)

    actions = AuditLog.objects.values_list('action', flat=True).distinct()

    return render(request, 'core/audit_log.html', {
        'logs':        logs,
        'actions':     actions,
        'action':      action,
        'model_name':  model_name,
        'q':           q,
        'page_title':  'Audit Log',
    })


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _greeting():
    from datetime import datetime
    hour = datetime.now().hour
    if hour < 12:  return 'Morning'
    if hour < 17:  return 'Afternoon'
    return 'Evening'