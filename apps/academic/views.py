
from django.shortcuts      import render, redirect, get_object_or_404
from django.contrib        import messages
from django.core.paginator import Paginator
from django.db.models      import Q, Count
from django.http           import JsonResponse
from django.urls import reverse

from apps.core.decorators  import admin_required, principal_or_above
from apps.core.models      import AcademicYear
from apps.accounts.models  import User
from .models               import Grade, Section, Subject, SubjectTeacher
from .timetable_models     import Period, Timetable
from .forms                import (
    GradeForm, SectionForm, SubjectForm,
    SubjectTeacherForm, PeriodForm, TimetableForm
)


# ══════════════════════════════════════════════
#  GRADE
# ══════════════════════════════════════════════

@admin_required
def grade_list(request):
    grades = Grade.objects.annotate(
        section_count=Count('sections'),
        subject_count=Count('subjects'),
    ).order_by('order')

    return render(request, 'academic/grade_list.html', {
        'grades':     grades,
        'page_title': 'Grades',
    })


@principal_or_above
def grade_create(request):
    form = GradeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        grade = form.save()
        messages.success(request, f'Grade "{grade.name}" created successfully.')
        return redirect('grade_list')
    return render(request, 'academic/grade_form.html', {
        'form':       form,
        'title':      'Create Grade',
        'page_title': 'Create Grade',
    })


@principal_or_above
def grade_edit(request, pk):
    grade = get_object_or_404(Grade, pk=pk)
    form  = GradeForm(request.POST or None, instance=grade)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Grade "{grade.name}" updated.')
        return redirect('grade_list')
    return render(request, 'academic/grade_form.html', {
        'form':       form,
        'title':      f'Edit — {grade.name}',
        'page_title': f'Edit Grade',
        'grade':      grade,
    })


@principal_or_above
def grade_delete(request, pk):
    grade = get_object_or_404(Grade, pk=pk)

    # Guard: cannot delete if sections/subjects exist
    if grade.sections.exists():
        messages.error(
            request,
            f'Cannot delete "{grade.name}" — '
            f'it has {grade.sections.count()} section(s). '
            f'Delete the sections first.'
        )
        return redirect('grade_list')
    if grade.subjects.exists():
        messages.error(
            request,
            f'Cannot delete "{grade.name}" — '
            f'it has {grade.subjects.count()} subject(s). '
            f'Delete the subjects first.'
        )
        return redirect('grade_list')

    if request.method == 'POST':
        name = grade.name
        grade.delete()
        messages.success(request, f'Grade "{name}" deleted.')
        return redirect('grade_list')

    return render(request, 'academic/confirm_delete.html', {
        'object':     grade,
        'title':      f'Delete Grade — {grade.name}',
        'page_title': 'Confirm Delete',
        'back_url':   'grade_list',
    })


# ══════════════════════════════════════════════
#  SECTION
# ══════════════════════════════════════════════

@admin_required
def section_list(request):
    sections = Section.objects.select_related(
        'grade', 'academic_year', 'class_teacher'
    ).annotate(
        student_count=Count('enrollments')
    ).order_by('grade__order', 'name')

    # Filter by grade
    grade_id = request.GET.get('grade', '')
    if grade_id:
        sections = sections.filter(grade_id=grade_id)

    # Filter by year
    year_id = request.GET.get('year', '')
    if year_id:
        sections = sections.filter(academic_year_id=year_id)
    else:
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            sections = sections.filter(academic_year=current)
            year_id  = str(current.pk)

    grades = Grade.objects.order_by('order')
    years  = AcademicYear.objects.order_by('-start_date')

    return render(request, 'academic/section_list.html', {
        'sections':  sections,
        'grades':    grades,
        'years':     years,
        'grade_id':  grade_id,
        'year_id':   year_id,
        'page_title': 'Sections',
    })


@principal_or_above
def section_create(request):
    form = SectionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        section = form.save()
        messages.success(
            request,
            f'Section "{section.grade} — {section.name}" created.'
        )
        return redirect('section_list')
    return render(request, 'academic/section_form.html', {
        'form':       form,
        'title':      'Create Section',
        'page_title': 'Create Section',
    })


@principal_or_above
def section_edit(request, pk):
    section = get_object_or_404(Section, pk=pk)
    form    = SectionForm(request.POST or None, instance=section)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Section "{section}" updated.')
        return redirect('section_list')
    return render(request, 'academic/section_form.html', {
        'form':       form,
        'title':      f'Edit — {section}',
        'page_title': 'Edit Section',
        'section':    section,
    })


@principal_or_above
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)

    enrolled = section.enrollments.filter(is_active=True).count()
    if enrolled:
        messages.error(
            request,
            f'Cannot delete "{section}" — '
            f'{enrolled} student(s) are currently enrolled. '
            f'Cancel their enrollments first.'
        )
        return redirect('section_list')

    if request.method == 'POST':
        label = str(section)
        section.delete()
        messages.success(request, f'Section "{label}" deleted.')
        return redirect('section_list')

    return render(request, 'academic/confirm_delete.html', {
        'object':     section,
        'title':      f'Delete Section — {section}',
        'page_title': 'Confirm Delete',
        'back_url':   'section_list',
    })


