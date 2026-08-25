from django.db   import models
from django.utils import timezone

# Create your models here.
class StudentAttendance(models.Model):
    STATUS = [('P','Present'),('A','Absent'),('L','Late'),('Ex','Excused')]

    student       = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    section       = models.ForeignKey('academic.Section', on_delete=models.CASCADE)
    date          = models.DateField()
    status        = models.CharField(max_length=2, choices=STATUS, default='P')
    marked_by     = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    remarks       = models.CharField(max_length=200, blank=True)
    academic_year = models.ForeignKey('core.AcademicYear', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['student', 'date']

class StaffAttendance(models.Model):
    STATUS = [('P','Present'),('A','Absent'),('L','Late'),('HD','Half Day'),('WFH','Work From Home')]

    staff    = models.ForeignKey('staff.Staff', on_delete=models.CASCADE)
    date     = models.DateField()
    status   = models.CharField(max_length=5, choices=STATUS)
    time_in  = models.TimeField(blank=True, null=True)
    time_out = models.TimeField(blank=True, null=True)
    remarks  = models.CharField(max_length=200, blank=True)

    class Meta: unique_together = ['staff', 'date']

class Attendance(models.Model):

    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent',  'Absent'),
        ('late',    'Late'),
        ('excused', 'Excused'),
    ]

    student      = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    section      = models.ForeignKey(
        'academic.Section',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    date         = models.DateField(default=timezone.now)
    status       = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='present'
    )
    marked_by    = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='marked_attendances'
    )
    note         = models.CharField(max_length=255, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Attendance'
        verbose_name_plural = 'Attendance Records'
        ordering            = ['-date', 'student__user__first_name']
        # One record per student per section per date
        unique_together     = ('student', 'section', 'date')

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} — "
            f"{self.date} — {self.get_status_display()}"
        )

    @property
    def is_present(self):
        return self.status == 'present'

    @property
    def is_absent(self):
        return self.status == 'absent'


class AttendanceSummary(models.Model):
    """
    Monthly/term pre-computed summary per student per section.
    Populated by a management command or signal — avoids
    counting raw rows on every report page load.
    """
    student       = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    section       = models.ForeignKey(
        'academic.Section',
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    academic_year = models.ForeignKey(
        'core.AcademicYear',
        on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    term          = models.ForeignKey(
        'core.Term',
        on_delete=models.CASCADE,
        related_name='attendance_summaries',
        null=True, blank=True
    )
    total_days    = models.PositiveIntegerField(default=0)
    present_days  = models.PositiveIntegerField(default=0)
    absent_days   = models.PositiveIntegerField(default=0)
    late_days     = models.PositiveIntegerField(default=0)
    excused_days  = models.PositiveIntegerField(default=0)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Attendance Summary'
        verbose_name_plural = 'Attendance Summaries'
        unique_together     = ('student', 'section', 'academic_year', 'term')

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} — "
            f"{self.academic_year} — "
            f"{self.present_days}/{self.total_days}"
        )

    @property
    def attendance_percentage(self):
        if self.total_days == 0:
            return 0
        return round((self.present_days / self.total_days) * 100, 1)

    @property
    def is_at_risk(self):
        """Flag students below 75% attendance"""
        return self.attendance_percentage < 75