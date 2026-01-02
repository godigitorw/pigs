# farm/task_utils.py
"""
Utility functions for sending task reminder emails
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_task_reminder_email(task, recipient_email):
    """
    Send email reminder for a pig task
    """
    subject = f"Reminder: {task.get_task_type_display()} for {task.pig_name}"
    
    context = {
        'task': task,
        'pig_name': task.pig_name,
        'task_type': task.get_task_type_display(),
        'due_date': task.due_date,
        'days_until_due': task.days_until_due,
        'description': task.description,
    }
    
    # Plain text message
    message = f"""
Pig Farm Task Reminder

Task: {task.get_task_type_display()}
Pig: {task.pig_name} ({task.get_pig_type_display()})
Due Date: {task.due_date}
Days Until Due: {task.days_until_due}

Description:
{task.description or 'No additional notes'}

Please complete this task before the due date.

---
Pig Farm Management System
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def check_and_send_reminders(user_email):
    """
    Check all pending tasks and send reminders if needed
    Returns number of reminders sent
    """
    from farm.models import PigTask
    
    # Get tasks that need reminders
    tasks_needing_reminder = PigTask.objects.filter(
        status='pending',
        send_email=True,
        email_sent=False
    )
    
    sent_count = 0
    for task in tasks_needing_reminder:
        if task.should_send_reminder:
            if send_task_reminder_email(task, user_email):
                task.email_sent = True
                task.save()
                sent_count += 1
    
    return sent_count
