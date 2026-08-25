from django.shortcuts import render

# Create your views here.
from django.shortcuts   import render, redirect, get_object_or_404
from django.contrib          import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator   import Paginator
from django.http             import HttpResponse, JsonResponse
from django.template.loader  import get_template
from django.db.models        import Q, Count

from apps.core.decorators    import admin_required, role_required
from apps.core.models        import AcademicYear
from apps.academic.models    import Grade, Section
from .models                 import Student, Parent, Enrollment
from .forms                  import (
    StudentUserForm, StudentProfileForm, StudentEditForm,
    ParentForm, EnrollmentForm, BulkEnrollmentForm
)


# ─────────────────────────────────────────────
#  Student List
# ─────────────────────────────────────────────

@admin_required
def student_list(request):
    students = Student.objects.select_related(
        'user'
    ).prefetch_related(
        'enrollments__section__grade'
    ).order_by('-user__date_joined')

    # ── Search ──
    q = request.GET.get('q', '').strip()
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q)  |
            Q(user__last_name__icontains=q)   |
            Q(admission_number__icontains=q)  |
            Q(user__email__icontains=q)
        )

    # ── Filter by grade ──
    grade_id = request.GET.get('grade', '')
    if grade_id:
        students = students.filter(
            enrollments__section__grade_id=grade_id,
            enrollments__is_active=True
        )

    # ── Filter by status ──
    status = request.GET.get('status', '')
    if status == 'active':
        students = students.filter(is_active=True)
    elif status == 'inactive':
        students = students.filter(is_active=False)

    # ── Paginate ──
    paginator = Paginator(students.distinct(), 20)
    page      = request.GET.get('page', 1)
    students  = paginator.get_page(page)

    grades = Grade.objects.all().order_by('order')

    return render(request, 'students/student_list.html', {
        'students':     students,
        'grades':       grades,
        'q':            q,
        'grade_id':     grade_id,
        'status':       status,
        'page_title':   'Students',
    })


# ─────────────────────────────────────────────
#  Add Student (2-step: user account → profile)
# ─────────────────────────────────────────────

@admin_required
def student_create(request):
    user_form    = StudentUserForm(request.POST or None)
    profile_form = StudentProfileForm(request.POST or None, request.FILES or None)

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            # Step 1 — create user account
            user = user_form.save()

            # Step 2 — create student profile
            student                  = profile_form.save(commit=False)
            student.user             = user
            student.admission_number = Student.generate_admission_number()
            student.save()

            messages.success(
                request,
                f'Student "{user.get_full_name()}" added. '
                f'Admission No: {student.admission_number}'
            )
            return redirect('student_detail', pk=student.pk)
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'students/student_form.html', {
        'user_form':    user_form,
        'profile_form': profile_form,
        'title':        'Add New Student',
        'page_title':   'Add Student',
    })


# ─────────────────────────────────────────────
#  Student Detail
# ─────────────────────────────────────────────

@admin_required
def student_detail(request, pk):
    student    = get_object_or_404(
        Student.objects.select_related('user'),
        pk=pk
    )
    enrollments = student.enrollments.select_related(
        'section__grade', 'academic_year'
    ).order_by('-academic_year__start_date')

    parents = student.parents.select_related('user').all()

    # Current enrollment
    current_year       = AcademicYear.objects.filter(is_current=True).first()
    current_enrollment = enrollments.filter(
        academic_year=current_year, is_active=True
    ).first() if current_year else None

    return render(request, 'students/student_detail.html', {
        'student':            student,
        'enrollments':        enrollments,
        'parents':            parents,
        'current_enrollment': current_enrollment,
        'current_year':       current_year,
        'page_title':         f'{student.user.get_full_name()} — Profile',
    })


# ─────────────────────────────────────────────
#  Edit Student
# ─────────────────────────────────────────────

@admin_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form    = StudentEditForm(
        request.POST   or None,
        request.FILES  or None,
        instance=student
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request,
            f'Student "{student.user.get_full_name()}" updated successfully.'
        )
        return redirect('student_detail', pk=student.pk)

    return render(request, 'students/student_edit.html', {
        'form':       form,
        'student':    student,
        'title':      f'Edit — {student.user.get_full_name()}',
        'page_title': f'Edit Student',
    })


