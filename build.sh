#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies for WeasyPrint (PDF generation)
echo "Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        libcairo2 \
        libpangoft2-1.0-0 || echo "Some system packages failed, continuing..."
else
    echo "apt-get not available, skipping system dependencies"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Navigate to Django project directory
cd pigfarm

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# Create default admin user if it doesn't exist
echo "Creating default admin user..."
python ../create_default_admin.py || echo "Admin user already exists or script failed"

echo "Build completed successfully!"
