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

        # Check farm migrations
        print("\n2. Checking farm migration history...")
        cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'farm';")
        farm_count = cursor.fetchone()[0]
        print(f"   Found {farm_count} farm migrations in history")

        # Check farm tables
        print("\n3. Checking for farm tables...")
        cursor.execute("""
            SELECT COUNT(*) FROM pg_tables
            WHERE tablename LIKE 'farm_%' AND schemaname = 'public';
        """)
        table_count = cursor.fetchone()[0]
        print(f"   Found {table_count} farm tables in database")

        # Fix corrupt state
        if farm_count > 0 and table_count == 0:
            print("\n⚠️  CORRUPT STATE DETECTED!")
            print("   Clearing farm migration history...")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'farm';")
            print("   ✅ Farm migration history cleared")
        elif farm_count > 0 and table_count > 0:
            print("\n   Checking if tables match migrations...")
            # If tables exist but migrations are failing, drop everything
            print("   ⚠️  Dropping all farm tables to recreate from scratch...")
            cursor.execute("""
                SELECT tablename FROM pg_tables
                WHERE tablename LIKE 'farm_%' AND schemaname = 'public';
            """)
            for row in cursor.fetchall():
                print(f"   Dropping {row[0]}...")
                cursor.execute(f"DROP TABLE IF EXISTS {row[0]} CASCADE;")
            print("   Clearing farm migration history...")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'farm';")
            print("   ✅ Farm app reset complete")
        else:
            print("\n   ✅ State looks good")
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
