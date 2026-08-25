from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .models import User
from .forms import (
    LoginForm, ProfileUpdateForm,
    CustomPasswordChangeForm, UserCreateForm
)
from apps.core.decorators import role_required, admin_required


# ── Authentication ─────────────────────────────────────────────────


def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        remember  = form.cleaned_data.get('remember_me', False)

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # Session expiry
            if not remember:
                request.session.set_expiry(0)   # closes when browser closes
            else:
                request.session.set_expiry(60 * 60 * 24 * 7)  # 7 days

            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', user.get_dashboard_url())
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('login')
    return redirect('login')


def access_denied_view(request):
    return render(request, 'accounts/access_denied.html', status=403)


# ── Profile ────────────────────────────────────────────────────────


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def profile_update_view(request):
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')

    return render(request, 'accounts/profile_update.html', {'form': form})


@login_required
def change_password_view(request):
    form = CustomPasswordChangeForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)   # keeps user logged in
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')

    return render(request, 'accounts/change_password.html', {'form': form})


# ── User Management (Admin only) ───────────────────────────────────


@admin_required
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')

    # Filter by role
    role = request.GET.get('role', '')
    if role:
        users = users.filter(role=role)

    # Search
    q = request.GET.get('q', '')
    if q:
        users = users.filter(
            username__icontains=q
        ) | users.filter(
            first_name__icontains=q
        ) | users.filter(
            last_name__icontains=q
        ) | users.filter(
            email__icontains=q
        )

    # Paginate
    paginator = Paginator(users, 20)
    page      = request.GET.get('page', 1)
    users     = paginator.get_page(page)

    roles = User.ROLE_CHOICES
    return render(request, 'accounts/user_list.html', {
        'users':        users,
        'roles':        roles,
        'current_role': role,
        'q':            q,
    })


@admin_required
def user_create_view(request):
    form = UserCreateForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f'User "{user.username}" created successfully.')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'form':  form,
        'title': 'Create New User',
    })


@admin_required
def user_update_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = ProfileUpdateForm(
        request.POST or None,
        request.FILES or None,
        instance=user
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'User "{user.username}" updated successfully.')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'form':  form,
        'title': f'Edit — {user.get_full_name()}',
        'user_obj': user,
    })


@admin_required
def user_toggle_active_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You can't deactivate your own account.")
    else:
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User "{user.username}" {status}.')
    return redirect('user_list')