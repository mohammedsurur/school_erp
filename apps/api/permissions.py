# apps/api/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


# ─────────────────────────────────────────────
#  Role helpers
# ─────────────────────────────────────────────

ADMIN_ROLES    = {'super_admin', 'principal', 'admin_staff'}
STAFF_ROLES    = {'super_admin', 'principal', 'admin_staff', 'teacher',
                  'accountant', 'librarian'}
FINANCE_ROLES  = {'super_admin', 'principal', 'admin_staff', 'accountant'}
LIBRARY_ROLES  = {'super_admin', 'principal', 'admin_staff', 'librarian'}
TEACHER_ROLES  = {'super_admin', 'principal', 'admin_staff', 'teacher'}


def _role(request):
    return getattr(request.user, 'role', None)


# ─────────────────────────────────────────────
#  Generic role-based permission factory
# ─────────────────────────────────────────────

def RolePermission(*allowed_roles):
    """
    Factory — returns a permission class that grants access
    only to users whose role is in `allowed_roles`.

    Usage:
        permission_classes = [RolePermission('super_admin', 'principal')]
    """
    allowed = set(allowed_roles)

    class _Permission(BasePermission):
        message = 'You do not have permission to perform this action.'

        def has_permission(self, request, view):
            return (
                request.user
                and request.user.is_authenticated
                and _role(request) in allowed
            )

    _Permission.__name__ = f"RolePermission({'|'.join(sorted(allowed))})"
    return _Permission


# ─────────────────────────────────────────────
#  Named permissions
# ─────────────────────────────────────────────

class IsAdminRole(BasePermission):
    """super_admin | principal | admin_staff"""
    message = 'Admin access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and _role(request) in ADMIN_ROLES
        )


class IsStaffRole(BasePermission):
    """Any staff member (not student / parent)"""
    message = 'Staff access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and _role(request) in STAFF_ROLES
        )


class IsTeacherOrAdmin(BasePermission):
    """teacher | admin roles"""
    message = 'Teacher or admin access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and _role(request) in TEACHER_ROLES
        )


class IsFinanceRole(BasePermission):
    """admin | accountant — read/write on fee data"""
    message = 'Finance access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and _role(request) in FINANCE_ROLES
        )


class IsLibraryRole(BasePermission):
    """admin | librarian"""
    message = 'Library access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and _role(request) in LIBRARY_ROLES
        )


class IsSuperAdmin(BasePermission):
    """super_admin only"""
    message = 'Super admin access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and _role(request) == 'super_admin'
        )


class IsPrincipalOrAbove(BasePermission):
    """super_admin | principal"""
    message = 'Principal access required.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and _role(request) in {'super_admin', 'principal'}
        )


# ─────────────────────────────────────────────
#  Mixed read/write permissions
# ─────────────────────────────────────────────

class IsAdminOrReadOnlyForStaff(BasePermission):
    """
    SAFE_METHODS (GET, HEAD, OPTIONS) → any staff
    Unsafe methods → admin only
    """
    message = 'Write access requires admin role.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        role = _role(request)
        if request.method in SAFE_METHODS:
            return role in STAFF_ROLES
        return role in ADMIN_ROLES


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level: user can access their own record,
    admins can access any record.
    Expects the object to have a `.user` attribute.
    """
    message = 'You can only access your own records.'

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if _role(request) in ADMIN_ROLES:
            return True
        return getattr(obj, 'user', None) == request.user


class IsStudentOwnerOrStaff(BasePermission):
    """
    Students can read their own data (GET).
    Staff can read all. Admins can write.
    Expects object to have `.student.user` or `.user`.
    """
    message = 'Access denied.'

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        role = _role(request)
        if role in ADMIN_ROLES:
            return True
        if role in STAFF_ROLES and request.method in SAFE_METHODS:
            return True
        # Student accessing their own record
        if role == 'student':
            if request.method not in SAFE_METHODS:
                return False
            user = (
                getattr(obj, 'user', None)
                or getattr(getattr(obj, 'student', None), 'user', None)
            )
            return user == request.user
        # Parent — read-only for their child's data
        if role == 'parent' and request.method in SAFE_METHODS:
            student_user = getattr(
                getattr(obj, 'student', None), 'user', None
            )
            if student_user:
                return student_user.parent == request.user
        return False