import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import httpx
from pydantic import BaseModel
from fastapi import HTTPException
from app.config import settings

logger = logging.getLogger("lenny_growth.providers")


class ProviderHealthStatus(BaseModel):
    is_available: bool
    provider_name: str
    model_name: str
    message: str
    available_models: List[str] = []
    latency_ms: Optional[float] = None


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM providers (Ollama, OpenRouter).
    """
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Executes a completion request given prompt, system instructions, and history.
        """
        pass

    @abstractmethod
    def check_health(self) -> ProviderHealthStatus:
        """
        Verifies connectivity and model availability for the provider.
        """
        pass


_health_cache: Dict[str, Any] = {}
HEALTH_CACHE_TTL_SECONDS = 15.0


class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama model provider.
    Communicates with Ollama daemon over HTTP REST.
    """
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model

    def check_health(self) -> ProviderHealthStatus:
        cache_key = f"ollama_{self.base_url}_{self.model}"
        now = time.time()
        if cache_key in _health_cache:
            cached_time, cached_val = _health_cache[cache_key]
            if now - cached_time < HEALTH_CACHE_TTL_SECONDS:
                return cached_val

        start_time = time.time()
        try:
            # Use fast connect timeout so offline daemon on Windows returns in < 0.5s
            timeout_config = httpx.Timeout(connect=0.5, read=1.0, write=1.0, pool=1.0)
            with httpx.Client(timeout=timeout_config) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Check if requested model or matching tag is available
                    model_match = any(self.model in m or m.startswith(self.model) for m in models)
                    if model_match:
                        status = ProviderHealthStatus(
                            is_available=True,
                            provider_name="ollama",
                            model_name=self.model,
                            message=f"Ollama is online and model '{self.model}' is ready.",
                            available_models=models,
                            latency_ms=latency
                        )
                    else:
                        status = ProviderHealthStatus(
                            is_available=False,
                            provider_name="ollama",
                            model_name=self.model,
                            message=f"Ollama is running, but model '{self.model}' is not installed. Run `ollama pull {self.model}`.",
                            available_models=models,
                            latency_ms=latency
                        )
                else:
                    status = ProviderHealthStatus(
                        is_available=False,
                        provider_name="ollama",
                        model_name=self.model,
                        message=f"Ollama responded with status code {resp.status_code}.",
                        latency_ms=latency
                    )
        except httpx.ConnectError:
            status = ProviderHealthStatus(
                is_available=False,
                provider_name="ollama",
                model_name=self.model,
                message=f"Cannot connect to Ollama at {self.base_url}. Ensure the service is running (`ollama serve`)."
            )
        except Exception as e:
            status = ProviderHealthStatus(
                is_available=False,
                provider_name="ollama",
                model_name=self.model,
                message=f"Ollama health check error: {str(e)}"
            )

        _health_cache[cache_key] = (now, status)
        return status

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for item in history:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": min(max_tokens or 150, 150),
                "num_ctx": 1024,
                "num_thread": 6
            }
        }

        try:
            logger.info(f"Dispatching generation to Ollama ({self.model}) at {self.base_url}")
            with httpx.Client(timeout=180.0) as client:
                resp = client.post(f"{self.base_url}/api/chat", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("message", {}).get("content", "")
                    return content.strip()
                elif resp.status_code == 404:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Model '{self.model}' not found in Ollama. Run: `ollama pull {self.model}`"
                    )
                else:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Ollama returned HTTP error {resp.status_code}: {resp.text}"
                    )
        except httpx.ConnectError:
            logger.error(f"Failed to connect to Ollama daemon at {self.base_url}")
            raise HTTPException(
                status_code=503,
                detail=f"Ollama service is not reachable at {self.base_url}. Please ensure Ollama is installed and running (`ollama serve`)."
            )
        except httpx.TimeoutException:
            logger.error("Ollama inference timed out after 180s")
            raise HTTPException(
                status_code=504,
                detail=f"Ollama inference timed out while running model '{self.model}'. Consider using OpenRouter or a lighter model."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error communicating with Ollama: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ollama inference error: {str(e)}")


class OpenRouterProvider(BaseLLMProvider):
    """
    Cloud OpenRouter provider.
    Provides unified access to commercial and open-source models via OpenRouter API.
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = settings.openrouter_api_key if api_key is None else api_key
        self.model = model or settings.openrouter_model
        self.base_url = settings.openrouter_base_url.rstrip("/")

    def check_health(self) -> ProviderHealthStatus:
        if not self.api_key or not self.api_key.strip():
            return ProviderHealthStatus(
                is_available=False,
                provider_name="openrouter",
                model_name=self.model,
                message="OPENROUTER_API_KEY is not set in environment or .env."
            )

        cache_key = f"openrouter_{self.api_key[:12]}_{self.model}"
        now = time.time()
        if cache_key in _health_cache:
            cached_time, cached_val = _health_cache[cache_key]
            if now - cached_time < HEALTH_CACHE_TTL_SECONDS:
                return cached_val

        start_time = time.time()
        try:
            # Check OpenRouter connection & key validity by pinging the auth endpoint / models
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/lenny-growth-assistant",
                "X-Title": "Lenny Growth Assistant"
            }
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(f"{self.base_url}/auth/key", headers=headers)
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    status = ProviderHealthStatus(
                        is_available=True,
                        provider_name="openrouter",
                        model_name=self.model,
                        message=f"OpenRouter API key is valid. Model: {self.model}",
                        latency_ms=latency
                    )
                elif resp.status_code == 401:
                    status = ProviderHealthStatus(
                        is_available=False,
                        provider_name="openrouter",
                        model_name=self.model,
                        message="OpenRouter authentication failed: Invalid API key.",
                        latency_ms=latency
                    )
                else:
                    status = ProviderHealthStatus(
                        is_available=False,
                        provider_name="openrouter",
                        model_name=self.model,
                        message=f"OpenRouter returned status {resp.status_code}: {resp.text[:100]}",
                        latency_ms=latency
                    )
        except Exception as e:
            status = ProviderHealthStatus(
                is_available=False,
                provider_name="openrouter",
                model_name=self.model,
                message=f"OpenRouter connection check failed: {str(e)}"
            )

        _health_cache[cache_key] = (now, status)
        return status

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        if not self.api_key or not self.api_key.strip():
            raise HTTPException(
                status_code=400,
                detail="OPENROUTER_API_KEY is missing. Please set it in .env or switch to Ollama."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            for item in history:
                messages.append({"role": item.get("role", "user"), "content": item.get("content", "")})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/lenny-growth-assistant",
            "X-Title": "Lenny Growth Assistant",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            logger.info(f"Dispatching generation to OpenRouter model: {self.model}")
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
                    return ""
                elif resp.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="OpenRouter authentication failed. Please verify your OPENROUTER_API_KEY."
                    )
                elif resp.status_code == 402:
                    raise HTTPException(
                        status_code=402,
                        detail="OpenRouter account has insufficient credits."
                    )
                else:
                    raise HTTPException(
                        status_code=502,
                        detail=f"OpenRouter returned HTTP error {resp.status_code}: {resp.text}"
                    )
        except httpx.TimeoutException:
            logger.error("OpenRouter request timed out after 60s")
            raise HTTPException(status_code=504, detail="OpenRouter API request timed out.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error communicating with OpenRouter: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OpenRouter generation error: {str(e)}")


def get_llm_provider(
    provider_name: Optional[str] = None,
    model_name: Optional[str] = None
) -> BaseLLMProvider:
    """
    Factory function returning the configured or requested LLM provider.
    Ensures safe model fallbacks so provider switches don't send mismatched IDs.
    """
    chosen = (provider_name or settings.llm_provider).lower().strip()
    if chosen == "openrouter":
        valid_model = model_name if (model_name and "/" in model_name) else settings.openrouter_model
        return OpenRouterProvider(model=valid_model)
    elif chosen == "ollama":
        valid_model = model_name if (model_name and "/" not in model_name) else "llama3.2"
        return OllamaProvider(model=valid_model)
    else:
        logger.warning(f"Unknown provider '{chosen}'. Falling back to Ollama.")
        return OllamaProvider(model="llama3.2")
