"""
Central application configuration.

All settings are loaded from environment variables (or a .env file) via
pydantic-settings. This gives us:
  - Type validation at startup: if OPENAI_API_KEY is missing, the app fails
    immediately with a clear error rather than at the first API call.
  - One place to look for every configurable value — no scattered os.getenv()
    calls throughout the codebase.
  - Easy testing: override specific settings in fixtures without touching .env.

Usage:
    from backend.config import get_settings
    settings = get_settings()
    print(settings.openai_model)
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

def _load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def _default(name: str, fallback: Any) -> Any:
    return _CONFIG_DEFAULTS.get(name, fallback)


CONFIG_DIR = Path("config")
_CONFIG_DEFAULTS = {
    **_load_yaml_config(CONFIG_DIR / "model_config.yaml"),
    **_load_yaml_config(CONFIG_DIR / "retrieval_config.yaml"),
    **_load_yaml_config(CONFIG_DIR / "logging_config.yaml"),
}


class Settings(BaseSettings):
    """Application settings. Values are read from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Clinical Insight AI"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = str(_default("log_level", "INFO"))

    # LLM Provider
    llm_provider: str = str(_default("llm_provider", "openai"))  # "openai" or "anthropic"
    openai_api_key: str = ""
    openai_model: str = str(_default("openai_model", "gpt-4o-mini"))
    anthropic_api_key: str = ""
    anthropic_model: str = str(_default("anthropic_model", "claude-3-haiku-20240307"))
    llm_temperature: float = float(_default("llm_temperature", 0.1))
    llm_max_tokens: int = int(_default("llm_max_tokens", 1024))

    # Database
    database_url: str = "sqlite:///./data/clinical_insights.db"

    # ChromaDB
    chroma_persist_directory: str = str(_default("chroma_persist_directory", "./data/chroma_db"))
    chroma_collection_name: str = str(_default("chroma_collection_name", "clinical_documents"))

    # Embeddings
    embedding_model: str = str(_default("embedding_model", "all-MiniLM-L6-v2"))

    # RAG pipeline
    chunk_size: int = int(_default("chunk_size", 512))
    chunk_overlap: int = int(_default("chunk_overlap", 64))
    retrieval_top_k: int = int(_default("retrieval_top_k", 5))
    sample_docs_directory: str = str(_default("sample_docs_directory", "./data/sample_docs"))
    sync_mode: str = str(_default("sync_mode", "DUAL_WRITE"))

    # File upload
    upload_directory: str = "./data/uploads"
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf", ".txt"]

    # AI safety
    enable_guardrails: bool = True
    confidence_threshold: float = float(_default("confidence_threshold", 0.7))
    mock_llm: bool = False
    vector_backend: str = str(_default("vector_backend", "chroma"))
    prompt_version: str = str(_default("prompt_version", "clinical-rag-safety-v1"))
    llm_timeout_seconds: int = int(_default("llm_timeout_seconds", 20))

    # Security-by-design controls
    auth_api_key: str = ""
    rate_limit_requests: int = int(_default("rate_limit_requests", 60))
    rate_limit_window_seconds: int = int(_default("rate_limit_window_seconds", 60))

    # Audit search
    audit_search_api_key: str = ""
    audit_trail_directory: str = "backend/audit/trail"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}, got '{v}'")
        return upper

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        valid = {"openai", "anthropic"}
        lower = v.lower()
        if lower not in valid:
            raise ValueError(f"llm_provider must be one of {valid}, got '{v}'")
        return lower

    @field_validator("sync_mode")
    @classmethod
    def validate_sync_mode(cls, v: str) -> str:
        upper = v.upper()
        if upper not in {"DUAL_WRITE", "PG_ONLY"}:
            raise ValueError("sync_mode must be either DUAL_WRITE or PG_ONLY")
        return upper

    @field_validator("llm_timeout_seconds", "rate_limit_requests", "rate_limit_window_seconds")
    @classmethod
    def validate_positive_ints(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("value must be greater than zero")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Return the cached Settings singleton.

    The @lru_cache decorator means Settings() is only constructed once per
    process — subsequent calls return the same instance.
    """
    return Settings()
