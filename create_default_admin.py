#!/usr/bin/env python
"""
Script to create a default superuser with farm_owner role
Run with: python create_default_admin.py
"""
import os
import sys
import django

# Add pigfarm to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pigfarm'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigfarm.settings')

django.setup()

from users.models import CustomUser, UserRole

# Default credentials - CHANGE THESE!
USERNAME = 'admin'
EMAIL = 'admin@pigfarm.com'
PASSWORD = 'admin123'  # CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN!

try:
    # Get or create farm_owner role
    farm_owner_role, created = UserRole.objects.get_or_create(
        name='farm_owner',
        defaults={
            'display_name': 'Farm Owner/Admin',
            'description': 'Full access to all system features',
            'is_active': True
        }
    )
    if created:
        print(f"✅ Created farm_owner role")
    
    if CustomUser.objects.filter(username=USERNAME).exists():
        print(f"User '{USERNAME}' already exists!")
        # Get the user and update credentials and role
        user = CustomUser.objects.get(username=USERNAME)
        user.set_password(PASSWORD)
        user.is_superuser = True
        user.is_staff = True
        user.role = farm_owner_role  # Assign farm_owner role
        user.save()
        print(f"✅ Password reset and role assigned for user '{USERNAME}'")
        print(f"Username: {USERNAME}")
        print(f"Password: {PASSWORD}")
        print(f"Role: {user.role.display_name}")
    else:
        user = CustomUser.objects.create_superuser(
            username=USERNAME,
            email=EMAIL,
            password=PASSWORD
        )
        # Assign farm_owner role
        user.role = farm_owner_role
        user.save()
        print(f"✅ Superuser created successfully!")
        print(f"Username: {USERNAME}")
        print(f"Password: {PASSWORD}")
        print(f"Role: {user.role.display_name}")
        print(f"⚠️  IMPORTANT: Change this password immediately after first login!")
except Exception as e:
    print(f"❌ Error creating superuser: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
