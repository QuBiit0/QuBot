"""
Unit test configuration — sets required env vars before any app imports.
Unit tests run in isolation without a real database or Redis.
"""

import os

# Set required env vars BEFORE any app code is imported
os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-minimum-32-chars-padding")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEBUG", "true")
