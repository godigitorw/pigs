#!/usr/bin/env bash
# Render build script

set -o errexit  # Exit on error

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running database migrations..."
python manage.py migrate

echo "Setting up user system and admin account..."
python manage.py setup_user_system

echo "Build completed successfully!"