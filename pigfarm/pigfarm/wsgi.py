"""
WSGI config for pigfarm project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Add the project directory to the sys.path
ROOT = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(ROOT))

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigfarm.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# Vercel expects 'app' variable
app = application
