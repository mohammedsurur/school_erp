# apps/exams/models.py
#
# ═══════════════════════════════════════════════════════
#  ETHIOPIAN GRADING SYSTEM
# ═══════════════════════════════════════════════════════
#
#  Components per subject (must sum to exactly 100):
#    Quiz              5  – 10
#    Mid-Term Exam    20  – 30
#    Final Exam       40  – 50
#    Assignment       10  – 20
#    Attendance+Book   5  – 10
#
#  Pass/Fail per subject:
#    Pass  → total score ≥ 50 / 100
#    Fail  → total score <  50 / 100
#    (No fail for individual components)
#
#  Promotion to next grade:
#    PROMOTED  → subject_average ≥ 50
#                AND failed_subjects ≤ 2
#    NOT PROMOTED → subject_average < 50
#                   OR failed_subjects ≥ 3
#    (1 or 2 failed subjects still allows promotion)
#
#  Grade labels (NO A/B/C/D/F):
#    90 – 100  →  Excellent
#    80 –  89  →  Very Good
#    70 –  79  →  Good
#    60 –  69  →  Satisfactory
#    50 –  59  →  Pass
#     0 –  49  →  Fail
# ═══════════════════════════════════════════════════════

from django.db  import models
from django.core.validators import MinValueValidator, MaxValueValidator


# ─────────────────────────────────────────────
#  Exam  (groups multiple subjects + sections)
# ─────────────────────────────────────────────

class Exam(models.Model):

    EXAM_TYPE = [
        ('semester',   'Semester Exam'),
        ('mid_term',   'Mid-Term Exam'),
        ('final',      'Final Exam'),
        ('quarterly',  'Quarterly Exam'),
        ('makeup',     'Make-Up Exam'),
    ]

    name          = models.CharField(max_length=100)
    exam_type     = models.CharField(max_length=20, choices=EXAM_TYPE)
    academic_year = models.ForeignKey(
        'core.AcademicYear', on_delete=models.CASCADE,
        related_name='exams'
    )
    term          = models.ForeignKey(
        'core.Term', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='exams'
    )
    grade         = models.ForeignKey(
        'academic.Grade', on_delete=models.CASCADE,
        related_name='exams'
    )
    start_date    = models.DateField()
    end_date      = models.DateField()
    description   = models.TextField(blank=True)
    is_published  = models.BooleanField(
        default=False,
        help_text='Published results are visible to students and parents'
    )
    created_by    = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_exams'
    )
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Exam'
        ordering     = ['-start_date']

    def __str__(self):
        return f"{self.name} — {self.grade} — {self.academic_year}"

    @property
    def is_completed(self):
        from django.utils import timezone
        return self.end_date < timezone.now().date()


# ─────────────────────────────────────────────
#  ExamSchedule  (one subject in one section)
# ─────────────────────────────────────────────

class ExamSchedule(models.Model):

    exam         = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='schedules'
    )
    subject      = models.ForeignKey(
        'academic.Subject', on_delete=models.CASCADE,
        related_name='exam_schedules'
    )
    section      = models.ForeignKey(
        'academic.Section', on_delete=models.CASCADE,
        related_name='exam_schedules'
    )
    exam_date    = models.DateField()
    start_time   = models.TimeField()
    end_time     = models.TimeField()
    room         = models.CharField(max_length=50, blank=True)

    # Total is always 100 in Ethiopian system
    # pass mark is always 50
    TOTAL_MARKS = 100
    PASS_MARK   = 50

    class Meta:
        verbose_name    = 'Exam Schedule'
        unique_together = ('exam', 'subject', 'section')
        ordering        = ['exam_date', 'start_time']

    def __str__(self):
        return f"{self.exam} — {self.subject} — {self.section}"


# ─────────────────────────────────────────────
#  ExamComponent  (Quiz / Mid / Final / etc.)
#  Defines what components make up this schedule
#  and their max marks — must sum to 100
# ─────────────────────────────────────────────

class ExamComponent(models.Model):

    COMPONENT_TYPE = [
        ('quiz',        'Quiz'),
        ('mid_term',    'Mid-Term Exam'),
        ('final',       'Final Exam'),
        ('assignment',  'Assignment'),
        ('attendance',  'Attendance + Exercise Book'),
    ]

    # Recommended ranges (enforced by form validation)
    COMPONENT_RANGES = {
        'quiz':       (5,  10),
        'mid_term':   (20, 30),
        'final':      (40, 50),
        'assignment': (10, 20),
        'attendance': (5,  10),
    }

    exam_schedule  = models.ForeignKey(
        ExamSchedule, on_delete=models.CASCADE,
        related_name='components'
    )
    component_type = models.CharField(
        max_length=20, choices=COMPONENT_TYPE
    )
    max_marks      = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Maximum marks for this component'
    )
    order          = models.PositiveIntegerField(
        default=1,
        help_text='Display order (1=first)'
    )

    class Meta:
        verbose_name    = 'Exam Component'
        unique_together = ('exam_schedule', 'component_type')
        ordering        = ['order']

    def __str__(self):
        return (
            f"{self.get_component_type_display()} "
            f"({self.max_marks} marks) — "
            f"{self.exam_schedule.subject}"
        )


# ─────────────────────────────────────────────
#  ComponentResult  (student score per component)
# ─────────────────────────────────────────────

class ComponentResult(models.Model):

    student       = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='component_results'
    )
    component     = models.ForeignKey(
        ExamComponent, on_delete=models.CASCADE,
        related_name='results'
    )
    marks_obtained = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    is_absent      = models.BooleanField(
        default=False,
        help_text='Student was absent for this component'
    )
    entered_by     = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='entered_component_results'
    )
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name    = 'Component Result'
        unique_together = ('student', 'component')

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} — "
            f"{self.component.get_component_type_display()} — "
            f"{self.marks_obtained}/{self.component.max_marks}"
        )


