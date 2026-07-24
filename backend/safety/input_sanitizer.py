from __future__ import annotations

import re

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


class InputSanitizer:
    """Normalize untrusted input before it enters retrieval or generation."""

    def sanitize(self, value: str) -> str:
        normalized = _CONTROL_CHARS.sub(" ", value)
        return " ".join(normalized.split()).strip()
