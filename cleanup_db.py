#!/usr/bin/env python
"""
Clean up corrupt farm migration state
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

    conn.autocommit = True
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("CLEANING UP CORRUPT MIGRATION STATE")
    print("="*60)

    # Drop all farm tables
    print("\n1. Dropping all farm tables...")
    cursor.execute("""
        SELECT tablename FROM pg_tables
        WHERE tablename LIKE 'farm_%' AND schemaname = 'public';
    """)
    farm_tables = cursor.fetchall()
    if farm_tables:
        for table in farm_tables:
            print(f"   Dropping {table[0]}...")
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]} CASCADE;")
        print(f"✅ Dropped {len(farm_tables)} farm tables")
    else:
        print("   No farm tables to drop")

    # Drop all health tables
    print("\n2. Dropping all health tables...")
    cursor.execute("""
        SELECT tablename FROM pg_tables
        WHERE tablename LIKE 'health_%' AND schemaname = 'public';
    """)
    health_tables = cursor.fetchall()
    if health_tables:
        for table in health_tables:
            print(f"   Dropping {table[0]}...")
            cursor.execute(f"DROP TABLE IF EXISTS {table[0]} CASCADE;")
        print(f"✅ Dropped {len(health_tables)} health tables")
    else:
        print("   No health tables to drop")

    # Delete farm migration history
    print("\n3. Deleting farm migrations from history...")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'farm';")
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'farm';")
    count = cursor.fetchone()[0]
    print(f"✅ Farm migration history cleared ({count} remaining)")

    # Delete health migration history
    print("\n4. Deleting health migrations from history...")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'health';")
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'health';")
    count = cursor.fetchone()[0]
    print(f"✅ Health migration history cleared ({count} remaining)")

    cursor.close()
    conn.close()

    print("\n" + "="*60)
    print("✅ CLEANUP COMPLETE - Database ready for fresh migrations")
    print("="*60 + "\n")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
