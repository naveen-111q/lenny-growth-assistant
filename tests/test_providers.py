from unittest.mock import patch, MagicMock
from app.backend.services.provider_service import OllamaProvider, OpenRouterProvider, get_llm_provider


def test_ollama_provider_health_when_offline():
    provider = OllamaProvider(base_url="http://invalid-host:11434")
    health = provider.check_health()
    assert health.is_available is False
    assert "Cannot connect" in health.message or "error" in health.message.lower()


def test_openrouter_provider_health_when_key_missing():
    provider = OpenRouterProvider(api_key="")
    health = provider.check_health()
    assert health.is_available is False
    assert "OPENROUTER_API_KEY is not set" in health.message


@patch("httpx.Client.post")
def test_ollama_generate_mocked(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": {"content": "Grounded answer from Ollama."}}
    mock_post.return_value = mock_resp

    provider = OllamaProvider()
    res = provider.generate(prompt="What is PMF?", system_prompt="Grounding prompt")
    assert "Grounded answer" in res


def test_provider_factory_selection():
    p1 = get_llm_provider("ollama")
    assert isinstance(p1, OllamaProvider)

    p2 = get_llm_provider("openrouter")
    assert isinstance(p2, OpenRouterProvider)
