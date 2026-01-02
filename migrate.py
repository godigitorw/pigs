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

    # First, check if we have corrupt migration state
    print("Checking database migration state...")
    try:
        with connection.cursor() as cursor:
            # Check if django_migrations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'django_migrations'
                );
            """)
            migrations_table_exists = cursor.fetchone()[0]

            if migrations_table_exists:
                # Check for farm migrations in history
                cursor.execute("""
                    SELECT COUNT(*) FROM django_migrations
                    WHERE app = 'farm';
                """)
                farm_migration_count = cursor.fetchone()[0]

                # Check if farm tables actually exist
                cursor.execute("""
                    SELECT COUNT(*) FROM pg_tables
                    WHERE tablename LIKE 'farm_%' AND schemaname = 'public';
                """)
                farm_table_count = cursor.fetchone()[0]

                print(f"Found {farm_migration_count} farm migrations in history")
                print(f"Found {farm_table_count} farm tables in database")

                # If we have migration history but no tables, we have corrupt state
                if farm_migration_count > 0 and farm_table_count == 0:
                    print("⚠️ Corrupt migration state detected: migrations recorded but tables missing")
                    print("Clearing farm migration history...")
                    cursor.execute("DELETE FROM django_migrations WHERE app = 'farm';")
                    print("✅ Farm migration history cleared")
    except Exception as check_error:
        print(f"⚠️ Could not check migration state: {check_error}")
        # Continue anyway

    try:
        print("\nRunning migrations...")
        call_command('migrate', verbosity=2, interactive=False)
        print("✅ Migrations completed successfully!")
        return True
    except Exception as e:
        error_msg = str(e)

        # Handle case where migration tries to alter a table that doesn't exist OR UUID conversion issues
        if ('does not exist' in error_msg and 'farm_breedingrecord' in error_msg) or 'cannot cast type bigint to uuid' in error_msg:
            print("⚠️ Migration error detected. Attempting strategic migration approach...")
            print(f"⚠️ Error: {error_msg}")
            try:
                # Drop all farm tables to start fresh
                print("\n=== Dropping all farm tables to start fresh ===")
                with connection.cursor() as cursor:
                    # Get all farm tables
                    cursor.execute("""
                        SELECT tablename FROM pg_tables
                        WHERE tablename LIKE 'farm_%' AND schemaname = 'public';
                    """)
                    tables = cursor.fetchall()

                    for table in tables:
                        table_name = table[0]
                        print(f"Dropping table: {table_name}")
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")

                print("✅ All farm tables dropped")

                # Run all non-farm migrations first
                print("\n=== Running migrations for other apps ===")
                call_command('migrate', 'contenttypes', verbosity=2, interactive=False)
                call_command('migrate', 'auth', verbosity=2, interactive=False)
                call_command('migrate', 'users', verbosity=2, interactive=False)
                call_command('migrate', 'admin', verbosity=2, interactive=False)
                call_command('migrate', 'sessions', verbosity=2, interactive=False)
                call_command('migrate', 'health', verbosity=2, interactive=False)

                # For farm app: Fake all migrations
                print("\n=== Faking all farm migrations ===")
                call_command('migrate', 'farm', '--fake', verbosity=2, interactive=False)

                # Now use migrate --run-syncdb to create tables from current models
                print("\n=== Creating tables from current models ===")
                call_command('migrate', '--run-syncdb', verbosity=2, interactive=False)

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
