# apps/fees/admin.py

from django.contrib import admin
from .models        import FeeCategory, FeeStructure, StudentFee, Payment


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'is_mandatory', 'created_at']
    list_filter   = ['is_mandatory']
    search_fields = ['name']


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display  = [
        'fee_category', 'grade', 'academic_year',
        'term', 'amount', 'due_date'
    ]
    list_filter   = ['academic_year', 'grade', 'fee_category']
    search_fields = ['fee_category__name']
    ordering      = ['grade__order', 'fee_category__name']


@admin.register(StudentFee)
class StudentFeeAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'fee_structure', 'academic_year',
        'amount_due', 'discount', 'amount_paid',
        'balance_display', 'status'
    ]
    list_filter   = ['status', 'academic_year', 'fee_structure__grade']
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__admission_number',
    ]
    readonly_fields = ['amount_paid', 'status', 'created_at', 'updated_at']

    def balance_display(self, obj):
        return f"{obj.balance:.2f}"
    balance_display.short_description = 'Balance'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = [
        'student_fee', 'amount', 'payment_method',
        'payment_date', 'reference_number', 'collected_by'
    ]
    list_filter   = ['payment_method', 'payment_date']
    search_fields = [
        'student_fee__student__user__first_name',
        'student_fee__student__user__last_name',
        'reference_number',
    ]
    date_hierarchy = 'payment_date'
    readonly_fields = ['created_at']