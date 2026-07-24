"""
AI safety guardrails for the RAG query pipeline.

Checks: minimum length, prompt injection patterns, harmful intent patterns.
Disabled entirely when settings.enable_guardrails is False.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.safety.input_sanitizer import InputSanitizer
from backend.safety.prompt_injection import PromptInjectionDetector

MIN_QUESTION_LENGTH: int = 5

_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
        r"forget\s+(everything|all(\s+previous)?\s+instructions?)",
        r"\bsystem\s+prompt\b",
        r"\bjailbreak\b",
        r"\bDAN\s+mode\b",
        r"bypass\s+(your\s+)?(safety|filter|restriction|guardrail)",
        r"override\s+(your\s+)?(instruction|system|setting)",
        r"act\s+as\s+an?\s+(unrestricted|unfiltered|different|alternative)",
        r"pretend\s+(you\s+(have\s+no|are\s+not\s+bound|are\s+free|can\s+do))",
    ]
]

_HARMFUL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"delete\s+(the\s+)?patient\s+database",
        r"delete\s+all\s+(patient\s+)?records",
        r"override\s+(the\s+)?governance\s+ya?ml",
        r"diagnose\s+(this\s+)?(terminal\s+illness|cancer|patient)",
        r"how\s+to\s+overdose",
        r"\blethal\s+dose\b",
        r"how\s+to\s+(commit\s+)?suicide",
        r"how\s+to\s+self[\s\-]?harm",
        r"how\s+to\s+poison\s+(someone|a\s+person|people|a\s+patient)",
        r"kill\s+(myself|themselves|someone|a\s+person|a\s+patient)",
    ]
]


@dataclass(frozen=True)
class SafetyResult:
    is_safe: bool
    action: str
    reason: str | None = None


_SAFE = SafetyResult(is_safe=True, action="allow")


class SafetyChecker:
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._sanitizer = InputSanitizer()
        self._injection_detector = PromptInjectionDetector()

    def check_input(self, question: str) -> SafetyResult:
        if not self._enabled:
            return _SAFE
        sanitized = self._sanitizer.sanitize(question)
        if len(sanitized) < MIN_QUESTION_LENGTH:
            return SafetyResult(is_safe=False, action="block",
                                reason="Question is too short. Please provide a complete clinical question.")
        injection = self._injection_detector.detect(sanitized)
        if injection.detected:
            return SafetyResult(is_safe=False, action="block", reason=injection.reason)
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(sanitized):
                return SafetyResult(is_safe=False, action="block",
                                    reason="Input contains patterns that cannot be processed by this system.")
        for pattern in _HARMFUL_PATTERNS:
            if pattern.search(sanitized):
                return SafetyResult(is_safe=False, action="block",
                                    reason="Query requests information that cannot be provided by this system.")
        return _SAFE
