#!/usr/bin/env python
"""
Script to create a superuser in Railway deployment
Run with: railway run python create_admin.py
"""
import os
import sys
import django

# Add pigfarm to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pigfarm'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigfarm.settings')

django.setup()

from users.models import CustomUser

# Create superuser
username = input("Enter username: ")
email = input("Enter email: ")
password = input("Enter password: ")

if CustomUser.objects.filter(username=username).exists():
    print(f"User '{username}' already exists!")
else:
    CustomUser.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role='admin'
    )
    print(f"Superuser '{username}' created successfully!")
