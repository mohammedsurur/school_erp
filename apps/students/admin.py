from django.contrib import admin
from .models import Student, Parent, Enrollment

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ['admission_number', 'user', 'gender', 'admission_date', 'is_active']
    list_filter   = ['gender', 'is_active']
    search_fields = ['admission_number', 'user__first_name', 'user__last_name']

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['user', 'relation', 'occupation']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'section', 'academic_year', 'is_active', 'is_promoted']
    list_filter  = ['academic_year', 'is_active']