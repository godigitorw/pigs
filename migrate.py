#!/usr/bin/env python
"""
Custom migration script to handle PostgreSQL UUID conversion issues on Render
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigfarm.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pigfarm'))
django.setup()

from django.core.management import call_command
from django.db import connection

def run_migrations():
    """Run migrations with special handling for UUID conversion and missing tables"""
    try:
        print("Running migrations...")
        call_command('migrate', verbosity=2, interactive=False)
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        error_msg = str(e)

        # Handle case where migration tries to alter a table that doesn't exist
        if 'does not exist' in error_msg and 'farm_breedingrecord' in error_msg:
            print("⚠️ Table doesn't exist yet. This shouldn't happen on a fresh database.")
            print("⚠️ Attempting complete reset of farm migrations...")
            try:
                # Run all non-farm migrations first
                print("Running migrations for other apps...")
                call_command('migrate', 'contenttypes', verbosity=2, interactive=False)
                call_command('migrate', 'auth', verbosity=2, interactive=False)
                call_command('migrate', 'users', verbosity=2, interactive=False)
                call_command('migrate', 'admin', verbosity=2, interactive=False)
                call_command('migrate', 'sessions', verbosity=2, interactive=False)
                call_command('migrate', 'health', verbosity=2, interactive=False)

                # For farm app: Run 0001 to create tables, then fake UUID conversions
                print("Creating tables with farm 0001 migration...")
                call_command('migrate', 'farm', '0001', verbosity=2, interactive=False)

                print("Faking UUID conversion migrations (0003, 0006)...")
                call_command('migrate', 'farm', '0003', '--fake', verbosity=2, interactive=False)
                call_command('migrate', 'farm', '0006', '--fake', verbosity=2, interactive=False)

                # Now run remaining farm migrations normally
                print("Running remaining farm migrations...")
                call_command('migrate', 'farm', verbosity=2, interactive=False)

                print("✅ Migrations completed after fix!")
                return True
            except Exception as fix_error:
                print(f"❌ Migration fix failed: {fix_error}")
                import traceback
                traceback.print_exc()
                return False
        elif 'cannot cast type bigint to uuid' in error_msg:
            print("⚠️ UUID conversion error detected. Attempting to fix...")
            try:
                # Drop the problematic tables and recreate
                with connection.cursor() as cursor:
                    print("Dropping farm_breedingrecord table...")
                    cursor.execute("DROP TABLE IF EXISTS farm_breedingrecord CASCADE;")
                    print("Retrying migrations...")
                call_command('migrate', verbosity=2, interactive=False)
                print("✅ Migrations completed after fix!")
                return True
            except Exception as fix_error:
                print(f"❌ Migration fix failed: {fix_error}")
                return False
        else:
            print(f"❌ Migration failed: {e}")
            return False

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
