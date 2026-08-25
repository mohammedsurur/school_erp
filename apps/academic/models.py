from django.db import models
from apps.core.models import AcademicYear

class Grade(models.Model):
    """e.g. Grade 1, Grade 2 ... Grade 12"""
    name          = models.CharField(max_length=50)
    description   = models.TextField(blank=True)
    order         = models.PositiveIntegerField(default=0)

    class Meta: ordering = ['order']
    def __str__(self): return self.name

class Section(models.Model):
    """e.g. Grade 9 — Section A"""
    grade         = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='sections')
    name          = models.CharField(max_length=10)  # A, B, C
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    class_teacher = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                       null=True, blank=True, limit_choices_to={'role':'teacher'})
    capacity      = models.PositiveIntegerField(default=40)

    def __str__(self): return f"{self.grade} - {self.name}"
    def enrolled_count(self): return self.enrollments.filter(is_active=True).count()

class Subject(models.Model):
    name          = models.CharField(max_length=100)
    code          = models.CharField(max_length=20, unique=True)
    grade         = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='subjects')
    is_core       = models.BooleanField(default=True)
    pass_mark     = models.DecimalField(max_digits=5, decimal_places=2, default=50.0)
    full_marks    = models.DecimalField(max_digits=5, decimal_places=2, default=100.0)

    def __str__(self): return f"{self.name} ({self.code})"

class SubjectTeacher(models.Model):
    """Which teacher teaches which subject in which section"""
    subject       = models.ForeignKey(Subject, on_delete=models.CASCADE)
    section       = models.ForeignKey(Section, on_delete=models.CASCADE)
    teacher       = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                       limit_choices_to={'role':'teacher'})
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    class Meta: unique_together = ['subject', 'section', 'academic_year']