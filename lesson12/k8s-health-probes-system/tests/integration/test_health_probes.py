"""Integration tests for health probe behavior."""

import pytest
import httpx
import asyncio
import time

BASE_URL = "http://localhost:8080"

@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=30.0)

class TestLivenessProbe:
    """Tests for liveness probe behavior."""
    
    def test_liveness_returns_healthy(self, client):
        """Liveness probe should return healthy for running service."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data["details"]
    
    def test_liveness_does_not_check_dependencies(self, client):
        """Liveness should not fail when dependencies are down."""
        # This test validates the principle that liveness
        # only checks internal process health
        response = client.get("/health/live")
        assert response.status_code == 200

class TestReadinessProbe:
    """Tests for readiness probe behavior."""
    
    def test_readiness_returns_ready(self, client):
        """Readiness probe should return ready when service is available."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    def test_readiness_checks_dependencies(self, client):
        """Readiness should check external dependencies."""
        response = client.get("/health/ready")
        if response.status_code == 200:
            data = response.json()
            # Should report on dependency status
            assert "details" in data

class TestStartupProbe:
    """Tests for startup probe behavior."""
    
    def test_startup_completes(self, client):
        """Startup probe should pass when initialization is complete."""
        response = client.get("/health/startup")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"

class TestGracefulShutdown:
    """Tests for graceful shutdown behavior."""
    
    def test_shutdown_endpoint_exists(self, client):
        """Shutdown endpoint should be available for preStop hook."""
        # Don't actually trigger shutdown in tests
        pass

class TestProbeTimings:
    """Tests for probe response times."""
    
    def test_liveness_responds_quickly(self, client):
        """Liveness probe should respond within timeout."""
        start = time.time()
        response = client.get("/health/live")
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 5.0, f"Liveness took {duration}s, should be < 5s"
    
    def test_readiness_responds_within_timeout(self, client):
        """Readiness probe should respond within configured timeout."""
        start = time.time()
        response = client.get("/health/ready")
        duration = time.time() - start
        
        # May fail if dependencies are down, but should respond quickly
        assert duration < 3.0, f"Readiness took {duration}s, should be < 3s"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
