"""
Centralized logging configuration.

All modules call `get_logger(__name__)`. Consistent format, level controlled
from one place, noisy third-party libraries suppressed.
"""

import logging
import json
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Small JSON formatter for container-friendly structured logs."""

    _EXTRA_KEYS = (
        "request_id",
        "correlation_id",
        "query_id",
        "prompt_version",
        "model_version",
        "retrieved_doc_ids",
        "confidence_score",
        "safety_decision",
        "refusal_reason",
        "processing_time_ms",
        "review_decision",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in self._EXTRA_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload)


def setup_logging(log_level: str = "INFO") -> None:
    try:
        from backend.config import get_settings
        level_str = get_settings().log_level
    except Exception:
        level_str = log_level
    level = getattr(logging, level_str.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)
    for noisy_lib in ("httpx", "httpcore", "chromadb", "sentence_transformers", "openai"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
