"""
Integration tests for the Log Ingestor service.
Run with:  pytest tests/ -v
Requires the ingestor reachable at INGESTOR_URL (default localhost:8000).
"""
import os
import httpx
import pytest

BASE = os.getenv("INGESTOR_URL", "http://localhost:8000")


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE, timeout=5.0)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_ingest_valid_event(client):
    payload = {
        "severity": "INFO",
        "service": "test-svc",
        "message": "integration test event",
        "metadata": {"env": "test"},
    }
    r = client.post("/ingest", json=payload)
    assert r.status_code == 202
    body = r.json()
    assert body["accepted"] is True
    assert len(body["trace_id"]) > 0


def test_ingest_missing_service(client):
    """Pydantic should reject a payload without 'service'."""
    r = client.post("/ingest", json={"severity": "INFO", "message": "no service field"})
    assert r.status_code == 422


def test_ingest_invalid_severity(client):
    r = client.post("/ingest", json={"severity": "INVALID", "service": "s", "message": "m"})
    assert r.status_code == 422


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "log_ingestor_events_received_total" in r.text
