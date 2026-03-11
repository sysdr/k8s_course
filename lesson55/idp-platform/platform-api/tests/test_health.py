"""Basic health and metrics tests (no cluster required)."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pytest
from fastapi.testclient import TestClient
os.environ.setdefault("ENVIRONMENT", "development")
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"

def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "platform_api_requests_total" in r.text or "platform_" in r.text
