import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select


async def seed_admin():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == "admin@qubot.ai")
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Admin user already exists: {existing_user.email}")
            return

        print("Creating default admin user...")
        admin = User(
            email="admin@qubot.ai",
            username="admin",
            hashed_password=get_password_hash("admin"),
            full_name="Qubot Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )

        session.add(admin)
        await session.commit()
        print("Default admin user created successfully!")
        print("Email: admin@qubot.ai")
        print("Password: admin")


if __name__ == "__main__":
    asyncio.run(seed_admin())
