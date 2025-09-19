"""
Vercel app entry point
"""
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigfarm.settings')

# Import and configure Django
import django
django.setup()

# Import the WSGI application
from django.core.handlers.wsgi import WSGIHandler
app = WSGIHandler()