# ─────────────────────────────────────────────
#  SubjectResult  (total for one subject)
#  Computed from all ComponentResults
# ─────────────────────────────────────────────

class SubjectResult(models.Model):
    """
    Total score for one student in one subject.
    Computed after all component marks are entered.

    total_score = sum(ComponentResult.marks_obtained)
    pass        = total_score >= 50
    """

    # Ethiopian grade labels
    GRADE_LABELS = [
        (90, 'Excellent'),
        (80, 'Very Good'),
        (70, 'Good'),
        (60, 'Satisfactory'),
        (50, 'Pass'),
        (0,  'Fail'),
    ]

    student       = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='subject_results'
    )
    exam_schedule = models.ForeignKey(
        ExamSchedule, on_delete=models.CASCADE,
        related_name='subject_results'
    )
    total_score   = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Sum of all component scores (out of 100)'
    )
    grade_label   = models.CharField(
        max_length=20, blank=True,
        help_text='Excellent / Very Good / Good / Satisfactory / Pass / Fail'
    )
    is_pass       = models.BooleanField(default=False)
    is_absent     = models.BooleanField(
        default=False,
        help_text='True if student was absent for most components'
    )
    entered_by    = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name    = 'Subject Result'
        unique_together = ('student', 'exam_schedule')
        ordering        = ['-total_score']

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} — "
            f"{self.exam_schedule.subject} — "
            f"{self.total_score}/100 ({self.grade_label})"
        )

    def compute(self):
        """
        Sum all component results for this student + schedule.
        Derive grade label and pass/fail.
        """
        components = self.exam_schedule.components.all()
        cr_qs      = ComponentResult.objects.filter(
            student=self.student,
            component__exam_schedule=self.exam_schedule,
        )

        total      = sum(float(cr.marks_obtained) for cr in cr_qs)
        all_absent = all(cr.is_absent for cr in cr_qs) if cr_qs.exists() else False

        self.total_score = round(total, 2)
        self.is_absent   = all_absent
        self.is_pass     = (total >= 50) and not all_absent

        # Ethiopian grade label
        self.grade_label = 'Fail'
        if all_absent:
            self.grade_label = 'Absent'
        else:
            for boundary, label in self.GRADE_LABELS:
                if total >= boundary:
                    self.grade_label = label
                    break

        self.save()

    @property
    def percentage(self):
        return round(float(self.total_score), 2)


# ─────────────────────────────────────────────
#  ReportCard  (overall per student per exam)
# ─────────────────────────────────────────────

class ReportCard(models.Model):
    """
    Ethiopian promotion rules:
      overall_average = sum(subject total scores) / number of subjects
      PROMOTED  → average >= 50 AND failed_subjects <= 2
      NOT PROMOTED → average < 50 OR failed_subjects >= 3
    """

    student        = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='report_cards'
    )
    exam           = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name='report_cards'
    )
    section        = models.ForeignKey(
        'academic.Section', on_delete=models.CASCADE,
        related_name='report_cards'
    )
    academic_year  = models.ForeignKey(
        'core.AcademicYear', on_delete=models.CASCADE,
        related_name='report_cards'
    )

    # Computed
    total_score      = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text='Sum of all subject total scores'
    )
    total_subjects   = models.PositiveIntegerField(default=0)
    failed_subjects  = models.PositiveIntegerField(
        default=0,
        help_text='Subjects where total_score < 50'
    )
    overall_average  = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='total_score / total_subjects'
    )
    overall_grade_label = models.CharField(
        max_length=20, blank=True,
        help_text='Excellent / Very Good / Good / Satisfactory / Pass / Fail'
    )
    rank             = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Class rank by overall_average (1 = highest)'
    )
    is_promoted      = models.BooleanField(
        default=False,
        help_text='average >= 50 AND failed_subjects <= 2'
    )
    teacher_remarks  = models.TextField(blank=True)
    generated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name    = 'Report Card'
        unique_together = ('student', 'exam')
        ordering        = ['-overall_average']

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} — "
            f"{self.exam.name} — "
            f"Avg: {self.overall_average} ({self.overall_grade_label})"
        )

    def compute(self):
        """
        Recompute from SubjectResults.

        Ethiopian rules:
          overall_average = sum(total_score) / total_subjects
          is_promoted     = average >= 50 AND failed_subjects <= 2
          (1 or 2 failed subjects → still promoted)
        """
        subject_results = SubjectResult.objects.filter(
            student=self.student,
            exam_schedule__exam=self.exam,
            exam_schedule__section=self.section,
        )

        total_subjects   = subject_results.count()
        total_score      = sum(
            float(sr.total_score)
            for sr in subject_results
            if not sr.is_absent
        )
        failed_subjects  = sum(
            1 for sr in subject_results
            if not sr.is_pass and not sr.is_absent
        )

        overall_average  = (
            round(total_score / total_subjects, 2)
            if total_subjects else 0
        )

        # Ethiopian grade label for overall average
        grade_label = 'Fail'
        for boundary, label in SubjectResult.GRADE_LABELS:
            if overall_average >= boundary:
                grade_label = label
                break

        # ── Ethiopian promotion rule ──────────────
        # Promoted if:
        #   average >= 50  AND  failed_subjects <= 2
        # NOT promoted if:
        #   average < 50   OR   failed_subjects >= 3
        is_promoted = (
            overall_average >= 50
            and failed_subjects <= 2
        )

        self.total_score         = total_score
        self.total_subjects      = total_subjects
        self.failed_subjects     = failed_subjects
        self.overall_average     = overall_average
        self.overall_grade_label = grade_label
        self.is_promoted         = is_promoted
        self.save()