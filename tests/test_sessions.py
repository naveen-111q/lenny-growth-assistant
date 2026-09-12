from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)


def test_session_creation_and_isolation():
    # 1. Create Session A
    resp_a = client.post("/sessions", json={"title": "Session A"})
    assert resp_a.status_code == 201
    sid_a = resp_a.json()["id"]

    # 2. Create Session B
    resp_b = client.post("/sessions", json={"title": "Session B"})
    assert resp_b.status_code == 201
    sid_b = resp_b.json()["id"]
    assert sid_a != sid_b

    # 3. List sessions
    list_resp = client.get("/sessions")
    assert list_resp.status_code == 200
    ids = [s["id"] for s in list_resp.json()]
    assert sid_a in ids
    assert sid_b in ids

    # 4. Verify initial empty message history
    detail_a = client.get(f"/sessions/{sid_a}").json()
    assert len(detail_a["messages"]) == 0
