#!/usr/bin/env python3
"""
Quick test script to verify authentication endpoints work
"""
import asyncio
import sys
sys.path.insert(0, '/home/peter/work/tripflow/backend')

from sqlalchemy import select
from app.db.database import async_session
from app.models.user import User
from app.core.security import verify_password

async def test_auth():
    print("Testing authentication...")

    async with async_session() as db:
        # Find admin user
        result = await db.execute(select(User).where(User.email == 'admin@tripflow.com'))
        user = result.scalar_one_or_none()

        if not user:
            print("❌ Admin user not found!")
            return False

        print(f"✅ Found user: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Admin: {user.is_admin}")
        print(f"   Active: {user.is_active}")

        # Test password
        if verify_password('admin123', user.password_hash):
            print("✅ Password verification successful!")
            return True
        else:
            print("❌ Password verification failed!")
            return False

if __name__ == "__main__":
    result = asyncio.run(test_auth())
    sys.exit(0 if result else 1)
