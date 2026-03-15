"""
Authentication Tests

Run with: pytest tests/test_auth.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.config import settings
from app.database import get_session
from app.core.security import get_password_hash
from app.models.user import User, UserRole

# Test database
TEST_DATABASE_URL = "postgresql+asyncpg://qubot:test@localhost:5432/qubot_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture
def client():
    """Create test client"""
    def override_get_session():
        async def _get_session():
            async with TestingSessionLocal() as session:
                yield session
        return _get_session()
    
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(client):
    """Create a test user"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User",
    }
    
    # Register user
    response = client.post("/api/v1/auth/register", json=user_data)
    return user_data


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_user(self, client):
        """Test user registration"""
        response = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "password123",
            "full_name": "New User",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new@example.com"
        assert data["username"] == "newuser"
        assert "hashed_password" not in data
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        # First registration
        client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "username": "user1",
            "password": "password123",
        })
        
        # Second registration with same email
        response = client.post("/api/v1/auth/register", json={
            "email": "dup@example.com",
            "username": "user2",
            "password": "password123",
        })
        
        assert response.status_code == 400
        assert "email already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"],
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": "wrongpassword",
        })
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, test_user):
        """Test getting current user info"""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"],
        })
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403


class TestSecurityUtils:
    """Test security utilities"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        from app.core.security import get_password_hash, verify_password
        
        password = "testpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_token_creation(self):
        """Test JWT token creation"""
        from app.core.security import create_access_token, decode_token
        
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        role = "user"
        
        token, jti = create_access_token(user_id, role)
        
        assert token is not None
        assert jti is not None
        
        # Decode and verify
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
