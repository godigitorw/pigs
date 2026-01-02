# users/views.py - Add this new view
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import UserActivity
from django.db.models import Q

@login_required
def activity_logs_view(request):
    """
    View for admins to see all user activities.
    Farm workers' actions will be logged here.
    """
    # Only allow farm owners to view activity logs
    if not (hasattr(request.user, 'role') and request.user.role and request.user.role.name == 'farm_owner'):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "You don't have permission to view activity logs.")
        return redirect('dashboard')
    
    # Get filter parameters
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    module_filter = request.GET.get('module', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Start with all activities
    activities = UserActivity.objects.all().select_related('user')
    
    # Apply filters
    if user_filter:
        activities = activities.filter(user__username__icontains=user_filter)
    if action_filter:
        activities = activities.filter(action=action_filter)
    if module_filter:
        activities = activities.filter(module__icontains=module_filter)
    if date_from:
        activities = activities.filter(timestamp__date__gte=date_from)
    if date_to:
        activities = activities.filter(timestamp__date__lte=date_to)
    
    # Paginate
    paginator = Paginator(activities, 50)  # Show 50 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'date_from': date_from,
        'date_to': date_to,
        'action_choices': UserActivity.ACTION_CHOICES,
    }
    
    return render(request, 'users/activity_logs.html', context)
