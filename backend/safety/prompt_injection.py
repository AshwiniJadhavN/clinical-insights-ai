from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptInjectionResult:
    detected: bool
    reason: str | None = None
    pattern: str | None = None


class PromptInjectionDetector:
    def __init__(self) -> None:
        self._patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in [
                r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
                r"forget\s+(everything|all(\s+previous)?\s+instructions?)",
                r"\bsystem\s+prompt\b",
                r"\bdeveloper\s+message\b",
                r"\bjailbreak\b",
                r"\bDAN\s+mode\b",
                r"bypass\s+(your\s+)?(safety|filter|restriction|guardrail)",
                r"override\s+(your\s+)?(instruction|system|setting)",
                r"act\s+as\s+an?\s+(unrestricted|unfiltered|different|alternative)",
                r"reveal\s+(the\s+)?hidden\s+prompt",
            ]
        ]

    def detect(self, question: str) -> PromptInjectionResult:
        for pattern in self._patterns:
            if pattern.search(question):
                return PromptInjectionResult(
                    detected=True,
                    reason="Prompt injection patterns cannot be processed by this system.",
                    pattern=pattern.pattern,
                )
        return PromptInjectionResult(detected=False)
