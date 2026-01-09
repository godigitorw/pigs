#!/usr/bin/env python
"""
Pre-Django database fix script
This runs BEFORE Django setup to fix corrupt migration state
"""
import os
import sys

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set")
    sys.exit(1)

print("="*60)
print("PRE-DJANGO DATABASE FIX")
print("="*60)

try:
    import psycopg2
    from urllib.parse import urlparse

    # Parse database URL
    result = urlparse(DATABASE_URL)

    print(f"\nConnecting to database: {result.path[1:]}")

    # Connect to database
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
    )

    conn.autocommit = True
    cursor = conn.cursor()

    # Check for corrupt state
    print("\n1. Checking for django_migrations table...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'django_migrations'
        );
    """)

    if cursor.fetchone()[0]:
        print("   ✓ django_migrations table exists")

    apps_to_check = ['farm', 'health', 'users']

    for app in apps_to_check:
        print(f"\nChecking {app} app state...")
        
        # Check migration history
        cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = %s;", (app,))
        mig_count = cursor.fetchone()[0]
        print(f"   Found {mig_count} {app} migrations in history")

        # Check tables
        cursor.execute("""
            SELECT COUNT(*) FROM pg_tables
            WHERE tablename LIKE %s AND schemaname = 'public';
        """, (f'{app}_%',))
        table_count = cursor.fetchone()[0]
        print(f"   Found {table_count} {app} tables in database")

        # Fix corrupt state
        if mig_count > 0 and table_count == 0:
            print(f"\n⚠️  CORRUPT STATE DETECTED FOR {app}!")
            print(f"   Clearing {app} migration history...")
            cursor.execute("DELETE FROM django_migrations WHERE app = %s;", (app,))
            print(f"   ✅ {app} migration history cleared")
        elif mig_count > 0 and table_count > 0:
            # Basic sanity check passed
            print(f"   ✅ {app} State looks good")
        elif mig_count == 0 and table_count == 0:
            print(f"   ℹ️  {app} appears clean (no migrations, no tables)")
        elif mig_count == 0 and table_count > 0:
             print(f"   ⚠️  Tables exist but no migrations for {app}. This might be okay if using legacy DB.")
        # Reset specific app if needed (logic can be expanded)
        pass
    else:
        print("   Fresh database - no migration table yet")

    cursor.close()
    conn.close()

    print("\n" + "="*60)
    print("✅ Database fix completed")
    print("="*60 + "\n")

except ImportError:
    print("\n⚠️  psycopg2 not available - skipping pre-fix")
    print("   (Will rely on migrate.py fallback logic)\n")
except Exception as e:
    print(f"\n⚠️  Database fix failed: {e}")
    print("   (Will rely on migrate.py fallback logic)\n")
    import traceback
    traceback.print_exc()
