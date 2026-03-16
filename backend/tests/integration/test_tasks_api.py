"""
Integration tests for the Tasks API
"""

import pytest
from fastapi.testclient import TestClient


class TestTasksListEndpoint:
    def test_list_tasks_returns_paginated_response(self, client):
        resp = client.get("/api/v1/tasks")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert "total" in body["meta"]

    def test_kanban_board_returns_columns(self, client):
        resp = client.get("/api/v1/tasks/kanban/board")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        # Board data should have kanban columns
        data = body["data"]
        assert isinstance(data, dict)

    def test_task_stats_overview(self, client):
        resp = client.get("/api/v1/tasks/stats/overview")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body

    def test_filter_tasks_by_status(self, client):
        resp = client.get("/api/v1/tasks?status=BACKLOG")
        assert resp.status_code == 200

    def test_pagination_limit(self, client):
        resp = client.get("/api/v1/tasks?limit=3")
        body = resp.json()
        assert len(body["data"]) <= 3


class TestTaskCRUDRequiresAuth:
    def test_create_task_without_auth_returns_401_or_403(self, client):
        resp = client.post("/api/v1/tasks", json={"title": "Unauth task"})
        assert resp.status_code in (401, 403)

    def test_update_task_without_auth_returns_401_or_403(self, client):
        resp = client.patch(
            "/api/v1/tasks/00000000-0000-0000-0000-000000000000",
            json={"title": "x"},
        )
        assert resp.status_code in (401, 403)

    def test_delete_task_without_auth_returns_401_or_403(self, client):
        resp = client.delete("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code in (401, 403)

    def test_get_nonexistent_task_returns_404(self, client):
        resp = client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
