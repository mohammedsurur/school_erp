from django.contrib import admin
from .models import *

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'section', 'marked_by']
    list_filter  = ['status', 'date', 'section']
    date_hierarchy = 'date'

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'status', 'time_in', 'time_out']
    list_filter  = ['status', 'date']



@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'section', 'date',
        'status', 'marked_by', 'created_at'
    ]
    list_filter   = ['status', 'date', 'section__grade']
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__admission_number',
    ]
    date_hierarchy = 'date'
    ordering       = ['-date']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'section', 'academic_year',
        'total_days', 'present_days',
        'absent_days', 'attendance_percentage'
    ]
    list_filter   = ['academic_year', 'section__grade']
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
    ]
    readonly_fields = ['updated_at']

    def attendance_percentage(self, obj):
        return f"{obj.attendance_percentage}%"
    attendance_percentage.short_description = 'Attendance %'