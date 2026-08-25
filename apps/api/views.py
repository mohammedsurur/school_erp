# apps/api/views.py  — PART 1
# Covers: Auth · Students · Staff · Academic · Attendance
# Paste Part 2 directly below this file.

from django.contrib.auth        import get_user_model
from django.utils               import timezone
from django.db.models           import Q, Count, Avg

from rest_framework             import viewsets, status, filters
from rest_framework.decorators  import action
from rest_framework.response    import Response
from rest_framework.views       import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from django_filters.rest_framework import DjangoFilterBackend

from apps.students.models   import Student
from apps.staff.models      import Staff
from apps.core.models      import  *
from apps.academic.models   import *
from apps.attendance.models import Attendance

from .serializers import (
    UserProfileSerializer, ChangePasswordSerializer,
    AcademicYearSerializer, TermSerializer,
    GradeSerializer, SectionSerializer,
    SubjectSerializer, ClassTeacherSerializer,
    StudentListSerializer, StudentDetailSerializer,
    StudentAttendanceSummarySerializer,
    StaffListSerializer, StaffDetailSerializer,
    AttendanceSerializer, AttendanceBulkSerializer,
    AttendanceSummarySerializer,
)
from .permissions import (
    IsAdminRole, IsStaffRole, IsTeacherOrAdmin,
    IsAdminOrReadOnlyForStaff, IsOwnerOrAdmin,
    IsStudentOwnerOrStaff,
)
from .pagination import StandardPagination, LargePagination, SmallPagination

User = get_user_model()
from django.db.models           import Q, Count, Sum, Avg, F

from rest_framework             import viewsets, status, filters
from rest_framework.decorators  import action
from rest_framework.response    import Response
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from apps.exams.models      import (
    Exam, ExamSchedule, ExamComponent,
    ComponentResult, SubjectResult, ReportCard,
)
from apps.fees.models       import (
    FeeCategory, FeeStructure, StudentFee, Payment,
)
from apps.library.models    import (
    BookCategory, Author, Book, BookCopy,
    BookIssuance, Fine,
)
from apps.transport.models  import (
    Vehicle, Route, RouteStop, StudentTransport,
)
from apps.communication.models import (
    Announcement, Notification, Event,
    MessageThread, Message,
)

from .serializers import (
    ExamSerializer, ExamScheduleSerializer,
    ExamComponentSerializer, ComponentResultSerializer,
    SubjectResultSerializer, ReportCardSerializer,
    FeeCategorySerializer, FeeStructureSerializer,
    StudentFeeSerializer, PaymentSerializer,
    BookCategorySerializer, AuthorSerializer,
    BookListSerializer, BookDetailSerializer,
    BookIssuanceSerializer, FineSerializer,
    VehicleSerializer, RouteSerializer,
    RouteStopSerializer, StudentTransportSerializer,
    AnnouncementSerializer, NotificationSerializer,
    EventSerializer, MessageThreadSerializer, MessageSerializer,
)
from .permissions import (
    IsAdminRole, IsStaffRole, IsTeacherOrAdmin,
    IsFinanceRole, IsLibraryRole,
    IsAdminOrReadOnlyForStaff,
)
from .pagination import StandardPagination, LargePagination, SmallPagination


# ══════════════════════════════════════════════
#  AUTH VIEWS
# ══════════════════════════════════════════════

