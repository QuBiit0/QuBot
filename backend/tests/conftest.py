"""
Pytest configuration and shared fixtures.
Imports are lazy (inside fixtures) so unit tests don't require
a full running stack.
"""

import os
import sys

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Test database ───────────────────────────────────────────────────────────
# Use env var so CI can override; falls back to a local test DB.
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://qubot:test@localhost:5432/qubot_test",
)


# ─── Session-scoped DB setup (only used by integration tests) ────────────────

@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables once per test session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_database):
    """Provide a transactional DB session that rolls back after each test."""
    engine = setup_database
    TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client(db_session):
    """
    FastAPI TestClient with DB dependency overridden.
    Lazy import so unit tests don't pay the full app startup cost.
    """
    from fastapi.testclient import TestClient

    # Lazy import app here — unit tests skip this fixture entirely
    from app.database import get_session
    from app.main import app

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ─── Common test data ────────────────────────────────────────────────────────

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest.fixture
def auth_headers(client, test_user_data):
    """Register + login, return Authorization headers."""
    client.post("/api/v1/auth/register", json=test_user_data)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Pytest markers ───────────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
