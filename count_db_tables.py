#!/usr/bin/env python
"""
Simple script to just COUNT what's in the database
No fixes, no Django, just raw numbers
"""
import os
import sys

DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

try:
    import psycopg2
    from urllib.parse import urlparse

    result = urlparse(DATABASE_URL)

    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port or 5432
    )

    cursor = conn.cursor()

    print("\n" + "="*60)
    print("DATABASE TABLE COUNT")
    print("="*60)

    # Total tables
    cursor.execute("""
        SELECT COUNT(*) FROM pg_tables
        WHERE schemaname = 'public';
    """)
    total = cursor.fetchone()[0]
    print(f"\nTotal tables in database: {total}")

    # Farm tables
    cursor.execute("""
        SELECT COUNT(*) FROM pg_tables
        WHERE tablename LIKE 'farm_%' AND schemaname = 'public';
    """)
    farm = cursor.fetchone()[0]
    print(f"Farm tables: {farm}")

    # Django migrations table
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'django_migrations'
        );
    """)
    has_migrations = cursor.fetchone()[0]
    print(f"Has django_migrations table: {has_migrations}")

    if has_migrations:
        cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'farm';")
        farm_migrations = cursor.fetchone()[0]
        print(f"Farm migrations in history: {farm_migrations}")

    # List all tables
    print("\nAll tables:")
    cursor.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    for row in cursor.fetchall():
        print(f"  - {row[0]}")

    cursor.close()
    conn.close()

    print("="*60 + "\n")

except ImportError:
    print("ERROR: psycopg2 not installed")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
