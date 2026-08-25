from django.db import models

# Create your models here.
# apps/events/models.py
from django.db import models


class EventCategory(models.Model):
    name  = models.CharField(max_length=100)
    color = models.CharField(max_length=10, default='#1a3c72')
    icon  = models.CharField(max_length=50, default='bi bi-calendar-event')

    def __str__(self): return self.name


class Event(models.Model):
    EVENT_TYPE = [
        ('holiday',   'Holiday'),
        ('exam',      'Exam'),
        ('meeting',   'Meeting'),
        ('sports',    'Sports'),
        ('cultural',  'Cultural'),
        ('other',     'Other'),
    ]
    AUDIENCE = [
        ('all',       'Everyone'),
        ('teachers',  'Teachers'),
        ('students',  'Students'),
        ('parents',   'Parents'),
    ]

    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    category     = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, blank=True)
    event_type   = models.CharField(max_length=20, choices=EVENT_TYPE)
    start_date   = models.DateField()
    end_date     = models.DateField()
    start_time   = models.TimeField(null=True, blank=True)
    end_time     = models.TimeField(null=True, blank=True)
    location     = models.CharField(max_length=200, blank=True)
    audience     = models.CharField(max_length=20, choices=AUDIENCE, default='all')
    is_published = models.BooleanField(default=True)
    created_by   = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True )
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta: ordering = ['start_date']

    def __str__(self): return self.title