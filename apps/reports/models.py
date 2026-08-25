# apps/reports/models.py

from django.db   import models
from django.utils import timezone


# ─────────────────────────────────────────────
#  Report Request  (log of every generated report)
# ─────────────────────────────────────────────

class ReportRequest(models.Model):
    REPORT_TYPE = [
        # Academic
        ('report_card',       'Student Report Card'),
        ('exam_results',      'Exam Results'),
        ('class_results',     'Class Results Summary'),
        # Attendance
        ('attendance_student', 'Student Attendance'),
        ('attendance_class',   'Class Attendance'),
        ('attendance_summary', 'Attendance Summary'),
        # Finance
        ('fee_collection',    'Fee Collection'),
        ('fee_outstanding',   'Outstanding Fees'),
        ('fee_daily',         'Daily Collection'),
        ('fee_structure',     'Fee Structure'),
        # Library
        ('library_issuances', 'Library Issuances'),
        ('library_overdue',   'Overdue Books'),
        ('library_fines',     'Library Fines'),
        # Transport
        ('transport_students','Transport Assignments'),
        ('transport_attendance','Transport Attendance'),
        # Staff
        ('staff_list',        'Staff List'),
        ('student_list',      'Student List'),
        # General
        ('custom',            'Custom Report'),
    ]
    STATUS = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('ready',      'Ready'),
        ('failed',     'Failed'),
    ]
    FORMAT = [
        ('pdf',  'PDF'),
        ('excel','Excel'),
    ]

    report_type  = models.CharField(max_length=30, choices=REPORT_TYPE)
    format       = models.CharField(
        max_length=5, choices=FORMAT, default='pdf'
    )
    title        = models.CharField(max_length=255)
    parameters   = models.JSONField(
        default=dict,
        help_text='Serialised filter parameters used to generate this report'
    )
    status       = models.CharField(
        max_length=12, choices=STATUS, default='pending'
    )
    file         = models.FileField(
        upload_to='reports/generated/%Y/%m/',
        null=True, blank=True
    )
    error_message= models.TextField(blank=True)
    requested_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='report_requests'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.get_report_type_display()} — {self.requested_at:%Y-%m-%d}"

    @property
    def duration_seconds(self):
        if self.completed_at and self.requested_at:
            return (self.completed_at - self.requested_at).seconds
        return None

    def mark_ready(self, file_path):
        self.status       = 'ready'
        self.file         = file_path
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'file', 'completed_at'])

    def mark_failed(self, error=''):
        self.status        = 'failed'
        self.error_message = error
        self.completed_at  = timezone.now()
        self.save(update_fields=['status', 'error_message', 'completed_at'])


# ─────────────────────────────────────────────
#  Scheduled Report
# ─────────────────────────────────────────────

class ScheduledReport(models.Model):
    FREQUENCY = [
        ('daily',   'Daily'),
        ('weekly',  'Weekly'),
        ('monthly', 'Monthly'),
        ('termly',  'Per Term'),
    ]

    report_type  = models.CharField(
        max_length=30,
        choices=ReportRequest.REPORT_TYPE
    )
    title        = models.CharField(max_length=255)
    frequency    = models.CharField(
        max_length=10, choices=FREQUENCY, default='monthly'
    )
    parameters   = models.JSONField(default=dict)
    recipients   = models.ManyToManyField(
        'accounts.User', blank=True,
        related_name='scheduled_reports',
        help_text='Users who receive this report by notification'
    )
    is_active    = models.BooleanField(default=True)
    last_run     = models.DateTimeField(null=True, blank=True)
    next_run     = models.DateTimeField(null=True, blank=True)
    created_by   = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, related_name='created_scheduled_reports'
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.get_frequency_display()})"