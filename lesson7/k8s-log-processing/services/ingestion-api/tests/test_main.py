"""Unit tests for ingestion API"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()

def test_liveness():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

def test_ingest_valid_log():
    log_data = {
        "level": "INFO",
        "service": "test-service",
        "message": "Test log message"
    }
    response = client.post("/api/v1/ingest", json=log_data)
    assert response.status_code in [202, 503]  # 503 if Redis not available

def test_ingest_invalid_level():
    log_data = {
        "level": "INVALID",
        "service": "test-service",
        "message": "Test message"
    }
    response = client.post("/api/v1/ingest", json=log_data)
    assert response.status_code == 422
