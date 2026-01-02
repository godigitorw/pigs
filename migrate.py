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
            print("⚠️ Table doesn't exist yet. Faking initial migration...")
            try:
                # Fake the problematic migrations
                print("Faking farm migrations 0001, 0002, 0003...")
                call_command('migrate', 'farm', '0002', '--fake', verbosity=2)
                call_command('migrate', 'farm', '0003', '--fake', verbosity=2)
                print("Running remaining migrations...")
                call_command('migrate', verbosity=2, interactive=False)
                print("✅ Migrations completed after fix!")
                return True
            except Exception as fix_error:
                print(f"❌ Migration fix failed: {fix_error}")
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
