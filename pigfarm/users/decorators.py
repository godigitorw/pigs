from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import UserActivity

def role_required(allowed_roles):
    """
    Decorator to check if user has required role
    Usage: @role_required(['farm_owner', 'farm_manager'])
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not request.user.role:
                messages.error(request, "Access denied: No role assigned.")
                return redirect('dashboard')

            if request.user.role.name not in allowed_roles:
                messages.error(request, "Access denied: Insufficient permissions.")
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def permission_required(permission_codename):
    """
    Decorator to check if user has specific permission
    Usage: @permission_required('farm.add')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not request.user.has_permission(permission_codename):
                messages.error(request, "Access denied: You don't have permission to perform this action.")
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def module_access_required(module_name):
    """
    Decorator to check if user has access to specific module
    Usage: @module_access_required('feeding')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if not request.user.has_module_access(module_name):
                messages.error(request, f"Access denied: No access to {module_name.title()} module.")
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def log_user_activity(action, module, object_id=None, object_repr=None, additional_data=None):
    """
    Decorator to log user activities
    Usage: @log_user_activity('create', 'farm', object_id='sow_id')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)

            if request.user.is_authenticated:
                # Get IP address
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')

                # Create activity log
                UserActivity.objects.create(
                    user=request.user,
                    action=action,
                    module=module,
                    object_id=str(object_id) if object_id else None,
                    object_repr=str(object_repr) if object_repr else None,
                    ip_address=ip,
                    additional_data=additional_data
                )

            return response
        return wrapped_view
    return decorator

def farm_owner_required(view_func):
    """Shortcut decorator for farm owner only access"""
    return role_required(['farm_owner'])(view_func)

def farm_manager_or_owner_required(view_func):
    """Shortcut decorator for farm manager or owner access"""
    return role_required(['farm_owner', 'farm_manager'])(view_func)

def financial_access_required(view_func):
    """Shortcut decorator for financial module access"""
    return role_required(['farm_owner', 'accountant'])(view_func)

def read_only_check(view_func):
    """
    Decorator to check if user has read-only access and prevent modifications
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if request.user.role and request.user.role.name == 'viewer':
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                messages.error(request, "Access denied: You have read-only access.")
                return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

        return view_func(request, *args, **kwargs)
    return wrapped_view