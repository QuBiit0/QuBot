import asyncio
import sys
import os

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_session, engine
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select

async def seed_admin():
    async with engine.begin() as conn:
        # Ensure tables exist (optional if already created by docker)
        pass

    async for session in get_session():
        # Check if admin already exists
        result = await session.execute(select(User).where(User.email == "admin@qubot.ai"))
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
            is_active=True
        )
        
        session.add(admin)
        await session.commit()
        print("Default admin user created successfully!")
        print("Email: admin@qubot.ai")
        print("Password: admin")
        break

if __name__ == "__main__":
    asyncio.run(seed_admin())
