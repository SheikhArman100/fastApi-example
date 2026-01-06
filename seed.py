#!/usr/bin/env python3
"""
FastAPI Database Seeder

This script seeds the database with initial data including admin users.
It will only add users that don't already exist.

Usage:
    python seed.py              # Seed admin users (safe, no overwriting)
"""

import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Import models to ensure they're registered before using
from app.models.user import User, Role
from app.models.file import File
from app.utils.seeder import seed_admin_users

if __name__ == "__main__":
    print("🌱 FastAPI Database Seeder")
    print("=" * 50)
    print("Note: This will only add new users, never delete existing ones.")
    print("=" * 50)

    seed_admin_users()

    print("\n" + "=" * 50)
    print("Seeder completed!")
