from django.db import models
from datetime import datetime, date

from .models import *
class Period(models.Model):
    """Defines time slots: Period 1 = 8:00 AM - 8:45 AM"""
    name       = models.CharField(max_length=20)   # "Period 1"
    start_time = models.TimeField()
    end_time   = models.TimeField()
    order      = models.PositiveIntegerField()

    class Meta: ordering = ['order']
    
    @property
    def duration_minutes(self):
        start = datetime.combine(date.today(), self.start_time)
        end   = datetime.combine(date.today(), self.end_time)
        return int((end - start).total_seconds() / 60)

class Timetable(models.Model):
    DAY_CHOICES = [
        ('MON','Monday'),('TUE','Tuesday'),('WED','Wednesday'),
        ('THU','Thursday'),('FRI','Friday'),
    ]
    section       = models.ForeignKey(Section, on_delete=models.CASCADE)
    day           = models.CharField(max_length=3, choices=DAY_CHOICES)
    period        = models.ForeignKey(Period, on_delete=models.CASCADE)
    subject       = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher       = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    room          = models.CharField(max_length=20, blank=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['section', 'day', 'period', 'academic_year']

  