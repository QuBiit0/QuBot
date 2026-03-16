"""
Integration tests for the Agents API
Requires a running PostgreSQL test database.
"""

import pytest
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────

def register_and_login(client: TestClient) -> dict:
    """Create a user and return auth headers."""
    import random
    suffix = random.randint(10000, 99999)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": f"agenttest{suffix}@example.com",
            "username": f"agentuser{suffix}",
            "password": "testpass123",
        },
    )
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": f"agenttest{suffix}@example.com", "password": "testpass123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────

class TestAgentsListEndpoint:
    def test_list_agents_returns_paginated_response(self, client):
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "meta" in body
        meta = body["meta"]
        assert "page" in meta
        assert "limit" in meta
        assert "total" in meta

    def test_list_agents_default_page_is_one(self, client):
        body = client.get("/api/v1/agents").json()
        assert body["meta"]["page"] == 1

    def test_list_agents_limit_respected(self, client):
        body = client.get("/api/v1/agents?limit=5").json()
        assert len(body["data"]) <= 5

    def test_filter_by_status(self, client):
        resp = client.get("/api/v1/agents?status=IDLE")
        assert resp.status_code == 200


class TestAgentClasses:
    def test_list_agent_classes(self, client):
        resp = client.get("/api/v1/agent-classes")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], list)


class TestAgentCRUDRequiresAuth:
    """Mutating endpoints require authentication"""

    def test_create_agent_without_auth_returns_401_or_403(self, client):
        resp = client.post("/api/v1/agents", json={"name": "Unauth"})
        assert resp.status_code in (401, 403)

    def test_update_agent_without_auth_returns_401_or_403(self, client):
        resp = client.patch("/api/v1/agents/00000000-0000-0000-0000-000000000000", json={})
        assert resp.status_code in (401, 403)

    def test_delete_agent_without_auth_returns_401_or_403(self, client):
        resp = client.delete("/api/v1/agents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code in (401, 403)

    def test_get_nonexistent_agent_returns_404(self, client):
        resp = client.get("/api/v1/agents/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
