from django.contrib import admin
from .models import Grade, Section, Subject, SubjectTeacher
from .timetable_models import Period, Timetable

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    ordering     = ['order']

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['grade', 'name', 'academic_year', 'class_teacher', 'capacity']
    list_filter  = ['grade', 'academic_year']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'grade', 'is_core', 'pass_mark', 'full_marks']
    list_filter  = ['grade', 'is_core']

@admin.register(SubjectTeacher)
class SubjectTeacherAdmin(admin.ModelAdmin):
    list_display = ['subject', 'section', 'teacher', 'academic_year']

@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'order']
    ordering     = ['order']

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['section', 'day', 'period', 'subject', 'teacher', 'room']
    list_filter  = ['section', 'day', 'academic_year']