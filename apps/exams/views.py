# apps/exams/views.py

from django.shortcuts        import render, redirect, get_object_or_404
from django.contrib          import messages
from django.contrib.auth.decorators import login_required
from django.db               import IntegrityError
from django.db.models        import Avg, Count

from apps.core.decorators    import (
    admin_required, principal_or_above, teacher_required
)
from apps.students.models    import Student, Enrollment
from .models                 import (
    Exam, ExamSchedule, ExamComponent,
    ComponentResult, SubjectResult, ReportCard
)
from .forms                  import (
    ExamForm, ExamScheduleForm, ExamComponentForm,
    ComponentResultEntryForm, ReportCardRemarksForm
)


# ══════════════════════════════════════════════
#  EXAM CRUD
# ══════════════════════════════════════════════

@login_required
def exam_list(request):
    exams = Exam.objects.select_related(
        'grade', 'academic_year', 'term'
    ).annotate(
        schedule_count=Count('schedules')
    ).order_by('-start_date')

    return render(request, 'exams/exam_list.html', {
        'exams':      exams,
        'page_title': 'Exams',
    })


@principal_or_above
def exam_create(request):
    form = ExamForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        exam            = form.save(commit=False)
        exam.created_by = request.user
        exam.save()
        messages.success(request, f'Exam "{exam.name}" created.')
        return redirect('exam_detail', pk=exam.pk)
    return render(request, 'exams/exam_form.html', {
        'form':       form,
        'title':      'Create Exam',
        'page_title': 'Create Exam',
    })


# apps/exams/views.py

@login_required
def exam_detail(request, pk):
    exam = get_object_or_404(
        Exam.objects.select_related('grade', 'academic_year', 'term'),
        pk=pk
    )
    schedules = exam.schedules.select_related(
        'subject', 'section'
    ).prefetch_related('components').order_by('exam_date', 'start_time')

    schedule_info = []
    for sch in schedules:
        comp_total   = sum(c.max_marks for c in sch.components.all())
        result_count = sch.subject_results.count()
        enr_count    = Enrollment.objects.filter(
            section=sch.section,
            academic_year=exam.academic_year,
            is_active=True
        ).count()
        schedule_info.append({
            'schedule':     sch,
            'comp_total':   comp_total,
            'comp_ready':   comp_total == 100,
            'result_count': result_count,
            'enr_count':    enr_count,
        })

    return render(request, 'exams/exam_detail.html', {
        'exam':          exam,
        'schedule_info': schedule_info,
        'page_title':    exam.name,
    })
