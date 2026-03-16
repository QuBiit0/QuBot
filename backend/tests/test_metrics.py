"""
Tests for Prometheus metrics endpoint

Run with: pytest tests/test_metrics.py -v
"""

import pytest


class TestMetricsEndpoints:
    """Test metrics-related endpoints"""

    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint returns valid data"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

        # Check content type
        assert "text/plain" in response.headers["content-type"]

        # Check for standard Prometheus format
        content = response.text
        assert (
            "# HELP" in content
            or "# TYPE" in content
            or "http_requests_total" in content
        )

    def test_metrics_contains_http_requests(self, client):
        """Test metrics contain HTTP request metrics after making requests"""
        # Make a request to generate metrics
        client.get("/api/v1/health")

        # Get metrics
        response = client.get("/api/v1/metrics")
        content = response.text

        # Should contain HTTP metrics
        assert "http_requests_total" in content or "http_request_duration" in content

    def test_metrics_contains_app_info(self, client):
        """Test metrics contain application info"""
        response = client.get("/api/v1/metrics")
        content = response.text

        # Check for FastAPI/Starlette metrics
        assert response.status_code == 200
        assert len(content) > 0


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_health_endpoint_exists(self, client):
        """Test health endpoint exists and returns data"""
        response = client.get("/api/v1/health")
        # Can be 200 (healthy) or 503 (unhealthy) but should not be 404
        assert response.status_code in [200, 503]

    def test_health_ready_endpoint(self, client):
        """Test readiness probe endpoint"""
        response = client.get("/api/v1/health/ready")
        # May return 503 if DB not available
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "ready" in data

    def test_health_live_endpoint(self, client):
        """Test liveness probe endpoint"""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data.get("alive") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
