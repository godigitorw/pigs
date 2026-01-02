#!/usr/bin/env python
"""
Django management script to check database state
Run with: python manage.py shell < check_database.py
"""
from django.db import connection

print("\n" + "="*60)
print("DATABASE INSPECTION REPORT")
print("="*60)

with connection.cursor() as cursor:
    # Check if django_migrations table exists
    print("\n1. Checking if django_migrations table exists...")
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'django_migrations'
        );
    """)
    migrations_exists = cursor.fetchone()[0]
    print(f"   django_migrations table exists: {migrations_exists}")

    if migrations_exists:
        # Get migration count by app
        print("\n2. Migration history by app:")
        cursor.execute("""
            SELECT app, COUNT(*) as count
            FROM django_migrations
            GROUP BY app
            ORDER BY app;
        """)
        for row in cursor.fetchall():
            print(f"   - {row[0]}: {row[1]} migrations")

        # Get farm migrations specifically
        print("\n3. Farm app migrations in history:")
        cursor.execute("""
            SELECT id, name, applied
            FROM django_migrations
            WHERE app = 'farm'
            ORDER BY applied;
        """)
        farm_migrations = cursor.fetchall()
        if farm_migrations:
            for row in farm_migrations:
                print(f"   - {row[1]} (applied: {row[2]})")
        else:
            print("   No farm migrations found in history")

    # List all tables in the database
    print("\n4. All tables in database:")
    cursor.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    """)
    tables = cursor.fetchall()
    if tables:
        for table in tables:
            print(f"   - {table[0]}")
    else:
        print("   No tables found!")

    # Check for farm tables specifically
    print("\n5. Farm app tables:")
    cursor.execute("""
        SELECT tablename
        FROM pg_tables
        WHERE tablename LIKE 'farm_%' AND schemaname = 'public'
        ORDER BY tablename;
    """)
    farm_tables = cursor.fetchall()
    if farm_tables:
        for table in farm_tables:
            print(f"   - {table[0]}")
    else:
        print("   ⚠️  No farm tables found!")

    # Check table row counts
    if tables:
        print("\n6. Row counts for existing tables:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
                count = cursor.fetchone()[0]
                print(f"   - {table[0]}: {count} rows")
            except Exception as e:
                print(f"   - {table[0]}: Error - {str(e)[:50]}")

print("\n" + "="*60)
print("DIAGNOSIS:")
print("="*60)

if migrations_exists and farm_migrations and not farm_tables:
    print("❌ CORRUPT STATE DETECTED!")
    print("   - Farm migrations are recorded in history")
    print("   - But farm tables don't exist in database")
    print("   - This will cause migration failures")
    print("\n   SOLUTION: Need to clear farm migration history")
elif not migrations_exists:
    print("✅ Fresh database - no migration history")
    print("   - Ready for initial migrations")
elif not farm_migrations and not farm_tables:
    print("✅ Clean state for farm app")
    print("   - No migration history, no tables")
else:
    print("✅ Database appears to be in good state")

print("="*60 + "\n")