@principal_or_above
def exam_edit(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    form = ExamForm(request.POST or None, instance=exam)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Exam "{exam.name}" updated.')
        return redirect('exam_detail', pk=exam.pk)
    return render(request, 'exams/exam_form.html', {
        'form':       form,
        'exam':       exam,
        'title':      f'Edit — {exam.name}',
        'page_title': 'Edit Exam',
    })


@principal_or_above
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        name = exam.name
        exam.delete()
        messages.success(request, f'Exam "{name}" deleted.')
        return redirect('exam_list')
    return render(request, 'exams/confirm_delete.html', {
        'object':   exam,
        'title':    f'Delete Exam — {exam.name}',
        'back_url': f'/exams/{pk}/',
    })


@principal_or_above
def exam_publish_toggle(request, pk):
    exam             = get_object_or_404(Exam, pk=pk)
    exam.is_published = not exam.is_published
    exam.save()
    state = 'published' if exam.is_published else 'unpublished'
    messages.success(request, f'Exam "{exam.name}" {state}.')
    return redirect('exam_detail', pk=exam.pk)


# ══════════════════════════════════════════════
#  EXAM SCHEDULE CRUD
# ══════════════════════════════════════════════

@principal_or_above
def schedule_create(request, exam_pk):
    exam = get_object_or_404(Exam, pk=exam_pk)
    form = ExamScheduleForm(request.POST or None, exam=exam)

    if request.method == 'POST' and form.is_valid():
        try:
            schedule      = form.save(commit=False)
            schedule.exam = exam
            schedule.save()
            messages.success(
                request,
                f'"{schedule.subject}" scheduled for '
                f'{schedule.section} on {schedule.exam_date}.'
            )
            return redirect('exam_detail', pk=exam.pk)
        except IntegrityError:
            messages.error(
                request,
                'This subject is already scheduled for that section. '
                'Choose a different subject or section.'
            )

    return render(request, 'exams/schedule_form.html', {
        'form':       form,
        'exam':       exam,
        'title':      f'Add Schedule — {exam.name}',
        'page_title': 'Add Exam Schedule',
    })


@principal_or_above
def schedule_delete(request, pk):
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    exam_pk  = schedule.exam.pk
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted.')
        return redirect('exam_detail', pk=exam_pk)
    return render(request, 'exams/confirm_delete.html', {
        'object':   schedule,
        'title':    'Delete Schedule',
        'back_url': f'/exams/{exam_pk}/',
    })


# ══════════════════════════════════════════════
#  EXAM COMPONENTS
#  Define Quiz/Mid/Final/Assignment/Attendance
#  for a schedule — must sum to exactly 100
# ══════════════════════════════════════════════

@principal_or_above
def component_list(request, schedule_pk):
    schedule   = get_object_or_404(
        ExamSchedule.objects.select_related('exam', 'subject', 'section'),
        pk=schedule_pk
    )
    components = schedule.components.order_by('order')
    total      = sum(c.max_marks for c in components)
    remaining  = 100 - total

    return render(request, 'exams/component_list.html', {
        'schedule':   schedule,
        'components': components,
        'total':      total,
        'remaining':  remaining,
        'is_complete': total == 100,
        'page_title': f'Components — {schedule.subject}',
    })


@principal_or_above
def component_add(request, schedule_pk):
    schedule = get_object_or_404(ExamSchedule, pk=schedule_pk)
    form     = ExamComponentForm(
        request.POST or None,
        exam_schedule=schedule
    )

    if request.method == 'POST' and form.is_valid():
        component               = form.save(commit=False)
        component.exam_schedule = schedule
        component.save()

        total = sum(
            c.max_marks for c in schedule.components.all()
        )
        messages.success(
            request,
            f'{component.get_component_type_display()} '
            f'({component.max_marks} marks) added. '
            f'Total: {total}/100.'
        )
        if total == 100:
            messages.success(
                request,
                '✅ Components sum to 100 — ready for result entry!'
            )
        return redirect('component_list', schedule_pk=schedule.pk)

    # Show current components + remaining
    components = schedule.components.order_by('order')
    total      = sum(c.max_marks for c in components)

    return render(request, 'exams/component_form.html', {
        'form':       form,
        'schedule':   schedule,
        'components': components,
        'total':      total,
        'remaining':  100 - total,
        'title':      f'Add Component — {schedule.subject}',
        'page_title': 'Add Exam Component',
    })


@principal_or_above
def component_delete(request, pk):
    component   = get_object_or_404(ExamComponent, pk=pk)
    schedule_pk = component.exam_schedule.pk

    if component.results.exists():
        messages.error(
            request,
            f'Cannot delete — results already entered for '
            f'{component.get_component_type_display()}. '
            f'Delete the results first.'
        )
        return redirect('component_list', schedule_pk=schedule_pk)

    if request.method == 'POST':
        label = component.get_component_type_display()
        component.delete()
        messages.success(request, f'{label} component deleted.')
        return redirect('component_list', schedule_pk=schedule_pk)

    return render(request, 'exams/confirm_delete.html', {
        'object':   component,
        'title':    f'Delete — {component.get_component_type_display()}',
        'back_url': f'/exams/schedule/{schedule_pk}/components/',
    })


# ══════════════════════════════════════════════
#  RESULT ENTRY
#  Enter student marks per component
# ══════════════════════════════════════════════

@teacher_required
def result_entry(request, schedule_pk):
    """
    Bulk result entry — one row per enrolled student.
    Shows a column per component (Quiz / Mid / Final / etc.)
    Saves ComponentResult per student per component.
    Recomputes SubjectResult totals after save.
    """
    schedule = get_object_or_404(
        ExamSchedule.objects.select_related(
            'exam', 'subject', 'section'
        ).prefetch_related('components'),
        pk=schedule_pk
    )

    components = list(schedule.components.order_by('order'))

    if not components:
        messages.warning(
            request,
            'No components defined yet. '
            'Add components (Quiz, Mid-Term, etc.) before entering results.'
        )
        return redirect('component_list', schedule_pk=schedule.pk)

    comp_total = sum(c.max_marks for c in components)
    if comp_total != 100:
        messages.warning(
            request,
            f'Components only sum to {comp_total}/100. '
            f'Add the remaining {100 - comp_total} marks before entering results.'
        )

    # Active enrolled students for this section
    enrollments = Enrollment.objects.filter(
        section=schedule.section,
        academic_year=schedule.exam.academic_year,
        is_active=True
    ).select_related('student__user').order_by(
        'student__user__first_name',
        'student__user__last_name'
    )

    # Existing results: {student_pk: {comp_pk: ComponentResult}}
    existing = {}
    for enr in enrollments:
        comp_results = ComponentResult.objects.filter(
            student=enr.student,
            component__exam_schedule=schedule
        ).select_related('component')
        existing[enr.student.pk] = {
            cr.component.pk: cr for cr in comp_results
        }

    if request.method == 'POST':
        errors  = []
        saved   = 0
        skipped = 0

        for enr in enrollments:
            student   = enr.student
            is_absent = f'absent_{student.pk}' in request.POST

            for comp in components:
                key = f'marks_{student.pk}_{comp.pk}'
                raw = request.POST.get(key, '').strip()

                # ── KEY FIX ──────────────────────────────────────
                # If input is empty AND student is not marked absent,
                # skip this cell entirely — do NOT overwrite existing
                # data with zero. This means editing one student never
                # touches the other students' saved results.
                if raw == '' and not is_absent:
                    skipped += 1
                    continue
                # ─────────────────────────────────────────────────

                try:
                    marks = 0.0 if is_absent else float(raw)
                except ValueError:
                    errors.append(
                        f'{student.user.get_full_name()}: '
                        f'Invalid marks for '
                        f'{comp.get_component_type_display()}.'
                    )
                    continue

                # Clamp to component max
                marks = max(0.0, min(float(comp.max_marks), marks))

                ComponentResult.objects.update_or_create(
                    student=student,
                    component=comp,
                    defaults={
                        'marks_obtained': marks,
                        'is_absent':      is_absent,
                        'entered_by':     request.user,
                    }
                )
                saved += 1

            # Always recompute subject total for this student
            # so existing results stay reflected in SubjectResult
            _recompute_subject_result(student, schedule, request.user)

        # Recompute all report cards for this section
        _recompute_report_cards(schedule)

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            messages.success(
                request,
                f'Results updated — '
                f'{saved} mark{"s" if saved != 1 else ""} saved'
                f'{f", {skipped} unchanged" if skipped else ""}.'
            )
        return redirect('result_list', schedule_pk=schedule.pk)

    # ── Build flat dict for JS pre-fill ──────────────────
    # Format: { "studentpk_comppk": marks_obtained }
    # Used by the EXISTING JS block in the template
    existing_js = {}
    for student_pk, comp_map in existing.items():
        for comp_pk, cr in comp_map.items():
            existing_js[f'{student_pk}_{comp_pk}'] = {
                'marks':  float(cr.marks_obtained),
                'absent': cr.is_absent,
            }

    return render(request, 'exams/result_entry.html', {
        'schedule':     schedule,
        'exam':         schedule.exam,
        'components':   components,
        'enrollments':  enrollments,
        'existing':     existing,
        'existing_js':  existing_js,
        'comp_total':   comp_total,
        'page_title':   f'Enter Results — {schedule.subject}',
    })

def _recompute_subject_result(student, schedule, user=None):
    """
    Compute or update SubjectResult for one student + schedule.
    total_score = sum of all ComponentResult marks
    """
    sr, _ = SubjectResult.objects.get_or_create(
        student=student,
        exam_schedule=schedule,
        defaults={'entered_by': user}
    )
    sr.compute()


def _recompute_report_cards(schedule):
    """
    After results are saved for a schedule, recompute all
    ReportCards for the exam + section.
    """
    enrollments = Enrollment.objects.filter(
        section=schedule.section,
        academic_year=schedule.exam.academic_year,
        is_active=True
    ).select_related('student')

    for enr in enrollments:
        rc, _ = ReportCard.objects.get_or_create(
            student=enr.student,
            exam=schedule.exam,
            defaults={
                'section':       schedule.section,
                'academic_year': schedule.exam.academic_year,
            }
        )
        rc.compute()

    # Assign class ranks
    rcs = ReportCard.objects.filter(
        exam=schedule.exam,
        section=schedule.section,
    ).order_by('-overall_average')

    for rank, rc in enumerate(rcs, start=1):
        ReportCard.objects.filter(pk=rc.pk).update(rank=rank)


# ══════════════════════════════════════════════
#  RESULT LIST
# ══════════════════════════════════════════════

@login_required
def result_list(request, schedule_pk):
    schedule = get_object_or_404(
        ExamSchedule.objects.select_related(
            'exam', 'subject', 'section'
        ).prefetch_related('components'),
        pk=schedule_pk
    )
    components  = list(schedule.components.order_by('order'))

    # All subject results for this schedule, ranked
    results = SubjectResult.objects.filter(
        exam_schedule=schedule
    ).select_related(
        'student__user'
    ).order_by('-total_score')

    # Attach component breakdown per student
    # {student_pk: {comp_pk: ComponentResult}}
    comp_data = {}
    student_pks = [sr.student.pk for sr in results]
    crs = ComponentResult.objects.filter(
        student__pk__in=student_pks,
        component__exam_schedule=schedule
    ).select_related('component')

    for cr in crs:
        comp_data.setdefault(cr.student.pk, {})[cr.component.pk] = cr

    # Summary stats
    passed  = sum(1 for r in results if r.is_pass)
    failed  = sum(1 for r in results if not r.is_pass and not r.is_absent)
    absent  = sum(1 for r in results if r.is_absent)
    scores  = [float(r.total_score) for r in results if not r.is_absent]
    avg     = round(sum(scores) / len(scores), 1) if scores else 0

    return render(request, 'exams/result_list.html', {
        'schedule':   schedule,
        'exam':       schedule.exam,
        'components': components,
        'results':    results,
        'comp_data':  comp_data,
        'passed':     passed,
        'failed':     failed,
        'absent':     absent,
        'avg':        avg,
        'total':      len(results),
        'page_title': f'Results — {schedule.subject}',
    })


# ══════════════════════════════════════════════
#  REPORT CARDS
# ══════════════════════════════════════════════

@login_required
def report_card_list(request, exam_pk):
    exam = get_object_or_404(
        Exam.objects.select_related('grade', 'academic_year'),
        pk=exam_pk
    )

    section_id = request.GET.get('section', '')

    report_cards = ReportCard.objects.filter(
        exam=exam
    ).select_related(
        'student__user', 'section'
    ).order_by('section', '-overall_average')

    if section_id:
        report_cards = report_cards.filter(section__pk=section_id)

    # Sections that have report cards
    sections = exam.grade.sections.filter(
        exam_schedules__exam=exam
    ).distinct()

    return render(request, 'exams/report_card_list.html', {
        'exam':         exam,
        'report_cards': report_cards,
        'sections':     sections,
        'section_id':   section_id,
        'page_title':   f'Report Cards — {exam.name}',
    })


@login_required
def report_card_detail(request, pk):
    rc = get_object_or_404(
        ReportCard.objects.select_related(
            'student__user', 'exam', 'section', 'academic_year'
        ),
        pk=pk
    )

    # All subject results for this student in this exam
    subject_results = SubjectResult.objects.filter(
        student=rc.student,
        exam_schedule__exam=rc.exam,
        exam_schedule__section=rc.section,
    ).select_related(
        'exam_schedule__subject'
    ).order_by('exam_schedule__subject__name')

    # Component breakdown per subject result
    comp_data = {}
    for sr in subject_results:
        components = sr.exam_schedule.components.order_by('order')
        crs        = ComponentResult.objects.filter(
            student=rc.student,
            component__exam_schedule=sr.exam_schedule
        ).select_related('component')
        comp_data[sr.exam_schedule.pk] = {
            'components': list(components),
            'results':    {cr.component.pk: cr for cr in crs},
        }

    # Remarks form
    form = ReportCardRemarksForm(request.POST or None, instance=rc)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Remarks saved.')
        return redirect('report_card_detail', pk=rc.pk)

    # School info for header
    from apps.core.models import School
    school = School.objects.first()

    return render(request, 'exams/report_card_detail.html', {
        'rc':             rc,
        'subject_results': subject_results,
        'comp_data':      comp_data,
        'form':           form,
        'school':         school,
        'page_title':     f'Report Card — {rc.student.user.get_full_name()}',
    })


# ══════════════════════════════════════════════
#  STUDENT: MY RESULTS
# ══════════════════════════════════════════════

@login_required
def my_results(request):
    try:
        student = request.user.student
    except Exception:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    from apps.core.models import AcademicYear
    current_year = AcademicYear.objects.filter(is_current=True).first()

    # Only published report cards
    report_cards = ReportCard.objects.filter(
        student=student,
        exam__is_published=True,
        academic_year=current_year,
    ).select_related(
        'exam__grade', 'exam__academic_year', 'section'
    ).order_by('-exam__start_date')

    # Per report card: subject results + component breakdown
    rc_data = []
    for rc in report_cards:
        subject_results = SubjectResult.objects.filter(
            student=student,
            exam_schedule__exam=rc.exam,
            exam_schedule__section=rc.section,
        ).select_related(
            'exam_schedule__subject'
        ).order_by('exam_schedule__subject__name')

        comp_data = {}
        for sr in subject_results:
            crs = ComponentResult.objects.filter(
                student=student,
                component__exam_schedule=sr.exam_schedule
            ).select_related('component').order_by('component__order')
            comp_data[sr.pk] = list(crs)

        rc_data.append({
            'rc':             rc,
            'subject_results': subject_results,
            'comp_data':      comp_data,
        })

    return render(request, 'exams/my_results.html', {
        'student':      student,
        'rc_data':      rc_data,
        'current_year': current_year,
        'page_title':   'My Results',
    })