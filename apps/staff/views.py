from django.shortcuts      import render, redirect, get_object_or_404
from django.contrib        import messages
from django.core.paginator import Paginator
from django.db.models      import Q

from apps.core.decorators  import *
from .models               import Staff
from .forms                import StaffUserForm, StaffProfileForm, StaffEditForm


# ─────────────────────────────────────────────
#  Staff List
# ─────────────────────────────────────────────

@admin_required
def staff_list(request):
    staff = Staff.objects.select_related(
        'user'
    ).order_by('-join_date')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        staff = staff.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)  |
            Q(staff_id__icontains=q)         |
            Q(department__icontains=q)       |
            Q(user__email__icontains=q)
        )

    # Filter by staff type
    staff_type = request.GET.get('type', '')
    if staff_type:
        staff = staff.filter(staff_type=staff_type)

    # Filter by status
    status = request.GET.get('status', '')
    if status == 'active':
        staff = staff.filter(is_active=True)
    elif status == 'inactive':
        staff = staff.filter(is_active=False)

    paginator = Paginator(staff, 20)
    page      = request.GET.get('page', 1)
    staff     = paginator.get_page(page)

    staff_types = Staff.STAFF_TYPE

    return render(request, 'staff/staff_list.html', {
        'staff':       staff,
        'staff_types': staff_types,
        'q':           q,
        'staff_type':  staff_type,
        'status':      status,
        'page_title':  'Staff',
    })


# ─────────────────────────────────────────────
#  Add Staff
# ─────────────────────────────────────────────

@principal_or_above
def staff_create(request):
    user_form    = StaffUserForm(request.POST or None)
    profile_form = StaffProfileForm(
        request.POST  or None,
        request.FILES or None
    )

    if request.method == 'POST':
        if user_form.is_valid() and profile_form.is_valid():
            # Create user account
            user = user_form.save()

            # Create staff profile
            staff         = profile_form.save(commit=False)
            staff.user    = user
            staff.staff_id = Staff.generate_staff_id()
            staff.save()

            messages.success(
                request,
                f'Staff "{user.get_full_name()}" added. '
                f'Staff ID: {staff.staff_id}'
            )
            return redirect('staff_detail', pk=staff.pk)
        else:
            messages.error(request, 'Please fix the errors below.')

    return render(request, 'staff/staff_form.html', {
        'user_form':    user_form,
        'profile_form': profile_form,
        'title':        'Add New Staff',
        'page_title':   'Add Staff',
    })


# ─────────────────────────────────────────────
#  Staff Detail
# ─────────────────────────────────────────────

@admin_required
def staff_detail(request, pk):
    staff = get_object_or_404(
        Staff.objects.select_related('user'),
        pk=pk
    )
    return render(request, 'staff/staff_detail.html', {
        'staff':      staff,
        'page_title': f'{staff.user.get_full_name()} — Profile',
    })


# ─────────────────────────────────────────────
#  Edit Staff
# ─────────────────────────────────────────────

@principal_or_above
def staff_edit(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    form  = StaffEditForm(
        request.POST  or None,
        request.FILES or None,
        instance=staff
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request,
            f'Staff "{staff.user.get_full_name()}" updated successfully.'
        )
        return redirect('staff_detail', pk=staff.pk)

    return render(request, 'staff/staff_edit.html', {
        'form':       form,
        'staff':      staff,
        'title':      f'Edit — {staff.user.get_full_name()}',
        'page_title': 'Edit Staff',
    })


# ─────────────────────────────────────────────
#  Toggle Active
# ─────────────────────────────────────────────

@principal_or_above
def staff_toggle_active(request, pk):
    staff            = get_object_or_404(Staff, pk=pk)
    staff.is_active  = not staff.is_active
    staff.user.is_active = staff.is_active
    staff.user.save()
    staff.save()
    status = 'activated' if staff.is_active else 'deactivated'
    messages.success(
        request,
        f'Staff "{staff.user.get_full_name()}" {status}.'
    )
    return redirect('staff_detail', pk=staff.pk)