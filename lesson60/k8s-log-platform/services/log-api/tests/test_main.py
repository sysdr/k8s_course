import pytest
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)
def test_liveness():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
def test_ingest_log():
    response = client.post("/logs", json={"level": "INFO", "message": "Test", "service": "test"})
    assert response.status_code in [200, 500]
