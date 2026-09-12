from unittest.mock import patch
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)


def test_chat_validation_error():
    # Invalid empty payload
    resp = client.post("/chat", json={})
    assert resp.status_code == 422


@patch("app.backend.services.provider_service.OpenRouterProvider.generate")
@patch("app.backend.services.provider_service.OllamaProvider.generate")
def test_chat_grounded_flow(mock_ollama, mock_openrouter):
    mock_ollama.return_value = "Superhuman measured PMF by asking users how disappointed they would be."
    mock_openrouter.return_value = "Superhuman measured PMF by asking users how disappointed they would be."

    # Create session
    sess_resp = client.post("/sessions", json={"title": "Test Chat"})
    sid = sess_resp.json()["id"]

    # Send chat query
    chat_resp = client.post("/chat", json={
        "session_id": sid,
        "message": "How does Rahul Vohra measure product-market fit?"
    })

    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["session_id"] == sid
    assert len(data["sources"]) > 0
    assert "Superhuman" in data["assistant_message"]

    # Verify session isolation and persistence
    sess_detail = client.get(f"/sessions/{sid}").json()
    assert len(sess_detail["messages"]) == 2  # user + assistant
    assert sess_detail["messages"][0]["role"] == "user"
    assert sess_detail["messages"][1]["role"] == "assistant"


def test_chat_greeting_flow():
    # Test conversational greeting "hii"
    sess_resp = client.post("/sessions", json={"title": "Greeting Chat"})
    sid = sess_resp.json()["id"]

    chat_resp = client.post("/chat", json={
        "session_id": sid,
        "message": "hii"
    })

    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["session_id"] == sid
    assert len(data["sources"]) == 0  # No random transcript chunks attached
    assert "Lenny Growth Assistant" in data["assistant_message"]
    assert "Rahul Vohra" in data["assistant_message"]

    # Verify session isolation
    sess_detail = client.get(f"/sessions/{sid}").json()
    assert len(sess_detail["messages"]) == 2

