# apps/api/serializers.py  — PART 1
# Covers: Auth · Students · Staff · Academic
# Paste Part 2 directly below this file.

from django.contrib.auth    import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework         import serializers
from rest_framework.validators import UniqueValidator

from apps.students.models   import Student
from apps.staff.models      import Staff
from apps.core.models      import *
from apps.academic.models   import (
    AcademicYear,  Grade, Section, Subject, ClassTeacher
)

User = get_user_model()


# ══════════════════════════════════════════════
#  AUTH / USER SERIALIZERS
# ══════════════════════════════════════════════

class UserBasicSerializer(serializers.ModelSerializer):
    """Minimal user — embedded in related objects"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'full_name', 'email', 'role']

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserProfileSerializer(serializers.ModelSerializer):
    """Full profile — returned by /api/me/"""
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(
        source='get_role_display', read_only=True
    )

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email',
            'first_name', 'last_name', 'full_name',
            'role', 'role_display',
            'phone_number',
            'is_active', 'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'role', 'date_joined', 'last_login']

    def get_full_name(self, obj):
        return obj.get_full_name()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, validators=[validate_password]
    )
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


# ══════════════════════════════════════════════
#  ACADEMIC SERIALIZERS
# ══════════════════════════════════════════════

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AcademicYear
        fields = [
            'id', 'name', 'start_date', 'end_date',
            'is_current', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError(
                    'End date must be after start date.'
                )
        return data


class TermSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(
        source='academic_year.name', read_only=True
    )

    class Meta:
        model  = Term
        fields = [
            'id', 'academic_year', 'academic_year_name',
            'term_number', 'name',
            'start_date', 'end_date', 'is_current',
        ]
        read_only_fields = ['id']


class GradeSerializer(serializers.ModelSerializer):
    student_count = serializers.SerializerMethodField()

    class Meta:
        model  = Grade
        fields = ['id', 'name', 'description', 'order', 'student_count']
        read_only_fields = ['id']

    def get_student_count(self, obj):
        return obj.sections.aggregate(
            total=serializers.Count('students')
        )['total'] if hasattr(obj, 'sections') else 0


class SectionSerializer(serializers.ModelSerializer):
    grade_name    = serializers.CharField(source='grade.name', read_only=True)
    student_count = serializers.SerializerMethodField()
    class_teacher = serializers.SerializerMethodField()

    class Meta:
        model  = Section
        fields = [
            'id', 'grade', 'grade_name', 'name',
            'capacity', 'student_count', 'class_teacher',
        ]
        read_only_fields = ['id']

    def get_student_count(self, obj):
        return obj.students.filter(is_active=True).count()

    def get_class_teacher(self, obj):
        ct = obj.class_teacher_assignments.filter(
            is_active=True
        ).select_related('teacher__user').first()
        if ct:
            return {
                'id':   ct.teacher.id,
                'name': ct.teacher.user.get_full_name(),
            }
        return None


class SubjectSerializer(serializers.ModelSerializer):
    grade_name = serializers.CharField(source='grade.name', read_only=True)

    class Meta:
        model  = Subject
        fields = [
            'id', 'name', 'code', 'grade', 'grade_name',
            'description', 'is_active',
        ]
        read_only_fields = ['id']


class ClassTeacherSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(
        source='teacher.user.get_full_name', read_only=True
    )
    section_name = serializers.SerializerMethodField()

    class Meta:
        model  = ClassTeacher
        fields = [
            'id', 'teacher', 'teacher_name',
            'section', 'section_name',
            'academic_year', 'is_active', 'assigned_date',
        ]
        read_only_fields = ['id']

    def get_section_name(self, obj):
        return f"{obj.section.grade.name} — {obj.section.name}"


# ══════════════════════════════════════════════
#  STUDENT SERIALIZERS
# ══════════════════════════════════════════════

class StudentListSerializer(serializers.ModelSerializer):
    """Compact — used in lists, search results"""
    full_name     = serializers.CharField(
        source='user.get_full_name', read_only=True
    )
    email         = serializers.EmailField(
        source='user.email', read_only=True
    )
    grade         = serializers.SerializerMethodField()
    section       = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model  = Student
        fields = [
            'id', 'student_id', 'full_name', 'email',
            'grade', 'section',
            'gender', 'date_of_birth',
            'is_active', 'profile_photo',
        ]
        read_only_fields = ['id', 'student_id']

    def get_grade(self, obj):
        sec = obj.current_section
        return sec.grade.name if sec and sec.grade else None

    def get_section(self, obj):
        sec = obj.current_section
        return sec.name if sec else None

    def get_profile_photo(self, obj):
        request = self.context.get('request')
        if obj.profile_photo and request:
            return request.build_absolute_uri(obj.profile_photo.url)
        return None


class StudentDetailSerializer(serializers.ModelSerializer):
    """Full detail — used in retrieve/create/update"""
    user          = UserBasicSerializer(read_only=True)
    section_name  = serializers.SerializerMethodField()
    grade_name    = serializers.SerializerMethodField()
    age           = serializers.SerializerMethodField()

    # Write-only fields for creation
    first_name    = serializers.CharField(write_only=True)
    last_name     = serializers.CharField(write_only=True)
    email         = serializers.EmailField(
        write_only=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password      = serializers.CharField(
        write_only=True, validators=[validate_password]
    )

    class Meta:
        model  = Student
        fields = [
            'id', 'student_id', 'user',
            # write-only creation fields
            'first_name', 'last_name', 'email', 'password',
            # student fields
            'current_section', 'section_name', 'grade_name',
            'gender', 'date_of_birth', 'age',
            'address', 'phone_number',
            'parent_name', 'parent_phone', 'parent_email',
            'emergency_contact', 'emergency_phone',
            'blood_group', 'medical_notes',
            'enrollment_date', 'is_active',
        ]
        read_only_fields = ['id', 'student_id', 'user']

    def get_section_name(self, obj):
        sec = obj.current_section
        return f"{sec.grade.name} — {sec.name}" if sec else None

    def get_grade_name(self, obj):
        sec = obj.current_section
        return sec.grade.name if sec else None

    def get_age(self, obj):
        from datetime import date
        if obj.date_of_birth:
            today = date.today()
            dob   = obj.date_of_birth
            return today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )
        return None

    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name  = validated_data.pop('last_name')
        email      = validated_data.pop('email')
        password   = validated_data.pop('password')

        user = User.objects.create_user(
            username  = email,
            email     = email,
            password  = password,
            first_name= first_name,
            last_name = last_name,
            role      = 'student',
        )
        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        # Remove write-only creation fields if present
        validated_data.pop('first_name', None)
        validated_data.pop('last_name',  None)
        validated_data.pop('email',      None)
        validated_data.pop('password',   None)
        return super().update(instance, validated_data)


class StudentAttendanceSummarySerializer(serializers.Serializer):
    """Read-only summary — returned by custom action"""
    student_id   = serializers.CharField()
    student_name = serializers.CharField()
    total        = serializers.IntegerField()
    present      = serializers.IntegerField()
    absent       = serializers.IntegerField()
    late         = serializers.IntegerField()
    rate         = serializers.FloatField()


# ══════════════════════════════════════════════
#  STAFF SERIALIZERS
# ══════════════════════════════════════════════

class StaffListSerializer(serializers.ModelSerializer):
    full_name    = serializers.CharField(
        source='user.get_full_name', read_only=True
    )
    email        = serializers.EmailField(
        source='user.email', read_only=True
    )
    role         = serializers.CharField(
        source='user.role', read_only=True
    )
    role_display = serializers.CharField(
        source='user.get_role_display', read_only=True
    )

    class Meta:
        model  = Staff
        fields = [
            'id', 'staff_id', 'full_name', 'email',
            'role', 'role_display',
            'department', 'qualification',
            'is_active',
        ]
        read_only_fields = ['id', 'staff_id']


class StaffDetailSerializer(serializers.ModelSerializer):
    user         = UserBasicSerializer(read_only=True)
    role_display = serializers.CharField(
        source='user.get_role_display', read_only=True
    )

    # Write-only for creation
    first_name   = serializers.CharField(write_only=True)
    last_name    = serializers.CharField(write_only=True)
    email        = serializers.EmailField(
        write_only=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password     = serializers.CharField(
        write_only=True, validators=[validate_password]
    )
    role         = serializers.ChoiceField(
        write_only=True,
        choices=[
            ('teacher', 'Teacher'), ('admin_staff', 'Admin Staff'),
            ('accountant', 'Accountant'), ('librarian', 'Librarian'),
            ('principal', 'Principal'),
        ]
    )

    class Meta:
        model  = Staff
        fields = [
            'id', 'staff_id', 'user', 'role_display',
            # write-only creation
            'first_name', 'last_name', 'email', 'password', 'role',
            # staff fields
            'department', 'qualification',
            'date_joined', 'phone_number',
            'emergency_contact', 'emergency_phone',
            'address', 'is_active',
        ]
        read_only_fields = ['id', 'staff_id', 'user']

    def create(self, validated_data):
        first_name = validated_data.pop('first_name')
        last_name  = validated_data.pop('last_name')
        email      = validated_data.pop('email')
        password   = validated_data.pop('password')
        role       = validated_data.pop('role')

        user = User.objects.create_user(
            username   = email,
            email      = email,
            password   = password,
            first_name = first_name,
            last_name  = last_name,
            role       = role,
        )
        return Staff.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        for f in ['first_name', 'last_name', 'email', 'password', 'role']:
            validated_data.pop(f, None)
        return super().update(instance, validated_data)

# apps/api/serializers.py  — PART 2
# Paste directly below Part 1 in the same file.
# Covers: Attendance · Exams · Fees · Library · Transport · Communication

from apps.attendance.models  import Attendance
from apps.exams.models       import (
    Exam, ExamSchedule, ExamComponent,
    ComponentResult, SubjectResult, ReportCard,
)
from apps.fees.models        import (
    FeeCategory, FeeStructure, StudentFee, Payment,
)
from apps.library.models     import (
    BookCategory, Author, Publisher, Book,
    BookCopy, BookIssuance, Fine,
)
from apps.transport.models   import (
    Vehicle, Route, RouteStop, StudentTransport,
)
from apps.communication.models import (
    Announcement, Notification, Event,
    MessageThread, Message,
)


# ══════════════════════════════════════════════
#  ATTENDANCE SERIALIZERS
# ══════════════════════════════════════════════

class AttendanceSerializer(serializers.ModelSerializer):
    student_name    = serializers.CharField(
        source='student.user.get_full_name', read_only=True
    )
    student_id_code = serializers.CharField(
        source='student.student_id', read_only=True
    )
    status_display  = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = Attendance
        fields = [
            'id', 'student', 'student_name', 'student_id_code',
            'date', 'status', 'status_display', 'remarks',
        ]
        read_only_fields = ['id']

    def validate_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError(
                'Attendance date cannot be in the future.'
            )
        return value


class AttendanceBulkSerializer(serializers.Serializer):
    """POST a list of attendance records at once"""
    date     = serializers.DateField()
    records  = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        min_length=1,
    )

    def validate_records(self, records):
        VALID_STATUS = {'present', 'absent', 'late', 'excused'}
        for idx, rec in enumerate(records):
            if 'student' not in rec:
                raise serializers.ValidationError(
                    f'Record {idx}: missing "student" field.'
                )
            if 'status' not in rec:
                raise serializers.ValidationError(
                    f'Record {idx}: missing "status" field.'
                )
            if rec['status'] not in VALID_STATUS:
                raise serializers.ValidationError(
                    f'Record {idx}: invalid status "{rec["status"]}".'
                )
        return records


class AttendanceSummarySerializer(serializers.Serializer):
    """Daily summary — returned by summary action"""
    date        = serializers.DateField()
    total       = serializers.IntegerField()
    present     = serializers.IntegerField()
    absent      = serializers.IntegerField()
    late        = serializers.IntegerField()
    rate        = serializers.FloatField()


# ══════════════════════════════════════════════
#  EXAM SERIALIZERS
# ══════════════════════════════════════════════

class ExamSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(
        source='academic_year.name', read_only=True
    )
    created_by_name    = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )

    class Meta:
        model  = Exam
        fields = [
            'id', 'name', 'academic_year', 'academic_year_name',
            'term', 'start_date', 'end_date',
            'is_published', 'created_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'created_by_name']


class ExamScheduleSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(
        source='subject.name', read_only=True
    )
    exam_name    = serializers.CharField(
        source='exam.name', read_only=True
    )

    class Meta:
        model  = ExamSchedule
        fields = [
            'id', 'exam', 'exam_name', 'subject', 'subject_name',
            'date', 'start_time', 'end_time',
            'room', 'invigilator',
        ]
        read_only_fields = ['id']


class ExamComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ExamComponent
        fields = [
            'id', 'exam', 'subject',
            'name', 'max_marks', 'order',
        ]
        read_only_fields = ['id']

    def validate(self, data):
        # Ensure total component marks ≤ 100 for this exam+subject
        qs = ExamComponent.objects.filter(
            exam=data.get('exam'),
            subject=data.get('subject'),
        )
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        existing = qs.aggregate(
            total=serializers.Sum('max_marks')
        )['total'] or 0
        if existing + data.get('max_marks', 0) > 100:
            raise serializers.ValidationError(
                'Total component marks cannot exceed 100.'
            )
        return data


class ComponentResultSerializer(serializers.ModelSerializer):
    student_name   = serializers.CharField(
        source='student.user.get_full_name', read_only=True
    )
    component_name = serializers.CharField(
        source='component.name', read_only=True
    )

    class Meta:
        model  = ComponentResult
        fields = [
            'id', 'component', 'component_name',
            'student', 'student_name',
            'marks_obtained', 'is_absent', 'remarks',
        ]
        read_only_fields = ['id']


class SubjectResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source='student.user.get_full_name', read_only=True
    )
    subject_name = serializers.CharField(
        source='subject.name', read_only=True
    )
    grade_label  = serializers.SerializerMethodField()

    class Meta:
        model  = SubjectResult
        fields = [
            'id', 'exam', 'student', 'student_name',
            'subject', 'subject_name',
            'total_score', 'grade_label', 'is_pass', 'remarks',
        ]
        read_only_fields = ['id', 'grade_label']

    def get_grade_label(self, obj):
        s = float(obj.total_score)
        if s >= 90: return 'Excellent'
        if s >= 80: return 'Very Good'
        if s >= 70: return 'Good'
        if s >= 60: return 'Satisfactory'
        if s >= 50: return 'Pass'
        return 'Fail'


class ReportCardSerializer(serializers.ModelSerializer):
    student_name   = serializers.CharField(
        source='student.user.get_full_name', read_only=True
    )
    student_id_code= serializers.CharField(
        source='student.student_id', read_only=True
    )
    exam_name      = serializers.CharField(
        source='exam.name', read_only=True
    )
    grade_label    = serializers.SerializerMethodField()

    class Meta:
        model  = ReportCard
        fields = [
            'id', 'exam', 'exam_name',
            'student', 'student_name', 'student_id_code',
            'average_score', 'grade_label',
            'failed_subjects', 'is_promoted',
            'teacher_remarks', 'principal_remarks',
        ]
        read_only_fields = ['id', 'grade_label']

    def get_grade_label(self, obj):
        s = float(obj.average_score)
        if s >= 90: return 'Excellent'
        if s >= 80: return 'Very Good'
        if s >= 70: return 'Good'
        if s >= 60: return 'Satisfactory'
        if s >= 50: return 'Pass'
        return 'Fail'


# ══════════════════════════════════════════════
#  FEE SERIALIZERS
# ══════════════════════════════════════════════

class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = FeeCategory
        fields = ['id', 'name', 'description', 'is_active']
        read_only_fields = ['id']


class FeeStructureSerializer(serializers.ModelSerializer):
    category_name      = serializers.CharField(
        source='fee_category.name', read_only=True
    )
    academic_year_name = serializers.CharField(
        source='academic_year.name', read_only=True
    )
    grade_name         = serializers.CharField(
        source='grade.name', read_only=True
    )

    class Meta:
        model  = FeeStructure
        fields = [
            'id', 'fee_category', 'category_name',
            'academic_year', 'academic_year_name',
            'grade', 'grade_name',
            'amount', 'due_date', 'description',
        ]
        read_only_fields = ['id']


class StudentFeeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source='student.user.get_full_name', read_only=True
    )
    category     = serializers.CharField(
        source='fee_structure.fee_category.name', read_only=True
    )
    balance      = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = StudentFee
        fields = [
            'id', 'student', 'student_name',
            'fee_structure', 'category',
            'academic_year', 'amount_due', 'amount_paid',
            'balance', 'discount', 'waiver_reason',
            'due_date', 'status', 'status_display',
        ]
        read_only_fields = ['id', 'balance']

    def get_balance(self, obj):
        return float(obj.amount_due - obj.amount_paid)


class PaymentSerializer(serializers.ModelSerializer):
    student_name    = serializers.CharField(
        source='student_fee.student.user.get_full_name', read_only=True
    )
    fee_category    = serializers.CharField(
        source='student_fee.fee_structure.fee_category.name', read_only=True
    )
    method_display  = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )

    class Meta:
        model  = Payment
        fields = [
            'id', 'student_fee', 'student_name', 'fee_category',
            'amount', 'payment_date', 'payment_method', 'method_display',
            'reference_number', 'note', 'collected_by',
        ]
        read_only_fields = ['id']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value


# ══════════════════════════════════════════════
#  LIBRARY SERIALIZERS
# ══════════════════════════════════════════════

class BookCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = BookCategory
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Author
        fields = ['id', 'name', 'bio']
        read_only_fields = ['id']


class BookListSerializer(serializers.ModelSerializer):
    category_name   = serializers.CharField(
        source='category.name', read_only=True
    )
    available_copies = serializers.SerializerMethodField()

    class Meta:
        model  = Book
        fields = [
            'id', 'title', 'isbn',
            'category', 'category_name',
            'author', 'publisher',
            'available_copies', 'is_active',
        ]
        read_only_fields = ['id']

    def get_available_copies(self, obj):
        return obj.copies.filter(status='available').count()


class BookDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name', read_only=True
    )
    total_copies     = serializers.SerializerMethodField()
    available_copies = serializers.SerializerMethodField()

    class Meta:
        model  = Book
        fields = [
            'id', 'title', 'isbn', 'edition',
            'category', 'category_name',
            'author', 'publisher',
            'published_year', 'language', 'pages',
            'description', 'shelf_location',
            'total_copies', 'available_copies',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_total_copies(self, obj):
        return obj.copies.count()

    def get_available_copies(self, obj):
        return obj.copies.filter(status='available').count()


class BookIssuanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source='student.user.get_full_name', read_only=True
    )
    book_title   = serializers.CharField(
        source='book_copy.book.title', read_only=True
    )
    days_overdue = serializers.SerializerMethodField()
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model  = BookIssuance
        fields = [
            'id', 'book_copy', 'book_title',
            'student', 'student_name',
            'issued_date', 'due_date', 'return_date',
            'status', 'status_display', 'days_overdue',
            'fine_amount', 'remarks',
        ]
        read_only_fields = ['id', 'days_overdue']

    def get_days_overdue(self, obj):
        if obj.status == 'overdue':
            from datetime import date
            return (date.today() - obj.due_date).days
        return 0


class FineSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source='issuance.student.user.get_full_name', read_only=True
    )
    book_title   = serializers.CharField(
        source='issuance.book_copy.book.title', read_only=True
    )

    class Meta:
        model  = Fine
        fields = [
            'id', 'issuance', 'student_name', 'book_title',
            'fine_type', 'total_amount', 'amount_paid',
            'status', 'issued_date', 'paid_date',
        ]
        read_only_fields = ['id']


# ══════════════════════════════════════════════
#  TRANSPORT SERIALIZERS
# ══════════════════════════════════════════════

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Vehicle
        fields = [
            'id', 'name', 'plate_number', 'vehicle_type',
            'capacity', 'driver_name', 'driver_phone',
            'is_active',
        ]
        read_only_fields = ['id']


class RouteStopSerializer(serializers.ModelSerializer):
    class Meta:
        model  = RouteStop
        fields = [
            'id', 'route', 'stop_name', 'stop_order',
            'pickup_time', 'landmark',
        ]
        read_only_fields = ['id']


class RouteSerializer(serializers.ModelSerializer):
    vehicle_name     = serializers.CharField(
        source='vehicle.name', read_only=True
    )
    vehicle_plate    = serializers.CharField(
        source='vehicle.plate_number', read_only=True
    )
    stops            = RouteStopSerializer(many=True, read_only=True)
    student_count    = serializers.SerializerMethodField()
    utilisation_pct  = serializers.SerializerMethodField()

    class Meta:
        model  = Route
        fields = [
            'id', 'name', 'start_point', 'end_point',
            'vehicle', 'vehicle_name', 'vehicle_plate',
            'departure_time', 'return_time', 'monthly_fee',
            'direction', 'is_active',
            'stops', 'student_count', 'utilisation_pct',
        ]
        read_only_fields = ['id']

    def get_student_count(self, obj):
        return obj.student_transports.filter(is_active=True).count()

    def get_utilisation_pct(self, obj):
        if obj.vehicle and obj.vehicle.capacity:
            count = obj.student_transports.filter(is_active=True).count()
            return round(count / obj.vehicle.capacity * 100, 1)
        return None


class StudentTransportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(
        source='student.user.get_full_name', read_only=True
    )
    route_name   = serializers.CharField(
        source='route.name', read_only=True
    )
    stop_name    = serializers.CharField(
        source='stop.stop_name', read_only=True
    )

    class Meta:
        model  = StudentTransport
        fields = [
            'id', 'student', 'student_name',
            'route', 'route_name', 'stop', 'stop_name',
            'academic_year', 'start_date', 'is_active', 'notes',
        ]
        read_only_fields = ['id']


# ══════════════════════════════════════════════
#  COMMUNICATION SERIALIZERS
# ══════════════════════════════════════════════

class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )
    audience_display = serializers.CharField(
        source='get_audience_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    status           = serializers.CharField(
        source='status_label', read_only=True
    )
    is_active        = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Announcement
        fields = [
            'id', 'title', 'body',
            'audience', 'audience_display',
            'priority', 'priority_display',
            'target_grade', 'target_section',
            'is_published', 'publish_date', 'expiry_date',
            'status', 'is_active',
            'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'is_active',
            'created_by_name', 'created_at', 'updated_at',
        ]


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(
        source='get_notif_type_display', read_only=True
    )

    class Meta:
        model  = Notification
        fields = [
            'id', 'notif_type', 'type_display',
            'title', 'body', 'link',
            'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source='get_category_display', read_only=True
    )
    audience_display = serializers.CharField(
        source='get_audience_display', read_only=True
    )
    state            = serializers.SerializerMethodField()
    duration_days    = serializers.IntegerField(read_only=True)
    created_by_name  = serializers.CharField(
        source='created_by.get_full_name', read_only=True
    )

    class Meta:
        model  = Event
        fields = [
            'id', 'title', 'description',
            'category', 'category_display',
            'start_date', 'end_date', 'all_day',
            'location', 'audience', 'audience_display',
            'is_published', 'state', 'duration_days',
            'created_by_name', 'created_at',
        ]
        read_only_fields = ['id', 'state', 'duration_days', 'created_at']

    def get_state(self, obj):
        if obj.is_ongoing:  return 'ongoing'
        if obj.is_upcoming: return 'upcoming'
        return 'past'

    def validate(self, data):
        s = data.get('start_date')
        e = data.get('end_date')
        if s and e and e < s:
            raise serializers.ValidationError('End date must be after start date.')
        return data


class MessageSerializer(serializers.ModelSerializer):
    sender_name  = serializers.CharField(
        source='sender.get_full_name', read_only=True
    )
    is_read      = serializers.SerializerMethodField()

    class Meta:
        model  = Message
        fields = [
            'id', 'thread', 'sender', 'sender_name',
            'body', 'sent_at', 'is_read',
        ]
        read_only_fields = ['id', 'sent_at', 'sender']

    def get_is_read(self, obj):
        request = self.context.get('request')
        if request:
            return obj.is_read_by(request.user)
        return False


class MessageThreadSerializer(serializers.ModelSerializer):
    participants     = UserBasicSerializer(many=True, read_only=True)
    last_message     = serializers.SerializerMethodField()
    unread_count     = serializers.SerializerMethodField()
    message_count    = serializers.SerializerMethodField()

    class Meta:
        model  = MessageThread
        fields = [
            'id', 'subject', 'participants',
            'last_message', 'unread_count', 'message_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        msg = obj.last_message
        if msg:
            return {
                'sender': msg.sender.get_full_name(),
                'body':   msg.body[:80],
                'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M'),
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        return obj.unread_count(request.user) if request else 0

    def get_message_count(self, obj):
        return obj.messages.count()