# ══════════════════════════════════════════════
#  SUBJECT
# ══════════════════════════════════════════════

@admin_required
def subject_list(request):
    subjects = Subject.objects.select_related('grade').order_by(
        'grade__order', 'name'
    )

    # Filter by grade
    grade_id = request.GET.get('grade', '')
    if grade_id:
        subjects = subjects.filter(grade_id=grade_id)

    # Filter by type
    subject_type = request.GET.get('type', '')
    if subject_type == 'core':
        subjects = subjects.filter(is_core=True)
    elif subject_type == 'elective':
        subjects = subjects.filter(is_core=False)

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        subjects = subjects.filter(
            Q(name__icontains=q) | Q(code__icontains=q)
        )

    grades = Grade.objects.order_by('order')

    return render(request, 'academic/subject_list.html', {
        'subjects':     subjects,
        'grades':       grades,
        'grade_id':     grade_id,
        'subject_type': subject_type,
        'q':            q,
        'page_title':   'Subjects',
    })


@principal_or_above
def subject_create(request):
    form = SubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subject = form.save()
        messages.success(
            request,
            f'Subject "{subject.name}" ({subject.code}) created.'
        )
        return redirect('subject_list')
    return render(request, 'academic/subject_form.html', {
        'form':       form,
        'title':      'Create Subject',
        'page_title': 'Create Subject',
    })


@principal_or_above
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form    = SubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Subject "{subject.name}" updated.')
        return redirect('subject_list')
    return render(request, 'academic/subject_form.html', {
        'form':       form,
        'title':      f'Edit — {subject.name}',
        'page_title': 'Edit Subject',
        'subject':    subject,
    })


@principal_or_above
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if SubjectTeacher.objects.filter(subject=subject).exists():
        messages.error(
            request,
            f'Cannot delete "{subject.name}" — it is assigned '
            f'to teachers. Remove those assignments first.'
        )
        return redirect('subject_list')

    if request.method == 'POST':
        name = subject.name
        subject.delete()
        messages.success(request, f'Subject "{name}" deleted.')
        return redirect('subject_list')

    return render(request, 'academic/confirm_delete.html', {
        'object':     subject,
        'title':      f'Delete Subject — {subject.name}',
        'page_title': 'Confirm Delete',
        'back_url':   'subject_list',
    })


# ══════════════════════════════════════════════
#  SUBJECT–TEACHER ASSIGNMENT
# ══════════════════════════════════════════════

@admin_required
def subject_teacher_list(request):
    assignments = SubjectTeacher.objects.select_related(
        'subject__grade', 'section', 'teacher', 'academic_year'
    ).order_by('academic_year', 'section__grade__order', 'section__name')

    # Filters
    year_id  = request.GET.get('year', '')
    grade_id = request.GET.get('grade', '')
    q        = request.GET.get('q', '').strip()

    if year_id:
        assignments = assignments.filter(academic_year_id=year_id)
    else:
        current = AcademicYear.objects.filter(is_current=True).first()
        if current:
            assignments = assignments.filter(academic_year=current)
            year_id = str(current.pk)

    if grade_id:
        assignments = assignments.filter(subject__grade_id=grade_id)

    if q:
        assignments = assignments.filter(
            Q(subject__name__icontains=q)           |
            Q(teacher__first_name__icontains=q)     |
            Q(teacher__last_name__icontains=q)      |
            Q(section__name__icontains=q)
        )

    years  = AcademicYear.objects.order_by('-start_date')
    grades = Grade.objects.order_by('order')

    return render(request, 'academic/subject_teacher_list.html', {
        'assignments': assignments,
        'years':       years,
        'grades':      grades,
        'year_id':     year_id,
        'grade_id':    grade_id,
        'q':           q,
        'page_title':  'Subject–Teacher Assignments',
    })


@principal_or_above
def subject_teacher_assign(request):
    form = SubjectTeacherForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        assignment = form.save()
        messages.success(
            request,
            f'"{assignment.subject}" assigned to '
            f'{assignment.teacher.get_full_name()} '
            f'in {assignment.section}.'
        )
        return redirect('subject_teacher_list')
    return render(request, 'academic/subject_teacher_form.html', {
        'form':       form,
        'title':      'Assign Subject to Teacher',
        'page_title': 'Assign Subject',
    })


