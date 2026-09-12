from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables and .env file.
    """
    # Active LLM Provider ('ollama' or 'openrouter')
    llm_provider: str = "ollama"

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # OpenRouter Configuration
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Database Configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/lenny_growth"

    # RAG & Embedding Settings
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 4
    rag_score_threshold: float = 0.20

    # Server & Port Settings
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 8501
    backend_api_url: str = "http://localhost:8000"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


settings = Settings()
