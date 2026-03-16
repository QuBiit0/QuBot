"""
Initialize database tables using SQLModel
"""

import asyncio
import logging

from app.database import engine
from app.models.database import SQLModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_tables():
    """Create all tables"""
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_tables())
