from django.shortcuts import redirect
from django.contrib   import messages
from functools        import wraps


# ─────────────────────────────────────────────
#  Generic role checker
# ─────────────────────────────────────────────

def role_required(*roles):
    """
    Allow only the specified role(s).

    Usage:
        @role_required('teacher', 'principal')
        def my_view(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login to continue.')
                return redirect('login')
            if request.user.role not in roles:
                messages.error(
                    request,
                    'You do not have permission to access this page.'
                )
                return redirect('access_denied')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────
#  Admin — all 3 school admin roles
# ─────────────────────────────────────────────

def admin_required(view_func):
    """
    Allow: super_admin, principal, admin_staff.
    Use for pages all admin roles can access
    (students, staff list, enrollment, reports).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if not request.user.is_school_admin():
            messages.error(
                request,
                'Admin access required.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  Principal or above — destructive / sensitive
# ─────────────────────────────────────────────

def principal_or_above(view_func):
    """
    Allow: super_admin, principal ONLY.
    Use for:
      - Creating / deleting users
      - School settings
      - Adding / editing staff
      - Creating grades, subjects, sections
      - Assigning subjects to teachers
      - Building timetable
    admin_staff CANNOT access these views.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if request.user.role not in ['super_admin', 'principal']:
            messages.error(
                request,
                'Principal or Super Admin access required '
                'for this action.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  Super Admin only — system-level
# ─────────────────────────────────────────────

def super_admin_required(view_func):
    """
    Allow: super_admin ONLY.
    Use for:
      - Audit log
      - Django admin access
      - System configuration
      - Deleting academic years
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if request.user.role != 'super_admin':
            messages.error(
                request,
                'Super Admin access required for this action.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  Teacher
# ─────────────────────────────────────────────

def teacher_required(view_func):
    """
    Allow: teacher, principal, super_admin.
    Use for:
      - Marking attendance
      - Entering exam marks
      - Viewing assigned classes
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if request.user.role not in ['teacher', 'principal', 'super_admin']:
            messages.error(
                request,
                'Teacher access required.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  Student
# ─────────────────────────────────────────────

def student_required(view_func):
    """
    Allow: student ONLY.
    Use for:
      - Student dashboard
      - Viewing own results, attendance, fees
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if request.user.role != 'student':
            messages.error(
                request,
                'Student access required.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  Parent
# ─────────────────────────────────────────────

def parent_required(view_func):
    """
    Allow: parent ONLY.
    Use for:
      - Parent dashboard
      - Viewing child progress, fees, attendance
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if request.user.role != 'parent':
            messages.error(
                request,
                'Parent access required.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  Librarian
# ─────────────────────────────────────────────

def librarian_required(view_func):
    """
    Allow: librarian, principal, super_admin.
    Use for:
      - Book catalog management
      - Issue and return
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if request.user.role not in ['librarian', 'principal', 'super_admin']:
            messages.error(
                request,
                'Librarian access required.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
#  Accountant
# ─────────────────────────────────────────────

def accountant_required(view_func):
    """
    Allow: accountant, principal, super_admin.
    Use for:
      - Fee collection
      - Payment records
      - Financial reports
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        if request.user.role not in ['accountant', 'principal', 'super_admin']:
            messages.error(
                request,
                'Accountant access required.'
            )
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper