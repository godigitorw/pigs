#!/bin/bash
# Test migrations locally with the Render database

echo "Testing migrations against Render database..."
echo ""

# Set the database URL
export DATABASE_URL="postgresql://pigfarm:fPEZ6b3fAxHaBklTtwOO9xGIesmO748a@dpg-d5bubjali9vc73c0gst0-a.oregon-postgres.render.com/pigfarm_wsx3"

# Clean the database first
echo "Step 1: Cleaning database..."
python3 cleanup_db.py

if [ $? -ne 0 ]; then
    echo "❌ Cleanup failed"
    exit 1
fi

echo ""
echo "Step 2: Running migrations..."
cd pigfarm
python3 manage.py migrate --no-input

if [ $? -ne 0 ]; then
    echo "❌ Migrations failed"
    exit 1
fi

echo ""
echo "✅ All migrations completed successfully!"
echo ""
echo "Step 3: Checking database tables..."
cd ..
python3 count_db_tables.py
