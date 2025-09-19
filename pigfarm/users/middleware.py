from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import UserSession, UserActivity
from django.utils import timezone

User = get_user_model()

class UserSessionMiddleware(MiddlewareMixin):
    """
    Middleware to track user sessions and activities
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            # Update last login IP
            if request.user.last_login_ip != ip:
                request.user.last_login_ip = ip
                request.user.save(update_fields=['last_login_ip'])

            # Update or create session record
            session_key = request.session.session_key
            if session_key:
                user_session, created = UserSession.objects.get_or_create(
                    session_key=session_key,
                    defaults={
                        'user': request.user,
                        'ip_address': ip,
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:255],
                    }
                )

                if not created:
                    user_session.last_activity = timezone.now()
                    user_session.save(update_fields=['last_activity'])

class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware to check role-based access for certain URLs
    """

    # Define URL patterns that require specific roles
    PROTECTED_URLS = {
        '/admin/': ['farm_owner'],
        '/users/': ['farm_owner', 'farm_manager'],
        '/reports/finance': ['farm_owner', 'accountant'],
        '/farm/delete': ['farm_owner', 'farm_manager'],
        '/health/delete': ['farm_owner', 'farm_manager'],
        '/feeding/delete': ['farm_owner', 'farm_manager', 'feed_manager'],
    }

    def process_request(self, request):
        if request.user.is_authenticated and request.user.role:
            # Check if the current URL requires specific role access
            current_path = request.path

            for protected_url, allowed_roles in self.PROTECTED_URLS.items():
                if current_path.startswith(protected_url):
                    if request.user.role.name not in allowed_roles:
                        from django.contrib import messages
                        from django.shortcuts import redirect
                        messages.error(request, "Access denied: Insufficient permissions for this section.")
                        return redirect('dashboard')

        return None

class ActivityLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log certain user activities
    """

    def process_response(self, request, response):
        # Only log for authenticated users and successful requests
        if (request.user.is_authenticated and
            200 <= response.status_code < 300 and
            request.method in ['POST', 'PUT', 'PATCH', 'DELETE']):

            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            # Determine action based on method
            action_map = {
                'POST': 'create',
                'PUT': 'update',
                'PATCH': 'update',
                'DELETE': 'delete'
            }

            action = action_map.get(request.method, 'unknown')

            # Determine module from URL
            path_parts = request.path.strip('/').split('/')
            module = path_parts[0] if path_parts else 'unknown'

            # Don't log certain paths
            if module not in ['admin', 'static', 'media', '__debug__']:
                try:
                    UserActivity.objects.create(
                        user=request.user,
                        action=action,
                        module=module,
                        object_id=None,
                        object_repr=f"{request.method} {request.path}",
                        ip_address=ip
                    )
                except Exception:
                    # Silently fail if logging fails
                    pass

        return response