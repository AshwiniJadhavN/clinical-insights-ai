"""
LLM answer generator for the RAG pipeline.

Supports OpenAI and Anthropic via settings.llm_provider.
Protocol + FakeGenerator for offline tests.

HIPAA: Never log question text or answer content.
Log only: model name, citation count, token counts.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol, runtime_checkable

from anthropic import Anthropic
from openai import OpenAI

from backend.rag.retriever import RetrievedChunk
from backend.utils.logger import get_logger

logger = get_logger(__name__)

EXCERPT_LENGTH: int = 200
_CITATION_MARKER = re.compile(r"(?<!\[)\[(\d+)\](?!\])")

NO_CONTEXT_ANSWER: str = (
    "I cannot answer this question because no relevant clinical documents have been "
    "indexed yet. Please upload documents first, then ask your question."
)

SYSTEM_PROMPT: str = """You are a clinical AI assistant. Answer medical and clinical questions based ONLY on the provided context documents.

Rules:
1. Answer exclusively from the context below — do not use external knowledge.
2. If the context lacks sufficient information, respond: "The provided documents do not contain enough information to answer this question."
3. Always cite which context sections you used (e.g., "According to [1]..." or "Based on [2] and [3]...").
4. Be precise and use professional medical writing. Avoid speculation.
5. Never reveal personally identifiable information."""


@dataclass(frozen=True)
class Citation:
    doc_id: str
    original_filename: str
    chunk_index: int
    similarity_score: float
    excerpt: str
    reference_id: int | None = None


@dataclass
class GeneratedAnswer:
    answer: str
    citations: list[Citation]
    model_used: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


@runtime_checkable
class GeneratorProtocol(Protocol):
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GeneratedAnswer: ...


def _build_context(chunks: list[RetrievedChunk]) -> tuple[str, list[Citation]]:
    lines: list[str] = []
    citations: list[Citation] = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(f"[{i}] (from: {chunk.original_filename})\n{chunk.text}")
        citations.append(Citation(
            doc_id=chunk.doc_id, original_filename=chunk.original_filename,
            chunk_index=chunk.chunk_index, similarity_score=chunk.similarity_score,
            excerpt=chunk.text[:EXCERPT_LENGTH], reference_id=i,
        ))
    return "\n\n".join(lines), citations


def _cited_sources(answer: str, available: list[Citation]) -> list[Citation]:
    """Return only sources explicitly referenced by numeric markers in the answer."""
    cited_indices = dict.fromkeys(
        int(match.group(1)) for match in _CITATION_MARKER.finditer(answer)
    )
    return [
        available[index - 1]
        for index in cited_indices
        if 1 <= index <= len(available)
    ]


class OpenAIGenerator:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int) -> None:
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GeneratedAnswer:
        if not chunks:
            return GeneratedAnswer(answer=NO_CONTEXT_ANSWER, citations=[], model_used=self._model)
        context_block, citations = _build_context(chunks)
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {question}"},
                ],
                temperature=self._temperature,
                max_tokens=self._max_tokens,
            )
            answer = response.choices[0].message.content or ""
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0
        except Exception as exc:
            raise RuntimeError("LLM generation failed. Check provider configuration.") from exc
        logger.info("Generated: model=%s citations=%d prompt_tokens=%d completion_tokens=%d",
                    self._model, len(citations), prompt_tokens, completion_tokens)
        return GeneratedAnswer(answer=answer, citations=_cited_sources(answer, citations), model_used=self._model,
                               prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)


class AnthropicGenerator:
    def __init__(self, api_key: str, model: str, temperature: float, max_tokens: int) -> None:
        if not api_key:
            raise ValueError("Anthropic API key is required.")
        self._client = Anthropic(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GeneratedAnswer:
        if not chunks:
            return GeneratedAnswer(answer=NO_CONTEXT_ANSWER, citations=[], model_used=self._model)
        context_block, citations = _build_context(chunks)
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Context:\n{context_block}\n\nQuestion: {question}"}],
                temperature=self._temperature,
            )
            answer = response.content[0].text if response.content else ""
            prompt_tokens = response.usage.input_tokens if response.usage else 0
            completion_tokens = response.usage.output_tokens if response.usage else 0
        except Exception as exc:
            raise RuntimeError("LLM generation failed. Check provider configuration.") from exc
        logger.info("Generated: model=%s citations=%d prompt_tokens=%d completion_tokens=%d",
                    self._model, len(citations), prompt_tokens, completion_tokens)
        return GeneratedAnswer(answer=answer, citations=_cited_sources(answer, citations), model_used=self._model,
                               prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)


class FakeGenerator:
    """Deterministic test double that returns a canned answer without calling any LLM."""

    _MODEL = "fake-llm"

    def generate(self, question: str, chunks: list[RetrievedChunk]) -> GeneratedAnswer:
        if not chunks:
            return GeneratedAnswer(answer=NO_CONTEXT_ANSWER, citations=[], model_used=self._MODEL)
        _, citations = _build_context(chunks)
        return GeneratedAnswer(
            answer=f"Based on the provided documents [1]: Test answer for '{question[:50]}'.",
            citations=_cited_sources("[1]", citations),
            model_used=self._MODEL,
            prompt_tokens=100,
            completion_tokens=50,
        )


def create_generator(settings) -> GeneratorProtocol:
    if settings.llm_provider == "anthropic":
        return AnthropicGenerator(
            api_key=settings.anthropic_api_key, model=settings.anthropic_model,
            temperature=settings.llm_temperature, max_tokens=settings.llm_max_tokens,
        )
    return OpenAIGenerator(
        api_key=settings.openai_api_key, model=settings.openai_model,
        temperature=settings.llm_temperature, max_tokens=settings.llm_max_tokens,
    )