# ─────────────────────────────────────────────
#  Toggle Active / Deactivate
# ─────────────────────────────────────────────

@admin_required
def student_toggle_active(request, pk):
    student            = get_object_or_404(Student, pk=pk)
    student.is_active  = not student.is_active
    student.user.is_active = student.is_active
    student.user.save()
    student.save()
    status = 'activated' if student.is_active else 'deactivated'
    messages.success(
        request,
        f'Student "{student.user.get_full_name()}" {status}.'
    )
    return redirect('student_detail', pk=student.pk)


# ─────────────────────────────────────────────
#  Parent Management
# ─────────────────────────────────────────────
@admin_required
def parent_list(request):
    parents = Parent.objects.select_related(
        'user'
    ).prefetch_related(
        'student__user'
    ).order_by('user__first_name')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        parents = parents.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)  |
            Q(user__phone__icontains=q)       |
            Q(user__email__icontains=q)
        )

    paginator = Paginator(parents, 20)
    page      = request.GET.get('page', 1)
    parents   = paginator.get_page(page)

    return render(request, 'students/parent_list.html', {
        'parents':    parents,
        'q':          q,
        'page_title': 'Parents',
    })

@admin_required
def parent_add(request, student_pk):
    student = get_object_or_404(Student, pk=student_pk)
    form    = ParentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        parent = form.save(student=student)
        messages.success(
            request,
            f'Parent "{parent.user.get_full_name()}" added and linked to {student.user.get_full_name()}.'
        )
        return redirect('student_detail', pk=student.pk)

    return render(request, 'students/parent_form.html', {
        'form':       form,
        'student':    student,
        'title':      f'Add Parent for {student.user.get_full_name()}',
        'page_title': 'Add Parent',
    })


# ─────────────────────────────────────────────
#  Enrollment
# ─────────────────────────────────────────────

@admin_required
def enrollment_list(request):
    current_year = AcademicYear.objects.filter(is_current=True).first()
    enrollments  = Enrollment.objects.select_related(
        'student__user', 'section__grade', 'academic_year'
    ).order_by('-enrolled_date')

    # Filter by year
    year_id = request.GET.get('year', '')
    if year_id:
        enrollments = enrollments.filter(academic_year_id=year_id)
    elif current_year:
        enrollments = enrollments.filter(academic_year=current_year)

    # Filter by grade
    grade_id = request.GET.get('grade', '')
    if grade_id:
        enrollments = enrollments.filter(section__grade_id=grade_id)

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        enrollments = enrollments.filter(
            Q(student__user__first_name__icontains=q) |
            Q(student__user__last_name__icontains=q)  |
            Q(student__admission_number__icontains=q)
        )

    paginator   = Paginator(enrollments, 25)
    page        = request.GET.get('page', 1)
    enrollments = paginator.get_page(page)

    years  = AcademicYear.objects.all().order_by('-start_date')
    grades = Grade.objects.all().order_by('order')

    return render(request, 'students/enrollment_list.html', {
        'enrollments':  enrollments,
        'years':        years,
        'grades':       grades,
        'year_id':      year_id,
        'grade_id':     grade_id,
        'current_year': current_year,
        'q':            q,
        'page_title':   'Enrollments',
    })


@admin_required
def student_enroll(request, student_pk=None):
    student = get_object_or_404(Student, pk=student_pk) if student_pk else None
    initial = {'student': student} if student else {}
    form    = EnrollmentForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        enrollment          = form.save(commit=False)
        enrollment.is_active = True
        enrollment.save()
        messages.success(
            request,
            f'{enrollment.student.user.get_full_name()} enrolled in '
            f'{enrollment.section} for {enrollment.academic_year}.'
        )
        if student:
            return redirect('student_detail', pk=student.pk)
        return redirect('enrollment_list')

    return render(request, 'students/enrollment_form.html', {
        'form':       form,
        'student':    student,
        'title':      f'Enroll {student.user.get_full_name()}' if student else 'New Enrollment',
        'page_title': 'Enroll Student',
    })


