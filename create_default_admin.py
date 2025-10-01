#!/usr/bin/env python
"""
Script to create a default superuser in Railway deployment
Run with: railway run python create_default_admin.py
"""
import os
import sys
import django

# Add pigfarm to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pigfarm'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigfarm.settings')

django.setup()

from users.models import CustomUser

# Default credentials - CHANGE THESE!
USERNAME = 'admin'
EMAIL = 'admin@pigfarm.com'
PASSWORD = 'admin123'  # CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN!

if CustomUser.objects.filter(username=USERNAME).exists():
    print(f"User '{USERNAME}' already exists!")
else:
    CustomUser.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD,
        role='admin'
    )
    print(f"✅ Superuser created successfully!")
    print(f"Username: {USERNAME}")
    print(f"Password: {PASSWORD}")
    print(f"⚠️  IMPORTANT: Change this password immediately after first login!")
