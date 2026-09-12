from unittest.mock import patch
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)


@patch("app.backend.services.provider_service.OpenRouterProvider.generate")
@patch("app.backend.services.provider_service.OllamaProvider.generate")
def test_ship30_skill_generation(mock_ollama, mock_openrouter):
    mock_essay = (
        "# The Fatal Trap of Measuring Product-Market Fit\n\n"
        "Most founders think launching early and praying is how you build a startup. It's not.\n\n"
        "## Part 1: The Trap\n"
        "Pouring users into a leaky bucket is suicidal.\n\n"
        "## Part 2: The Core Framework\n"
        "Rahul Vohra used the 40% rule. If 40% of users aren't very disappointed, you don't have PMF.\n\n"
        "## Part 3: The Playbook\n"
        "- Segment your high-expectation customers.\n"
        "- Ignore the not disappointed crowd.\n"
        "- Double down on what superfans love.\n\n"
        "## Conclusion\n"
        "Track this every quarter to build an enduring growth engine."
    )
    mock_ollama.return_value = mock_essay
    mock_openrouter.return_value = mock_essay

    # Create session
    sid = client.post("/sessions", json={"title": "Ship 30 Test"}).json()["id"]

    resp = client.post("/generate/ship30", json={
        "session_id": sid,
        "topic": "Superhuman PMF Engine"
    })

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sid
    assert data["title"] == "The Fatal Trap of Measuring Product-Market Fit"
    assert data["word_count"] > 50
    assert len(data["sources"]) > 0