@principal_or_above
def subject_teacher_edit(request, pk):
    assignment = get_object_or_404(SubjectTeacher, pk=pk)
    form       = SubjectTeacherForm(
        request.POST or None, instance=assignment
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Assignment updated successfully.')
        return redirect('subject_teacher_list')
    return render(request, 'academic/subject_teacher_form.html', {
        'form':       form,
        'title':      'Edit Assignment',
        'page_title': 'Edit Assignment',
        'assignment': assignment,
    })


@principal_or_above
def subject_teacher_delete(request, pk):
    assignment = get_object_or_404(SubjectTeacher, pk=pk)
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment removed successfully.')
        return redirect('subject_teacher_list')
    return render(request, 'academic/confirm_delete.html', {
        'object':     assignment,
        'title':      'Remove Assignment',
        'page_title': 'Confirm Delete',
        'back_url':   'subject_teacher_list',
    })


# ══════════════════════════════════════════════
#  PERIOD
# ══════════════════════════════════════════════

@admin_required
def period_list(request):
    periods = Period.objects.order_by('order')
    return render(request, 'academic/period_list.html', {
        'periods':    periods,
        'page_title': 'Periods',
    })


@principal_or_above
def period_create(request):
    form = PeriodForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        period = form.save()
        messages.success(request, f'Period "{period.name}" created.')
        return redirect('period_list')
    return render(request, 'academic/period_form.html', {
        'form':       form,
        'title':      'Create Period',
        'page_title': 'Create Period',
    })


@principal_or_above
def period_edit(request, pk):
    period = get_object_or_404(Period, pk=pk)
    form   = PeriodForm(request.POST or None, instance=period)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Period "{period.name}" updated.')
        return redirect('period_list')
    return render(request, 'academic/period_form.html', {
        'form':       form,
        'title':      f'Edit — {period.name}',
        'page_title': 'Edit Period',
        'period':     period,
    })


@principal_or_above
def period_delete(request, pk):
    period = get_object_or_404(Period, pk=pk)
    if Timetable.objects.filter(period=period).exists():
        messages.error(
            request,
            f'Cannot delete "{period.name}" — '
            f'it is used in timetable entries. '
            f'Remove those entries first.'
        )
        return redirect('period_list')
    if request.method == 'POST':
        name = period.name
        period.delete()
        messages.success(request, f'Period "{name}" deleted.')
        return redirect('period_list')
    return render(request, 'academic/confirm_delete.html', {
        'object':     period,
        'title':      f'Delete Period — {period.name}',
        'page_title': 'Confirm Delete',
        'back_url':   'period_list',
    })


# ══════════════════════════════════════════════
#  TIMETABLE
# ══════════════════════════════════════════════

@admin_required
def timetable_view(request):
    """Class timetable — shows full week grid for a section"""
    sections = Section.objects.select_related(
        'grade', 'academic_year'
    ).order_by('grade__order', 'name')

    current_year = AcademicYear.objects.filter(is_current=True).first()
    if current_year:
        sections = sections.filter(academic_year=current_year)

    section_id = request.GET.get('section', '')
    section    = None
    timetable  = {}
    periods    = Period.objects.order_by('order')

    DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI']

    if section_id:
        section = get_object_or_404(Section, pk=section_id)
        entries = Timetable.objects.filter(
            section=section,
            academic_year=current_year
        ).select_related('subject', 'teacher', 'period')

        # Build grid: {day: {period_id: entry}}
        for day in DAYS:
            timetable[day] = {}
            for period in periods:
                entry = entries.filter(day=day, period=period).first()
                timetable[day][period.pk] = entry

    return render(request, 'academic/timetable_view.html', {
        'sections':    sections,
        'section':     section,
        'section_id':  section_id,
        'timetable':   timetable,
        'periods':     periods,
        'days':        DAYS,
        'current_year': current_year,
        'page_title':  'Timetable',
    })


@principal_or_above
def timetable_entry_create(request):
    form = TimetableForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        entry = form.save()
        messages.success(
            request,
            f'Timetable entry added: {entry.subject} — '
            f'{entry.section} on {entry.day}.'
        )
        # return redirect(
        #     f"{{% url 'timetable_view' %}}?section={entry.section.pk}"
        # )
    # FIX: Generate the base URL using reverse() and append the section query parameter
        base_url = reverse('timetable_view')
        return redirect(f"{base_url}?section={entry.section.pk}")
    return render(request, 'academic/timetable_entry_form.html', {
        'form':       form,
        'title':      'Add Timetable Entry',
        'page_title': 'Add Timetable Entry',
    })


@principal_or_above
def timetable_entry_delete(request, pk):
    entry = get_object_or_404(Timetable, pk=pk)
    section_pk = entry.section.pk
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Timetable entry removed.')
        
        return redirect(f'/academic/timetable/?section={section_pk}')
    return render(request, 'academic/confirm_delete.html', {
        'object':     entry,
        'title':      'Remove Timetable Entry',
        'page_title': 'Confirm Delete',
        'back_url':   'timetable_view',
    })


# ══════════════════════════════════════════════
#  AJAX
# ══════════════════════════════════════════════

def ajax_subjects_by_grade(request):
    """Return subjects filtered by grade — used in forms"""
    grade_id = request.GET.get('grade_id', '')
    subjects = []
    if grade_id:
        subjects = list(
            Subject.objects.filter(grade_id=grade_id).values('id', 'name', 'code')
        )
    return JsonResponse({'subjects': subjects})


def ajax_sections_by_grade(request):
    """Return sections filtered by grade + current year"""
    grade_id = request.GET.get('grade_id', '')
    sections = []
    if grade_id:
        year = AcademicYear.objects.filter(is_current=True).first()
        qs   = Section.objects.filter(grade_id=grade_id)
        if year:
            qs = qs.filter(academic_year=year)
        sections = list(qs.values('id', 'name'))
    return JsonResponse({'sections': sections})