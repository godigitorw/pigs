#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Setup user system
python manage.py update_roles

# Collect static files
python manage.py collectstatic --noinput --clear