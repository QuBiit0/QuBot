"""
API Tests - Basic integration tests for endpoints

Run with: pytest tests/test_api.py -v
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

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://qubot:test@localhost:5432/qubot_test"

# Create test engine
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture
def client():
    """Create a test client"""
    def override_get_session():
        async def _get_session():
            async with TestingSessionLocal() as session:
                yield session
        return _get_session()
    
    # Override dependency
    app.dependency_overrides[get_session] = override_get_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


class TestSystemEndpoints:
    """Test system-related endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "online"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        # May return 503 if DB not available in test environment
        assert response.status_code in [200, 503]
    
    def test_info_endpoint(self, client):
        """Test system info endpoint"""
        response = client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "features" in data
    
    def test_config_endpoint(self, client):
        """Test public config endpoint"""
        response = client.get("/api/v1/config")
        assert response.status_code == 200
        data = response.json()
        assert "project_name" in data
        assert "features" in data


class TestAgentEndpoints:
    """Test agent-related endpoints"""
    
    def test_list_agents(self, client):
        """Test list agents endpoint"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
    
    def test_list_agent_classes(self, client):
        """Test list agent classes endpoint"""
        response = client.get("/api/v1/agent-classes")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestTaskEndpoints:
    """Test task-related endpoints"""
    
    def test_list_tasks(self, client):
        """Test list tasks endpoint"""
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
    
    def test_get_task_stats(self, client):
        """Test task stats endpoint"""
        response = client.get("/api/v1/tasks/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_get_kanban_board(self, client):
        """Test kanban board endpoint"""
        response = client.get("/api/v1/tasks/kanban/board")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestLLMConfigEndpoints:
    """Test LLM config endpoints"""
    
    def test_list_llm_configs(self, client):
        """Test list LLM configs endpoint"""
        response = client.get("/api/v1/llm-configs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_list_llm_providers(self, client):
        """Test list LLM providers endpoint"""
        response = client.get("/api/v1/llm-providers")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestToolEndpoints:
    """Test tool-related endpoints"""
    
    def test_list_available_tools(self, client):
        """Test list available tools endpoint"""
        response = client.get("/api/v1/tools/available")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_list_tool_types(self, client):
        """Test list tool types endpoint"""
        response = client.get("/api/v1/tool-types")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


# Run tests if called directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
