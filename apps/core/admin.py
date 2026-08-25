from django.contrib import admin

from .models import School, AcademicYear, Term, AuditLog

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'established']

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display  = ['name', 'start_date', 'end_date', 'is_current']
    list_editable = ['is_current']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'start_date', 'end_date', 'is_current']
    list_filter  = ['academic_year']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'model_name', 'timestamp']
    list_filter   = ['action', 'model_name']
    readonly_fields = ['user','action','model_name','object_id','detail','ip_address','timestamp']