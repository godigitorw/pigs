"""
Management command to force apply specific migrations
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Force apply all pending migrations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting forced migration...'))

        # Show current migration status
        self.stdout.write(self.style.WARNING('\n=== Migration Status BEFORE ==='))
        call_command('showmigrations', 'farm')

        # Run migrate with fake-initial to handle existing tables
        self.stdout.write(self.style.WARNING('\n=== Running Migration ==='))
        call_command('migrate', 'farm', '--verbosity=2')

        # Show migration status after
        self.stdout.write(self.style.WARNING('\n=== Migration Status AFTER ==='))
        call_command('showmigrations', 'farm')

        self.stdout.write(self.style.SUCCESS('\nForced migration completed!'))
