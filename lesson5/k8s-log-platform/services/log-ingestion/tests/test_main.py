import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "log-ingestion"}

def test_ingest_log_validation():
    invalid_log = {
        "level": "INVALID",
        "message": "test",
        "service": "test-service"
    }
    response = client.post("/api/v1/logs", json=invalid_log)
    assert response.status_code == 422
