#!/usr/bin/env python3
"""
Simple database check without Django - just to test connectivity
"""

# Try to use the built-in sqlite3 module's dbapi2 concept
print("Attempting to connect to Render PostgreSQL database...")
print("Note: This requires psycopg2 to be installed\n")

DATABASE_URL = "postgresql://pigfarm:fPEZ6b3fAxHaBklTtwOO9xGIesmO748a@dpg-d5bubjali9vc73c0gst0-a.oregon-postgres.render.com/pigfarm_wsx3"

print(f"Database URL (masked): postgresql://pigfarm:***@dpg-d5bubjali9vc73c0gst0-a.oregon-postgres.render.com/pigfarm_wsx3")
print("\nTo check the database, you have two options:")
print("\n1. Install psycopg2 locally:")
print("   pip3 install --user psycopg2-binary")
print("   python3 check_db.py")
print("\n2. Or, let's create a SQL file and execute it on Render's database using psql:")
print("   We can generate SQL queries to check the database state")

print("\n" + "="*60)
print("GENERATING SQL QUERIES TO CHECK DATABASE STATE")
print("="*60)

sql_queries = """
-- Check if django_migrations table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'django_migrations'
);

-- Get migration count by app
SELECT app, COUNT(*) as count
FROM django_migrations
GROUP BY app
ORDER BY app;

-- Get farm migrations
SELECT id, name, applied
FROM django_migrations
WHERE app = 'farm'
ORDER BY applied;

-- List all tables
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check for farm tables
SELECT tablename
FROM pg_tables
WHERE tablename LIKE 'farm_%' AND schemaname = 'public'
ORDER BY tablename;
"""

print("\nSQL queries to run:")
print(sql_queries)

print("\n" + "="*60)
print("RECOMMENDED ACTION")
print("="*60)
print("\nSince we can't connect locally easily, let's just fix the database")
print("directly on Render by improving our migration script.")
print("\nThe issue is clear from the error:")
print("- Migration tries to use farm_breedingrecord table")
print("- Table doesn't exist")
print("- This means corrupt migration state")
print("\nOur migrate.py script should handle this, but it seems the")
print("detection isn't catching it properly. Let me fix the script...")
