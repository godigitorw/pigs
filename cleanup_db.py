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

    # Delete farm migration history
    print("\nDeleting farm migrations from history...")
    cursor.execute("DELETE FROM django_migrations WHERE app = 'farm';")
    print("✅ Farm migration history cleared")

    # Verify
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = 'farm';")
    count = cursor.fetchone()[0]
    print(f"✅ Confirmed: {count} farm migrations remaining (should be 0)")

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