class MeView(APIView):
    """
    GET  /api/me/          → current user profile
    PUT  /api/me/          → update own profile
    POST /api/me/password/ → change own password
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        return self.put(request)


class ChangePasswordView(APIView):
    """POST /api/me/password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(
            serializer.validated_data['new_password']
        )
        request.user.save()
        return Response(
            {'detail': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


# ══════════════════════════════════════════════
#  ACADEMIC VIEWSETS
# ══════════════════════════════════════════════

class AcademicYearViewSet(viewsets.ModelViewSet):
    """
    GET    /api/academic-years/
    POST   /api/academic-years/
    GET    /api/academic-years/{id}/
    PUT    /api/academic-years/{id}/
    DELETE /api/academic-years/{id}/
    GET    /api/academic-years/current/   → current year
    """
    queryset           = AcademicYear.objects.order_by('-start_date')
    serializer_class   = AcademicYearSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]
    pagination_class   = SmallPagination
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['name']

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        year = AcademicYear.objects.filter(is_current=True).first()
        if not year:
            return Response(
                {'detail': 'No current academic year set.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(AcademicYearSerializer(year).data)


class TermViewSet(viewsets.ModelViewSet):
    """
    GET  /api/terms/
    GET  /api/terms/current/  → current term
    """
    queryset           = Term.objects.select_related(
        'academic_year'
    ).order_by('-academic_year__start_date', 'start_date')
    serializer_class   = TermSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]
    pagination_class   = SmallPagination
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['academic_year', 'is_current']

    @action(detail=False, methods=['get'])
    def current(self, request):
        term = Term.objects.filter(is_current=True).first()
        if not term:
            return Response(
                {'detail': 'No current term set.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(TermSerializer(term).data)


class GradeViewSet(viewsets.ModelViewSet):
    """
    GET  /api/grades/
    GET  /api/grades/{id}/sections/  → sections in this grade
    """
    queryset           = Grade.objects.order_by('order', 'name')
    serializer_class   = GradeSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]
    pagination_class   = SmallPagination
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['name']

    @action(detail=True, methods=['get'])
    def sections(self, request, pk=None):
        grade    = self.get_object()
        sections = grade.sections.order_by('name')
        return Response(
            SectionSerializer(sections, many=True).data
        )


class SectionViewSet(viewsets.ModelViewSet):
    """
    GET  /api/sections/
    GET  /api/sections/{id}/students/  → students in this section
    """
    queryset           = Section.objects.select_related('grade').order_by(
        'grade__name', 'name'
    )
    serializer_class   = SectionSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]
    pagination_class   = SmallPagination
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['grade']
    search_fields      = ['name', 'grade__name']

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        section  = self.get_object()
        students = section.students.filter(
            is_active=True
        ).select_related('user')
        page = self.paginate_queryset(students)
        if page is not None:
            return self.get_paginated_response(
                StudentListSerializer(
                    page, many=True, context={'request': request}
                ).data
            )
        return Response(
            StudentListSerializer(
                students, many=True, context={'request': request}
            ).data
        )


class SubjectViewSet(viewsets.ModelViewSet):
    queryset           = Subject.objects.select_related('grade').order_by(
        'grade__name', 'name'
    )
    serializer_class   = SubjectSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['grade', 'is_active']
    search_fields      = ['name', 'code']


# ══════════════════════════════════════════════
#  STUDENT VIEWSET
# ══════════════════════════════════════════════

class StudentViewSet(viewsets.ModelViewSet):
    """
    GET    /api/students/                  → list (staff) or own (student)
    POST   /api/students/                  → create (admin only)
    GET    /api/students/{id}/             → detail
    PUT    /api/students/{id}/             → update (admin)
    DELETE /api/students/{id}/            → soft-delete (admin)
    GET    /api/students/{id}/attendance/ → attendance summary
    GET    /api/students/search/?q=       → name/ID search
    """
    permission_classes = [IsAuthenticated]
    pagination_class   = LargePagination
    filter_backends    = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields  = ['gender', 'is_active']
    search_fields     = [
        'user__first_name', 'user__last_name',
        'user__email', 'student_id',
    ]
    ordering_fields   = ['user__first_name', 'user__last_name']
    ordering          = ['user__first_name']

    def get_queryset(self):
        user = self.request.user
        qs   = Student.objects.select_related('user').all()

        # Students see only themselves
        if user.role == 'student':
            return qs.filter(user=user)
        # Parents see their children
        if user.role == 'parent':
            return qs.filter(parents=user)
        # Staff / admin see all
        return qs.filter(is_active=True)

    def get_serializer_class(self):
        if self.action in ('list', 'search'):
            return StudentListSerializer
        return StudentDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminRole()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        # Soft delete
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @action(detail=False, methods=['get'])
    def search(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response(
                {'detail': 'Query must be at least 2 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs = self.get_queryset().filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(student_id__icontains=q)
            | Q(user__email__icontains=q)
        )
        return Response(
            StudentListSerializer(
                qs[:20], many=True, context={'request': request}
            ).data
        )

    @action(detail=True, methods=['get'])
    def attendance(self, request, pk=None):
        """Attendance summary for one student"""
        student = self.get_object()
        qs      = Attendance.objects.filter(student=student)

        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        total   = qs.count()
        present = qs.filter(status='present').count()
        absent  = qs.filter(status='absent').count()
        late    = qs.filter(status='late').count()

        data = {
            'student_id':   student.student_id,
            'student_name': student.user.get_full_name(),
            'total':        total,
            'present':      present,
            'absent':       absent,
            'late':         late,
            'rate':         round(present / total * 100, 1) if total else 0.0,
        }
        return Response(
            StudentAttendanceSummarySerializer(data).data
        )

    @action(detail=True, methods=['get'])
    def report_cards(self, request, pk=None):
        """All report cards for one student"""
        from apps.exams.models import ReportCard
        from .serializers      import ReportCardSerializer
        student = self.get_object()
        cards   = ReportCard.objects.filter(
            student=student
        ).select_related('exam').order_by('-exam__start_date')
        return Response(
            ReportCardSerializer(cards, many=True).data
        )


# ══════════════════════════════════════════════
#  STAFF VIEWSET
# ══════════════════════════════════════════════

class StaffViewSet(viewsets.ModelViewSet):
    """
    GET    /api/staff/           → list (staff roles)
    POST   /api/staff/           → create (admin only)
    GET    /api/staff/{id}/      → detail
    PUT    /api/staff/{id}/      → update (admin)
    DELETE /api/staff/{id}/      → soft-delete (admin)
    GET    /api/staff/teachers/  → teachers only
    """
    queryset           = Staff.objects.select_related('user').filter(
        is_active=True
    )
    permission_classes = [IsStaffRole]
    pagination_class   = LargePagination
    filter_backends    = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields  = ['department', 'is_active']
    search_fields     = [
        'user__first_name', 'user__last_name',
        'user__email', 'staff_id',
    ]
    ordering_fields   = ['user__first_name', 'user__last_name']
    ordering          = ['user__first_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return StaffListSerializer
        return StaffDetailSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsStaffRole()]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])

    @action(detail=False, methods=['get'])
    def teachers(self, request):
        teachers = self.get_queryset().filter(user__role='teacher')
        page = self.paginate_queryset(teachers)
        if page is not None:
            return self.get_paginated_response(
                StaffListSerializer(page, many=True).data
            )
        return Response(StaffListSerializer(teachers, many=True).data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """GET /api/staff/me/ — own staff profile"""
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            return Response(
                {'detail': 'Staff profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(StaffDetailSerializer(staff).data)


# ══════════════════════════════════════════════
#  ATTENDANCE VIEWSET
# ══════════════════════════════════════════════

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    GET    /api/attendance/             → list (filterable)
    POST   /api/attendance/             → create single record
    POST   /api/attendance/bulk/        → create many records at once
    GET    /api/attendance/daily/       → daily summary
    GET    /api/attendance/my/          → own attendance (student)
    """
    serializer_class   = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = LargePagination
    filter_backends    = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    filterset_fields  = ['student', 'date', 'status']
    ordering_fields   = ['date']
    ordering          = ['-date']

    def get_queryset(self):
        user = self.request.user
        qs   = Attendance.objects.select_related('student__user')

        if user.role == 'student':
            return qs.filter(student__user=user)
        if user.role == 'parent':
            return qs.filter(student__parents=user)

        # Staff filters
        qp = self.request.query_params
        if qp.get('section'):
            try:
                qs = qs.filter(student__current_section=qp['section'])
            except Exception:
                pass
        if qp.get('grade'):
            try:
                qs = qs.filter(
                    student__current_section__grade=qp['grade']
                )
            except Exception:
                pass
        if qp.get('date_from'):
            qs = qs.filter(date__gte=qp['date_from'])
        if qp.get('date_to'):
            qs = qs.filter(date__lte=qp['date_to'])
        return qs

    def get_permissions(self):
        if self.action in ('create', 'bulk', 'update',
                           'partial_update', 'destroy'):
            return [IsTeacherOrAdmin()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """
        POST /api/attendance/bulk/
        Body: { "date": "2024-09-01",
                "records": [{"student":1,"status":"present"}, ...] }
        """
        serializer = AttendanceBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attendance_date = serializer.validated_data['date']
        records         = serializer.validated_data['records']
        created, updated = 0, 0

        for rec in records:
            obj, is_new = Attendance.objects.update_or_create(
                student_id=rec['student'],
                date=attendance_date,
                defaults={
                    'status':  rec['status'],
                    'remarks': rec.get('remarks', ''),
                }
            )
            if is_new: created += 1
            else:      updated += 1

        return Response({
            'detail':  f'{created} created, {updated} updated.',
            'created': created,
            'updated': updated,
            'date':    str(attendance_date),
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """
        GET /api/attendance/daily/?date=2024-09-01
        Returns summary counts for that date.
        """
        date_str = request.query_params.get('date')
        if not date_str:
            from datetime import date
            date_str = str(date.today())

        qs      = Attendance.objects.filter(date=date_str)
        total   = qs.count()
        present = qs.filter(status='present').count()
        absent  = qs.filter(status='absent').count()
        late    = qs.filter(status='late').count()

        return Response({
            'date':    date_str,
            'total':   total,
            'present': present,
            'absent':  absent,
            'late':    late,
            'rate':    round(present / total * 100, 1) if total else 0.0,
        })

    @action(detail=False, methods=['get'])
    def my(self, request):
        """
        GET /api/attendance/my/
        Own attendance (student/parent). Same as list but explicit endpoint.
        """
        qs   = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                AttendanceSerializer(page, many=True).data
            )
        return Response(AttendanceSerializer(qs, many=True).data)


# ══════════════════════════════════════════════
#  EXAM VIEWSETS
# ══════════════════════════════════════════════

class ExamViewSet(viewsets.ModelViewSet):
    """
    GET    /api/exams/
    POST   /api/exams/
    GET    /api/exams/{id}/
    GET    /api/exams/{id}/results/    → all subject results for this exam
    GET    /api/exams/{id}/report_cards/ → all report cards
    GET    /api/exams/{id}/summary/    → pass rate + average per subject
    """
    queryset           = Exam.objects.select_related(
        'academic_year', 'term'
    ).order_by('-start_date')
    serializer_class   = ExamSerializer
    permission_classes = [IsTeacherOrAdmin]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['academic_year', 'term', 'is_published']
    search_fields      = ['name']

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsTeacherOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        exam    = self.get_object()
        results = SubjectResult.objects.filter(
            exam=exam
        ).select_related('student__user', 'subject').order_by(
            'subject__name', 'student__user__last_name'
        )
        # Optional filters
        if request.query_params.get('subject'):
            results = results.filter(
                subject=request.query_params['subject']
            )
        if request.query_params.get('student'):
            results = results.filter(
                student=request.query_params['student']
            )
        page = self.paginate_queryset(results)
        if page is not None:
            return self.get_paginated_response(
                SubjectResultSerializer(page, many=True).data
            )
        return Response(SubjectResultSerializer(results, many=True).data)

    @action(detail=True, methods=['get'])
    def report_cards(self, request, pk=None):
        exam  = self.get_object()
        cards = ReportCard.objects.filter(exam=exam).select_related(
            'student__user'
        ).order_by('-average_score')
        page = self.paginate_queryset(cards)
        if page is not None:
            return self.get_paginated_response(
                ReportCardSerializer(page, many=True).data
            )
        return Response(ReportCardSerializer(cards, many=True).data)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        exam     = self.get_object()
        by_subj  = SubjectResult.objects.filter(exam=exam).values(
            'subject__name'
        ).annotate(
            avg=Avg('total_score'),
            total=Count('id'),
            passed=Count('id', filter=Q(is_pass=True)),
        ).order_by('-avg')

        total_students = ReportCard.objects.filter(exam=exam).count()
        promoted       = ReportCard.objects.filter(
            exam=exam, is_promoted=True
        ).count()
        overall_avg    = SubjectResult.objects.filter(
            exam=exam
        ).aggregate(a=Avg('total_score'))['a'] or 0

        return Response({
            'exam':            exam.name,
            'total_students':  total_students,
            'promoted':        promoted,
            'promotion_rate':  round(promoted / total_students * 100, 1)
                               if total_students else 0,
            'overall_average': round(overall_avg, 2),
            'subjects': [
                {
                    'subject':    r['subject__name'],
                    'average':    round(r['avg'] or 0, 2),
                    'pass_rate':  round(r['passed'] / r['total'] * 100, 1)
                                  if r['total'] else 0,
                    'total':      r['total'],
                    'passed':     r['passed'],
                }
                for r in by_subj
            ]
        })


class ExamScheduleViewSet(viewsets.ModelViewSet):
    queryset           = ExamSchedule.objects.select_related(
        'exam', 'subject'
    ).order_by('date', 'start_time')
    serializer_class   = ExamScheduleSerializer
    permission_classes = [IsTeacherOrAdmin]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['exam', 'subject']


class SubjectResultViewSet(viewsets.ModelViewSet):
    """
    GET  /api/subject-results/
    POST /api/subject-results/bulk/  → save many results at once
    """
    queryset           = SubjectResult.objects.select_related(
        'student__user', 'subject', 'exam'
    ).order_by('-exam__start_date')
    serializer_class   = SubjectResultSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class   = LargePagination
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['exam', 'subject', 'student', 'is_pass']

    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """
        POST /api/subject-results/bulk/
        Body: [{"exam":1,"student":2,"subject":3,"total_score":78}, ...]
        """
        if not isinstance(request.data, list):
            return Response(
                {'detail': 'Expected a list of results.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = SubjectResultSerializer(
            data=request.data, many=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': f'{len(serializer.data)} results saved.'},
            status=status.HTTP_201_CREATED
        )


class ReportCardViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — report cards are generated by the system"""
    queryset           = ReportCard.objects.select_related(
        'student__user', 'exam'
    ).order_by('-exam__start_date')
    serializer_class   = ReportCardSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = LargePagination
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['exam', 'student', 'is_promoted']

    def get_queryset(self):
        user = self.request.user
        qs   = super().get_queryset()
        if user.role == 'student':
            return qs.filter(student__user=user)
        if user.role == 'parent':
            return qs.filter(student__parents=user)
        return qs


# ══════════════════════════════════════════════
#  FEE VIEWSETS
# ══════════════════════════════════════════════

class FeeCategoryViewSet(viewsets.ModelViewSet):
    queryset           = FeeCategory.objects.filter(is_active=True)
    serializer_class   = FeeCategorySerializer
    permission_classes = [IsFinanceRole]


class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset           = FeeStructure.objects.select_related(
        'fee_category', 'academic_year', 'grade'
    ).order_by('-academic_year__start_date')
    serializer_class   = FeeStructureSerializer
    permission_classes = [IsFinanceRole]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['academic_year', 'grade', 'fee_category']


class StudentFeeViewSet(viewsets.ModelViewSet):
    """
    GET  /api/student-fees/
    GET  /api/student-fees/{id}/payments/ → payment history
    GET  /api/student-fees/outstanding/   → unpaid/partial only
    """
    queryset           = StudentFee.objects.select_related(
        'student__user',
        'fee_structure__fee_category',
        'academic_year',
    ).order_by('-academic_year__start_date')
    serializer_class   = StudentFeeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = LargePagination
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['student', 'academic_year', 'status']

    def get_queryset(self):
        user = self.request.user
        qs   = super().get_queryset()
        if user.role == 'student':
            return qs.filter(student__user=user)
        if user.role == 'parent':
            return qs.filter(student__parents=user)
        return qs

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsFinanceRole()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        fee      = self.get_object()
        payments = fee.payments.order_by('-payment_date')
        return Response(PaymentSerializer(payments, many=True).data)

    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        qs = self.get_queryset().filter(
            status__in=['unpaid', 'partial']
        )
        total = qs.aggregate(
            s=Sum(F('amount_due') - F('amount_paid'))
        )['s'] or 0
        page = self.paginate_queryset(qs)
        if page is not None:
            resp = self.get_paginated_response(
                StudentFeeSerializer(page, many=True).data
            )
            resp.data['total_outstanding'] = float(total)
            return resp
        return Response({
            'total_outstanding': float(total),
            'results': StudentFeeSerializer(qs, many=True).data,
        })


class PaymentViewSet(viewsets.ModelViewSet):
    queryset           = Payment.objects.select_related(
        'student_fee__student__user',
        'student_fee__fee_structure__fee_category',
        'collected_by',
    ).order_by('-payment_date')
    serializer_class   = PaymentSerializer
    permission_classes = [IsFinanceRole]
    pagination_class   = LargePagination
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['student_fee', 'payment_method', 'payment_date']
    ordering_fields    = ['payment_date', 'amount']

    def perform_create(self, serializer):
        serializer.save(collected_by=self.request.user)


# ══════════════════════════════════════════════
#  LIBRARY VIEWSETS
# ══════════════════════════════════════════════

class BookCategoryViewSet(viewsets.ModelViewSet):
    queryset           = BookCategory.objects.all()
    serializer_class   = BookCategorySerializer
    permission_classes = [IsLibraryRole]


class AuthorViewSet(viewsets.ModelViewSet):
    queryset           = Author.objects.all()
    serializer_class   = AuthorSerializer
    permission_classes = [IsLibraryRole]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['name']


class BookViewSet(viewsets.ModelViewSet):
    """
    GET  /api/books/
    GET  /api/books/{id}/availability/ → copy count breakdown
    GET  /api/books/search/?q=
    """
    permission_classes = [IsAuthenticated]
    filter_backends    = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields  = ['category', 'is_active']
    search_fields     = ['title', 'isbn', 'author__name']
    ordering_fields   = ['title', 'created_at']
    ordering          = ['title']

    def get_queryset(self):
        return Book.objects.select_related(
            'category', 'author', 'publisher'
        ).filter(is_active=True)

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer
        return BookDetailSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsLibraryRole()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        book   = self.get_object()
        copies = book.copies.values('status').annotate(cnt=Count('id'))
        by_status = {r['status']: r['cnt'] for r in copies}
        return Response({
            'book':      book.title,
            'total':     book.copies.count(),
            'available': by_status.get('available', 0),
            'issued':    by_status.get('issued', 0),
            'lost':      by_status.get('lost', 0),
            'damaged':   by_status.get('damaged', 0),
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response(
                {'detail': 'Query must be at least 2 characters.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        qs = self.get_queryset().filter(
            Q(title__icontains=q)
            | Q(isbn__icontains=q)
            | Q(author__name__icontains=q)
        )
        return Response(
            BookListSerializer(qs[:20], many=True).data
        )


class BookIssuanceViewSet(viewsets.ModelViewSet):
    """
    GET  /api/issuances/
    POST /api/issuances/               → issue a book
    POST /api/issuances/{id}/return/   → mark as returned
    GET  /api/issuances/overdue/       → overdue list
    GET  /api/issuances/my/            → own issuances (student)
    """
    queryset           = BookIssuance.objects.select_related(
        'book_copy__book', 'student__user'
    ).order_by('-issued_date')
    serializer_class   = BookIssuanceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = LargePagination
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['student', 'status']

    def get_queryset(self):
        user = self.request.user
        qs   = super().get_queryset()
        if user.role == 'student':
            return qs.filter(student__user=user)
        if user.role == 'parent':
            return qs.filter(student__parents=user)
        return qs

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update',
                           'destroy', 'return_book'):
            return [IsLibraryRole()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request, pk=None):
        issuance = self.get_object()
        if issuance.status == 'returned':
            return Response(
                {'detail': 'Book already returned.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        from datetime import date
        issuance.status      = 'returned'
        issuance.return_date = date.today()
        issuance.save(update_fields=['status', 'return_date'])
        # Update copy status
        issuance.book_copy.status = 'available'
        issuance.book_copy.save(update_fields=['status'])
        return Response(
            {'detail': 'Book returned successfully.',
             'return_date': str(issuance.return_date)}
        )

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        qs   = self.get_queryset().filter(status='overdue')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                BookIssuanceSerializer(page, many=True).data
            )
        return Response(BookIssuanceSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def my(self, request):
        qs   = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                BookIssuanceSerializer(page, many=True).data
            )
        return Response(BookIssuanceSerializer(qs, many=True).data)


class FineViewSet(viewsets.ModelViewSet):
    queryset           = Fine.objects.select_related(
        'issuance__student__user',
        'issuance__book_copy__book',
    ).order_by('-issued_date')
    serializer_class   = FineSerializer
    permission_classes = [IsLibraryRole]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['status', 'issuance__student']


# ══════════════════════════════════════════════
#  TRANSPORT VIEWSETS
# ══════════════════════════════════════════════

class VehicleViewSet(viewsets.ModelViewSet):
    queryset           = Vehicle.objects.filter(is_active=True)
    serializer_class   = VehicleSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['name', 'plate_number', 'driver_name']


class RouteViewSet(viewsets.ModelViewSet):
    """
    GET  /api/routes/
    GET  /api/routes/{id}/students/    → assigned students
    GET  /api/routes/{id}/utilisation/ → capacity stats
    """
    queryset           = Route.objects.select_related(
        'vehicle'
    ).prefetch_related('stops').filter(is_active=True)
    serializer_class   = RouteSerializer
    permission_classes = [IsAdminOrReadOnlyForStaff]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['name', 'start_point', 'end_point']

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        route       = self.get_object()
        assignments = StudentTransport.objects.filter(
            route=route, is_active=True
        ).select_related('student__user', 'stop')
        return Response(
            StudentTransportSerializer(assignments, many=True).data
        )

    @action(detail=True, methods=['get'])
    def utilisation(self, request, pk=None):
        route    = self.get_object()
        capacity = route.vehicle.capacity if route.vehicle else 0
        assigned = StudentTransport.objects.filter(
            route=route, is_active=True
        ).count()
        return Response({
            'route':         route.name,
            'capacity':      capacity,
            'assigned':      assigned,
            'available':     max(0, capacity - assigned),
            'utilisation':   round(assigned / capacity * 100, 1)
                             if capacity else 0,
        })


class StudentTransportViewSet(viewsets.ModelViewSet):
    """
    GET  /api/transport-assignments/
    GET  /api/transport-assignments/my/ → own assignment (student)
    """
    queryset           = StudentTransport.objects.select_related(
        'student__user', 'route', 'stop'
    ).filter(is_active=True)
    serializer_class   = StudentTransportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['route', 'academic_year', 'student']

    def get_queryset(self):
        user = self.request.user
        qs   = super().get_queryset()
        if user.role == 'student':
            return qs.filter(student__user=user)
        if user.role == 'parent':
            return qs.filter(student__parents=user)
        return qs

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def my(self, request):
        qs = self.get_queryset()
        return Response(
            StudentTransportSerializer(qs, many=True).data
        )


# ══════════════════════════════════════════════
#  COMMUNICATION VIEWSETS
# ══════════════════════════════════════════════

class AnnouncementViewSet(viewsets.ModelViewSet):
    """
    GET  /api/announcements/           → role-filtered list
    GET  /api/announcements/active/    → only active ones
    POST /api/announcements/{id}/publish/ → toggle publish
    """
    serializer_class   = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['audience', 'priority', 'is_published']
    search_fields      = ['title', 'body']

    def get_queryset(self):
        from django.utils import timezone as tz
        user = self.request.user
        qs   = Announcement.objects.select_related(
            'created_by', 'target_grade'
        ).order_by('-created_at')

        if user.role not in {
            'super_admin','principal','admin_staff','teacher','accountant','librarian'
        }:
            now = tz.now()
            role_map = {'student': 'students', 'parent': 'parents'}
            aud = role_map.get(user.role, 'all')
            qs  = qs.filter(is_published=True).filter(
                Q(audience='all') | Q(audience=aud)
            ).filter(
                Q(publish_date__isnull=True) | Q(publish_date__lte=now)
            ).filter(
                Q(expiry_date__isnull=True) | Q(expiry_date__gte=now)
            )
        return qs

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update',
                           'destroy', 'publish'):
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        from django.utils import timezone as tz
        now = tz.now()
        qs  = self.get_queryset().filter(is_published=True).filter(
            Q(publish_date__isnull=True) | Q(publish_date__lte=now)
        ).filter(
            Q(expiry_date__isnull=True) | Q(expiry_date__gte=now)
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                AnnouncementSerializer(page, many=True).data
            )
        return Response(AnnouncementSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        ann              = self.get_object()
        ann.is_published = not ann.is_published
        ann.save(update_fields=['is_published'])
        return Response({
            'detail':       f'{"Published" if ann.is_published else "Unpublished"}.',
            'is_published': ann.is_published,
        })


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET  /api/notifications/           → own notifications
    POST /api/notifications/{id}/read/ → mark one as read
    POST /api/notifications/read-all/  → mark all as read
    GET  /api/notifications/unread/    → unread only (bell feed)
    """
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = SmallPagination
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['notif_type', 'is_read']

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notif = self.get_object()
        notif.mark_read()
        return Response({'detail': 'Marked as read.', 'link': notif.link})

    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({'detail': f'{count} notification(s) marked read.'})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        qs = self.get_queryset().filter(is_read=False)
        return Response({
            'count':   qs.count(),
            'results': NotificationSerializer(qs[:10], many=True).data,
        })


class EventViewSet(viewsets.ModelViewSet):
    """
    GET  /api/events/
    GET  /api/events/upcoming/  → future events
    """
    serializer_class   = EventSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields   = ['category', 'audience', 'is_published']
    search_fields      = ['title', 'description', 'location']

    def get_queryset(self):
        from django.utils import timezone as tz
        user = self.request.user
        qs   = Event.objects.filter(
            is_published=True
        ).order_by('start_date')
        if user.role not in {
            'super_admin','principal','admin_staff','teacher'
        }:
            role_map = {'student': 'students', 'parent': 'parents'}
            aud = role_map.get(user.role, 'all')
            qs  = qs.filter(Q(audience='all') | Q(audience=aud))
        return qs

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAdminRole()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        from django.utils import timezone as tz
        qs   = self.get_queryset().filter(start_date__gte=tz.now())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(
                EventSerializer(page, many=True).data
            )
        return Response(EventSerializer(qs, many=True).data)


class MessageThreadViewSet(viewsets.ModelViewSet):
    """
    GET  /api/threads/          → inbox
    POST /api/threads/          → start new thread
    GET  /api/threads/{id}/messages/ → messages in thread
    POST /api/threads/{id}/reply/    → send reply
    """
    serializer_class   = MessageThreadSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = StandardPagination

    def get_queryset(self):
        return MessageThread.objects.filter(
            participants=self.request.user
        ).order_by('-updated_at')

    def perform_create(self, serializer):
        thread = serializer.save()
        thread.participants.add(self.request.user)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        thread = self.get_object()
        msgs   = thread.messages.order_by('sent_at')
        # Mark unread as read
        for msg in msgs:
            if not msg.is_read_by(request.user):
                msg.mark_read(request.user)
        return Response(
            MessageSerializer(
                msgs, many=True, context={'request': request}
            ).data
        )

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        thread = self.get_object()
        body   = request.data.get('body', '').strip()
        if not body:
            return Response(
                {'detail': 'Message body cannot be empty.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        msg = Message.objects.create(
            thread=thread,
            sender=request.user,
            body=body,
        )
        msg.read_by.add(request.user)
        thread.save()   # bump updated_at

        # Notify other participants
        from apps.communication.models import Notification as Notif
        others = thread.participants.exclude(pk=request.user.pk)
        Notif.broadcast(
            recipients=others,
            title=f'New message from {request.user.get_full_name()}',
            body=body[:100],
            notif_type='message',
            link=f'/communication/messages/{thread.pk}/',
        )
        return Response(
            MessageSerializer(msg, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

