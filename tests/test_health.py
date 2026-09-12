from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "providers" in data
    assert "ollama" in data["providers"]
    assert "openrouter" in data["providers"]
    assert data["database"]["ingested_chunks"] > 0
