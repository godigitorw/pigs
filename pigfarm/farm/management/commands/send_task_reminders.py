# farm/management/commands/send_task_reminders.py
"""
Management command to send task reminder emails
Run this daily via cron or scheduler
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from farm.models import PigTask
from farm.task_utils import send_task_reminder_email

User = get_user_model()

class Command(BaseCommand):
    help = 'Send email reminders for upcoming pig tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Specific email to send reminders to (default: all farm owners)',
        )
    
    def handle(self, *args, **options):
        email = options.get('email')
        
        # Get tasks that need reminders
        tasks_needing_reminder = PigTask.objects.filter(
            status='pending',
            send_email=True,
            email_sent=False
        )
        
        sent_count = 0
        failed_count = 0
        
        for task in tasks_needing_reminder:
            # Check if reminder should be sent
            if task.should_send_reminder:
                # Determine recipient
                if email:
                    recipient_email = email
                else:
                    # Send to farm owner
                    farm_owners = User.objects.filter(
                        role__name='farm_owner',
                        is_active=True
                    )
                    if not farm_owners.exists():
                        self.stdout.write(self.style.WARNING('No farm owners found'))
                        continue
                    recipient_email = farm_owners.first().email
                    
                    if not recipient_email:
                        self.stdout.write(
                            self.style.WARNING(f'No email for user {farm_owners.first().username}')
                        )
                        continue
                
                # Send email
                if send_task_reminder_email(task, recipient_email):
                    task.email_sent = True
                    task.save()
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Reminder sent for: {task.title}')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to send reminder for: {task.title}')
                    )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Sent: {sent_count} reminders'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed_count} reminders'))
        
        if sent_count == 0 and failed_count == 0:
            self.stdout.write(self.style.WARNING('No reminders needed at this time'))
