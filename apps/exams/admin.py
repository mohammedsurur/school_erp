# apps/exams/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Exam, ExamSchedule, ExamComponent,
    ComponentResult, SubjectResult, ReportCard
)


# ─────────────────────────────────────────────
#  Inline: ExamSchedule inside Exam
# ─────────────────────────────────────────────

class ExamScheduleInline(admin.TabularInline):
    model        = ExamSchedule
    extra        = 0
    fields       = ['subject', 'section', 'exam_date', 'start_time', 'end_time', 'room']
    show_change_link = True


# ─────────────────────────────────────────────
#  Inline: ExamComponent inside ExamSchedule
# ─────────────────────────────────────────────

class ExamComponentInline(admin.TabularInline):
    model   = ExamComponent
    extra   = 0
    fields  = ['component_type', 'max_marks', 'order']
    ordering= ['order']


# ─────────────────────────────────────────────
#  Inline: ComponentResult inside ExamComponent
# ─────────────────────────────────────────────

class ComponentResultInline(admin.TabularInline):
    model         = ComponentResult
    extra         = 0
    fields        = ['student', 'marks_obtained', 'is_absent', 'entered_by']
    raw_id_fields = ['student']


# ─────────────────────────────────────────────
#  Exam Admin
# ─────────────────────────────────────────────

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display  = [
        'name', 'exam_type', 'grade',
        'academic_year', 'term',
        'start_date', 'end_date',
        'is_published', 'schedule_count',
    ]
    list_filter   = [
        'is_published', 'exam_type',
        'grade', 'academic_year', 'term',
    ]
    search_fields = ['name']
    ordering      = ['-start_date']
    inlines       = [ExamScheduleInline]
    actions       = ['publish_exams', 'unpublish_exams']

    def schedule_count(self, obj):
        return obj.schedules.count()
    schedule_count.short_description = 'Schedules'

    def publish_exams(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} exam(s) published.')
    publish_exams.short_description = 'Publish selected exams'

    def unpublish_exams(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} exam(s) unpublished.')
    unpublish_exams.short_description = 'Unpublish selected exams'


# ─────────────────────────────────────────────
#  ExamSchedule Admin
# ─────────────────────────────────────────────

@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display  = [
        'exam', 'subject', 'section',
        'exam_date', 'start_time', 'end_time',
        'room', 'component_total', 'is_ready',
    ]
    list_filter   = ['exam__grade', 'exam__academic_year', 'exam']
    search_fields = ['subject__name', 'section__name', 'exam__name']
    ordering      = ['exam_date', 'start_time']
    inlines       = [ExamComponentInline]

    def component_total(self, obj):
        total = sum(c.max_marks for c in obj.components.all())
        colour = 'green' if total == 100 else 'red'
        return format_html(
            '<span style="color:{};font-weight:700">{}/100</span>',
            colour, total
        )
    component_total.short_description = 'Components'

    def is_ready(self, obj):
        total = sum(c.max_marks for c in obj.components.all())
        if total == 100:
            return format_html('<span style="color:green">✅ Ready</span>')
        return format_html('<span style="color:red">⚠ {}/100</span>', total)
    is_ready.short_description = 'Status'


# ─────────────────────────────────────────────
#  ExamComponent Admin
# ─────────────────────────────────────────────

@admin.register(ExamComponent)
class ExamComponentAdmin(admin.ModelAdmin):
    list_display  = [
        'exam_schedule', 'component_type',
        'max_marks', 'order',
        'allowed_range',
    ]
    list_filter   = [
        'component_type',
        'exam_schedule__exam__grade',
    ]
    search_fields = [
        'exam_schedule__subject__name',
        'exam_schedule__exam__name',
    ]
    ordering      = ['exam_schedule', 'order']
    inlines       = [ComponentResultInline]

    def allowed_range(self, obj):
        ranges = ExamComponent.COMPONENT_RANGES.get(obj.component_type)
        if ranges:
            lo, hi  = ranges
            in_range= lo <= obj.max_marks <= hi
            colour  = 'green' if in_range else 'orange'
            return format_html(
                '<span style="color:{}">{}–{}</span>',
                colour, lo, hi
            )
        return '—'
    allowed_range.short_description = 'Allowed Range'


# ─────────────────────────────────────────────
#  ComponentResult Admin
# ─────────────────────────────────────────────

@admin.register(ComponentResult)
class ComponentResultAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'component',
        'marks_obtained', 'is_absent',
        'entered_by', 'updated_at',
    ]
    list_filter   = [
        'is_absent',
        'component__component_type',
        'component__exam_schedule__exam',
    ]
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__admission_number',
    ]
    raw_id_fields    = ['student']
    readonly_fields  = ['created_at', 'updated_at']


# ─────────────────────────────────────────────
#  SubjectResult Admin
# ─────────────────────────────────────────────

@admin.register(SubjectResult)
class SubjectResultAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'subject_name',
        'total_score', 'grade_label',
        'is_pass', 'is_absent', 'updated_at',
    ]
    list_filter   = [
        'is_pass', 'is_absent',
        'grade_label',
        'exam_schedule__exam__grade',
        'exam_schedule__exam',
    ]
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__admission_number',
        'exam_schedule__subject__name',
    ]
    readonly_fields = ['total_score', 'grade_label', 'is_pass', 'updated_at']
    actions         = ['recompute_selected']

    def subject_name(self, obj):
        return obj.exam_schedule.subject.name
    subject_name.short_description = 'Subject'

    def recompute_selected(self, request, queryset):
        for sr in queryset:
            sr.compute()
        self.message_user(
            request,
            f'{queryset.count()} subject result(s) recomputed.'
        )
    recompute_selected.short_description = 'Recompute selected results'


# ─────────────────────────────────────────────
#  ReportCard Admin
# ─────────────────────────────────────────────

@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display  = [
        'student', 'exam', 'section',
        'total_subjects', 'overall_average',
        'failed_subjects', 'overall_grade_label',
        'rank', 'is_promoted', 'generated_at',
    ]
    list_filter   = [
        'is_promoted',
        'overall_grade_label',
        'exam__grade',
        'exam__academic_year',
        'exam',
        'section',
    ]
    search_fields = [
        'student__user__first_name',
        'student__user__last_name',
        'student__admission_number',
        'exam__name',
    ]
    readonly_fields = [
        'total_score', 'total_subjects',
        'failed_subjects', 'overall_average',
        'overall_grade_label', 'rank',
        'is_promoted', 'generated_at',
    ]
    ordering = ['-overall_average']
    actions  = ['recompute_selected']

    def recompute_selected(self, request, queryset):
        for rc in queryset:
            rc.compute()
        self.message_user(
            request,
            f'{queryset.count()} report card(s) recomputed.'
        )
    recompute_selected.short_description = 'Recompute selected report cards'