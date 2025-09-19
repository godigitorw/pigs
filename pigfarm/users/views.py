from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from .models import CustomUser, UserRole, Permission, RolePermission, UserActivity, UserSession
from .decorators import role_required, permission_required, farm_owner_required, log_user_activity
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

@farm_owner_required
def user_management(request):
    """User management dashboard - only for Farm Owner"""
    users = CustomUser.objects.select_related('role').all()
    roles = UserRole.objects.filter(is_active=True)

    # Search functionality
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(employee_id__icontains=search)
        )

    # Role filter
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role__name=role_filter)

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True, is_active_employee=True)
    elif status_filter == 'inactive':
        users = users.filter(Q(is_active=False) | Q(is_active_employee=False))

    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)

    # Get recent activities
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:10]

    # Get active sessions
    active_sessions = UserSession.objects.filter(
        is_active=True,
        last_activity__gte=timezone.now() - timezone.timedelta(hours=24)
    ).select_related('user').order_by('-last_activity')[:10]

    context = {
        'users': users_page,
        'roles': roles,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'recent_activities': recent_activities,
        'active_sessions': active_sessions,
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True, is_active_employee=True).count(),
    }

    return render(request, 'users/user_management.html', context)

@farm_owner_required
@log_user_activity('create', 'users')
def create_user(request):
    """Create new user - only for Farm Owner"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role_id = request.POST.get('role')
        employee_id = request.POST.get('employee_id')
        phone_number = request.POST.get('phone_number')
        department = request.POST.get('department')

        # Basic validation
        if not all([username, email, password, role_id]):
            messages.error(request, 'All required fields must be filled.')
            return redirect('users:user_management')

        # Check if username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('users:user_management')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('users:user_management')

        # Check employee_id uniqueness if provided
        if employee_id and CustomUser.objects.filter(employee_id=employee_id).exists():
            messages.error(request, 'Employee ID already exists.')
            return redirect('users:user_management')

        try:
            role = UserRole.objects.get(id=role_id)

            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                employee_id=employee_id,
                phone_number=phone_number,
                department=department,
                created_by=request.user,
                hire_date=timezone.now().date()
            )

            messages.success(request, f'User {username} created successfully.')
            return redirect('users:user_management')

        except UserRole.DoesNotExist:
            messages.error(request, 'Invalid role selected.')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')

    return redirect('users:user_management')

@farm_owner_required
def edit_user(request, user_id):
    """Edit user details - only for Farm Owner"""
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'GET':
        # Return user data as JSON for populating the edit modal
        try:
            user_data = {
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email or '',
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'employee_id': user.employee_id or '',
                    'phone_number': user.phone_number or '',
                    'department': user.department or '',
                    'role_id': user.role.id if user.role else None,
                    'is_active': user.is_active,
                    'is_active_employee': user.is_active_employee,
                }
            }
            return JsonResponse(user_data)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    elif request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.department = request.POST.get('department', user.department)
        user.employee_id = request.POST.get('employee_id', user.employee_id)

        # Update role if provided
        role_id = request.POST.get('role')
        if role_id:
            try:
                role = UserRole.objects.get(id=role_id)
                user.role = role
            except UserRole.DoesNotExist:
                messages.error(request, 'Invalid role selected.')
                return redirect('users:user_management')

        # Update status
        user.is_active = request.POST.get('is_active') == 'true'
        user.is_active_employee = request.POST.get('is_active_employee') == 'true'

        user.save()
        messages.success(request, f'User {user.username} updated successfully.')

    return redirect('users:user_management')

@farm_owner_required
@log_user_activity('delete', 'users')
def delete_user(request, user_id):
    """Deactivate user - only for Farm Owner"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)

        # Don't allow deleting the current user
        if user == request.user:
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('users:user_management')

        # Deactivate instead of delete
        user.is_active = False
        user.is_active_employee = False
        user.save()

        messages.success(request, f'User {user.username} deactivated successfully.')

    return redirect('users:user_management')

@role_required(['farm_owner', 'farm_manager'])
def role_permissions(request):
    """View and manage role permissions"""
    roles = UserRole.objects.prefetch_related('permissions__permission').filter(is_active=True)
    permissions = Permission.objects.all().order_by('module', 'permission_type')

    context = {
        'roles': roles,
        'permissions': permissions,
    }

    return render(request, 'users/role_permissions.html', context)

@login_required
def profile(request):
    """User profile view and edit"""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.email = request.POST.get('email', request.user.email)
            request.user.phone_number = request.POST.get('phone_number', request.user.phone_number)
            request.user.address = request.POST.get('address', request.user.address)
            request.user.emergency_contact = request.POST.get('emergency_contact', request.user.emergency_contact)
            request.user.emergency_phone = request.POST.get('emergency_phone', request.user.emergency_phone)

            request.user.save()
            messages.success(request, 'Profile updated successfully.')

        elif action == 'change_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
            else:
                for error in form.errors.values():
                    messages.error(request, error[0])

    # Get user's recent activities
    recent_activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:20]

    # Get user's sessions
    user_sessions = UserSession.objects.filter(user=request.user, is_active=True).order_by('-last_activity')

    context = {
        'recent_activities': recent_activities,
        'user_sessions': user_sessions,
    }

    return render(request, 'users/profile.html', context)

@role_required(['farm_owner', 'farm_manager'])
def activity_logs(request):
    """View user activity logs"""
    activities = UserActivity.objects.select_related('user').order_by('-timestamp')

    # Filters
    user_filter = request.GET.get('user', '')
    if user_filter:
        activities = activities.filter(user__username__icontains=user_filter)

    action_filter = request.GET.get('action', '')
    if action_filter:
        activities = activities.filter(action=action_filter)

    module_filter = request.GET.get('module', '')
    if module_filter:
        activities = activities.filter(module=module_filter)

    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)

    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    activities_page = paginator.get_page(page_number)

    context = {
        'activities': activities_page,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'users/activity_logs.html', context)

@farm_owner_required
def user_sessions(request):
    """View active user sessions"""
    sessions = UserSession.objects.select_related('user').filter(is_active=True).order_by('-last_activity')

    context = {
        'sessions': sessions,
    }

    return render(request, 'users/user_sessions.html', context)

@farm_owner_required
def revoke_session(request, session_id):
    """Revoke user session"""
    if request.method == 'POST':
        session = get_object_or_404(UserSession, id=session_id)
        session.is_active = False
        session.save()

        messages.success(request, f'Session for {session.user.username} revoked successfully.')

    return redirect('users:user_sessions')

def ajax_check_username(request):
    """AJAX endpoint to check username availability"""
    username = request.GET.get('username', '')
    is_available = not CustomUser.objects.filter(username=username).exists()

    return JsonResponse({'available': is_available})

def ajax_check_email(request):
    """AJAX endpoint to check email availability"""
    email = request.GET.get('email', '')
    is_available = not CustomUser.objects.filter(email=email).exists()

    return JsonResponse({'available': is_available})
