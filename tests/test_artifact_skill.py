from unittest.mock import patch
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)


@patch("app.backend.services.provider_service.OpenRouterProvider.generate")
@patch("app.backend.services.provider_service.OllamaProvider.generate")
def test_markdown_artifact_generation(mock_ollama, mock_openrouter):
    mock_val = "```markdown\n# Growth Strategy PRD\n\n## 1. Objective\nDouble activation.\n```"
    mock_ollama.return_value = mock_val
    mock_openrouter.return_value = mock_val

    sid = client.post("/sessions", json={"title": "Artifact Test"}).json()["id"]
    resp = client.post("/generate/artifact", json={
        "session_id": sid,
        "artifact_type": "markdown",
        "prompt": "Create a growth strategy PRD"
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["artifact_type"] == "markdown"
    assert "Growth Strategy PRD" in data["content"]


@patch("app.backend.services.provider_service.OpenRouterProvider.generate")
@patch("app.backend.services.provider_service.OllamaProvider.generate")
def test_html_artifact_generation(mock_ollama, mock_openrouter):
    mock_val = "```html\n<div class='landing'><h1>Elena Verna PLG Dashboard</h1></div>\n```"
    mock_ollama.return_value = mock_val
    mock_openrouter.return_value = mock_val

    sid = client.post("/sessions", json={"title": "Artifact Test HTML"}).json()["id"]
    resp = client.post("/generate/artifact", json={
        "session_id": sid,
        "artifact_type": "html",
        "prompt": "Build a PLG dashboard"
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["artifact_type"] == "html"
    assert "<html" in data["content"].lower()
    assert "Elena Verna PLG Dashboard" in data["content"]