@admin_required
def enrollment_cancel(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == 'POST':
        enrollment.is_active = False
        enrollment.save()
        messages.success(request, 'Enrollment cancelled.')
        return redirect('student_detail', pk=enrollment.student.pk)
    return render(request, 'students/enrollment_cancel_confirm.html', {
        'enrollment': enrollment,
        'page_title': 'Cancel Enrollment',
    })


# ─────────────────────────────────────────────
#  Bulk Enrollment
# ─────────────────────────────────────────────

@admin_required
def bulk_enroll(request):
    form = BulkEnrollmentForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        grade         = form.cleaned_data['grade']
        section       = form.cleaned_data['section']
        academic_year = form.cleaned_data['academic_year']

        students = Student.objects.filter(is_active=True)
        enrolled = 0
        skipped  = 0

        for student in students:
            if not Enrollment.objects.filter(
                student=student,
                academic_year=academic_year,
                is_active=True
            ).exists():
                Enrollment.objects.create(
                    student=student,
                    section=section,
                    academic_year=academic_year,
                    is_active=True
                )
                enrolled += 1
            else:
                skipped += 1

        messages.success(
            request,
            f'Bulk enrollment done: {enrolled} enrolled, {skipped} already enrolled (skipped).'
        )
        return redirect('enrollment_list')

    return render(request, 'students/bulk_enroll.html', {
        'form':       form,
        'page_title': 'Bulk Enrollment',
    })


# ─────────────────────────────────────────────
#  Student Promotion
# ─────────────────────────────────────────────

@admin_required
def student_promote(request):
    """Promote all passing students to the next grade"""
    current_year = AcademicYear.objects.filter(is_current=True).first()
    next_year    = AcademicYear.objects.filter(
        is_current=False,
        start_date__gt=current_year.end_date
    ).order_by('start_date').first() if current_year else None

    grades = Grade.objects.prefetch_related('sections').order_by('order')

    if request.method == 'POST':
        promoted = 0
        for key, value in request.POST.items():
            if key.startswith('section_'):
                enrollment_id = key.split('_')[1]
                new_section_id = value
                try:
                    enrollment = Enrollment.objects.get(pk=enrollment_id)
                    new_section = Section.objects.get(pk=new_section_id)
                    # Deactivate old enrollment
                    enrollment.is_active   = True
                    enrollment.is_promoted = True
                    enrollment.save()
                    # Create new enrollment
                    Enrollment.objects.create(
                        student=enrollment.student,
                        section=new_section,
                        academic_year=next_year,
                        is_active=True
                    )
                    promoted += 1
                except (Enrollment.DoesNotExist, Section.DoesNotExist):
                    pass
        messages.success(request, f'{promoted} student(s) promoted to {next_year}.')
        return redirect('enrollment_list')

    # Get current enrollments for each grade
    current_enrollments = Enrollment.objects.filter(
        academic_year=current_year,
        is_active=True,
        is_promoted=False
    ).select_related('student__user', 'section__grade')

    return render(request, 'students/student_promote.html', {
        'current_year':        current_year,
        'next_year':           next_year,
        'grades':              grades,
        'current_enrollments': current_enrollments,
        'page_title':          'Promote Students',
    })


# ─────────────────────────────────────────────
#  ID Card
# ─────────────────────────────────────────────

@admin_required
def student_id_card(request, pk):
    student = get_object_or_404(
        Student.objects.select_related('user'),
        pk=pk
    )
    current_year       = AcademicYear.objects.filter(is_current=True).first()
    current_enrollment = Enrollment.objects.filter(
        student=student,
        academic_year=current_year,
        is_active=True
    ).select_related('section__grade').first() if current_year else None

    from apps.core.models import School
    school = School.objects.first()

    return render(request, 'students/id_card.html', {
        'student':            student,
        'current_enrollment': current_enrollment,
        'school':             school,
        'current_year':       current_year,
        'page_title':         'Student ID Card',
    })


# ─────────────────────────────────────────────
#  AJAX — Load Sections by Grade
# ─────────────────────────────────────────────

@login_required
def ajax_sections_by_grade(request):
    grade_id = request.GET.get('grade_id', '')
    sections = []
    if grade_id:
        year = AcademicYear.objects.filter(is_current=True).first()
        qs   = Section.objects.filter(grade_id=grade_id)
        if year:
            qs = qs.filter(academic_year=year)
        sections = list(qs.values('id', 'name'))
    return JsonResponse({'sections': sections})