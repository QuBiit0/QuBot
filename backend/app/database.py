"""
Qubot Database Configuration
Uses SQLModel with async SQLAlchemy
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlmodel import SQLModel

# Export declarative_base for models that use pure SQLAlchemy
Base = declarative_base()
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Detect stale connections
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """Dependency for getting async DB sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all tables. Only for testing - production uses Alembic"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database tables created")


async def drop_tables():
    """Drop all tables. Use with caution!"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    logger.info("Database tables dropped")


# For backwards compatibility with existing code
def init_db():
    """Synchronous init for backwards compatibility"""
    import asyncio

    try:
        asyncio.run(create_tables())
    except Exception as e:
        logger.error(f"Failed to init database: {e}")


# Sync engine for Alembic (run in sync context)
from sqlalchemy import create_engine


def get_sync_database_url() -> str:
    """Get sync database URL by removing asyncpg driver"""
    url = settings.DATABASE_URL
    # Handle both +asyncpg and postgresql+asyncpg formats
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "")
    elif url.startswith("postgresql://"):
        return url
    elif url.startswith("postgresql+"):
        # Remove any other driver
        return url.replace(url.split("://")[0], "postgresql")
    return url


sync_engine = create_engine(
    get_sync_database_url(),
    echo=settings.DEBUG,
)
