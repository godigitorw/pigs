#!/usr/bin/env python3
"""
Generate a new Django SECRET_KEY for production use.
Run: python generate_secret_key.py
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print(f"Generated SECRET_KEY for production:")
    print(secret_key)
    print(f"\nSet this in your Render environment variables:")
    print(f"SECRET_KEY={secret_key}")