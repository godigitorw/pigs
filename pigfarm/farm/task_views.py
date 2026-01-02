# farm/task_views.py
"""
Views for pig task management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import date, timedelta
from .models import PigTask, Sow, Piglet
from .forms import PigTaskForm

@login_required
def task_list(request):
    """List all tasks with filtering"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    pig_type_filter = request.GET.get('pig_type', '')
    task_type_filter = request.GET.get('task_type', '')
    
    # Base queryset
    tasks = PigTask.objects.all().select_related('sow', 'piglet', 'created_by')
    
    # Apply filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if pig_type_filter:
        tasks = tasks.filter(pig_type=pig_type_filter)
    if task_type_filter:
        tasks = tasks.filter(task_type=task_type_filter)
    
    # Pagination
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get upcoming tasks (next 7 days)
    today = date.today()
    upcoming_tasks = PigTask.objects.filter(
        status='pending',
        due_date__range=[today, today + timedelta(days=7)]
    ).order_by('due_date')[:5]
    
    # Get overdue tasks
    overdue_tasks = PigTask.objects.filter(
        status__in=['pending', 'overdue'],
        due_date__lt=today
    ).count()
    
    context = {
        'page_obj': page_obj,
        'upcoming_tasks': upcoming_tasks,
        'overdue_count': overdue_tasks,
        'status_filter': status_filter,
        'pig_type_filter': pig_type_filter,
        'task_type_filter': task_type_filter,
        'task_statuses': PigTask.STATUS_CHOICES,
        'pig_types': PigTask.PIG_TYPE_CHOICES,
        'task_types': PigTask.TASK_TYPE_CHOICES,
    }
    
    return render(request, 'farm/task_list.html', context)


@login_required
def task_create(request):
    """Create a new task"""
    if request.method == 'POST':
        form = PigTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('task_list')
    else:
        form = PigTaskForm()
    
    context = {'form': form}
    return render(request, 'farm/task_form.html', context)


@login_required
def task_edit(request, pk):
    """Edit an existing task"""
    task = get_object_or_404(PigTask, pk=pk)
    
    if request.method == 'POST':
        form = PigTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_list')
    else:
        form = PigTaskForm(instance=task)
    
    context = {'form': form, 'task': task}
    return render(request, 'farm/task_form.html', context)


@login_required
def task_complete(request, pk):
    """Mark a task as completed"""
    task = get_object_or_404(PigTask, pk=pk)
    
    if request.method == 'POST':
        task.status = 'completed'
        task.completed_date = date.today()
        task.save()
        messages.success(request, f'Task "{task.title}" marked as completed!')
        return redirect('task_list')
    
    context = {'task': task}
    return render(request, 'farm/task_complete_confirm.html', context)


@login_required
def task_delete(request, pk):
    """Delete a task"""
    task = get_object_or_404(PigTask, pk=pk)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('task_list')
    
    context = {'task': task}
    return render(request, 'farm/task_delete_confirm.html', context)


@login_required
def pig_tasks(request, pig_type, pig_id):
    """View all tasks for a specific pig"""
    if pig_type == 'sow':
        pig = get_object_or_404(Sow, pk=pig_id)
        tasks = PigTask.objects.filter(sow=pig)
    else:
        pig = get_object_or_404(Piglet, pk=pig_id)
        tasks = PigTask.objects.filter(piglet=pig)
    
    # Separate by status
    pending_tasks = tasks.filter(status='pending').order_by('due_date')
    overdue_tasks = tasks.filter(status='overdue').order_by('due_date')
    completed_tasks = tasks.filter(status='completed').order_by('-completed_date')
    
    context = {
        'pig': pig,
        'pig_type': pig_type,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'completed_tasks': completed_tasks,
    }
    
    return render(request, 'farm/pig_tasks.html', context)
