# apps/api/urls.py

from django.urls        import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views

# ─────────────────────────────────────────────
#  Router — auto-generates CRUD endpoints
# ─────────────────────────────────────────────

router = DefaultRouter()

# Academic
router.register(r'academic-years',  views.AcademicYearViewSet,  basename='academic-year')
router.register(r'terms',           views.TermViewSet,           basename='term')
router.register(r'grades',          views.GradeViewSet,          basename='grade')
router.register(r'sections',        views.SectionViewSet,        basename='section')
router.register(r'subjects',        views.SubjectViewSet,        basename='subject')

# Students & Staff
router.register(r'students',        views.StudentViewSet,        basename='student')
router.register(r'staff',           views.StaffViewSet,          basename='staff')

# Attendance
router.register(r'attendance',      views.AttendanceViewSet,     basename='attendance')

# Exams
router.register(r'exams',           views.ExamViewSet,           basename='exam')
router.register(r'exam-schedules',  views.ExamScheduleViewSet,   basename='exam-schedule')
router.register(r'subject-results', views.SubjectResultViewSet,  basename='subject-result')
router.register(r'report-cards',    views.ReportCardViewSet,     basename='report-card')

# Fees
router.register(r'fee-categories',  views.FeeCategoryViewSet,    basename='fee-category')
router.register(r'fee-structures',  views.FeeStructureViewSet,   basename='fee-structure')
router.register(r'student-fees',    views.StudentFeeViewSet,     basename='student-fee')
router.register(r'payments',        views.PaymentViewSet,        basename='payment')

# Library
router.register(r'book-categories', views.BookCategoryViewSet,   basename='book-category')
router.register(r'authors',         views.AuthorViewSet,         basename='author')
router.register(r'books',           views.BookViewSet,           basename='book')
router.register(r'issuances',       views.BookIssuanceViewSet,   basename='issuance')
router.register(r'fines',           views.FineViewSet,           basename='fine')

# Transport
router.register(r'vehicles',        views.VehicleViewSet,        basename='vehicle')
router.register(r'routes',          views.RouteViewSet,          basename='route')
router.register(r'transport-assignments', views.StudentTransportViewSet, basename='transport-assignment')

# Communication
router.register(r'announcements',   views.AnnouncementViewSet,   basename='announcement')
router.register(r'notifications',   views.NotificationViewSet,   basename='notification')
router.register(r'events',          views.EventViewSet,          basename='event')
router.register(r'threads',         views.MessageThreadViewSet,  basename='thread')


# ─────────────────────────────────────────────
#  URL patterns
# ─────────────────────────────────────────────

urlpatterns = [

    # ── JWT Auth ──────────────────────────────
    path(
        'token/',
        TokenObtainPairView.as_view(),
        name='token_obtain'
    ),
    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path(
        'token/verify/',
        TokenVerifyView.as_view(),
        name='token_verify'
    ),

    # ── Current user ──────────────────────────
    path(
        'me/',
        views.MeView.as_view(),
        name='api_me'
    ),
    path(
        'me/password/',
        views.ChangePasswordView.as_view(),
        name='api_change_password'
    ),

    # ── All registered ViewSets ───────────────
    path('', include(router.urls)),
]