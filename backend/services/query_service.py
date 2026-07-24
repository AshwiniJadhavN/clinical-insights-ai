"""
Query orchestration service.

Pipeline: embed question → retrieve chunks → score confidence → generate answer → audit log

HIPAA:
  Log only: query_id, retrieval_count, confidence_score, confidence_level, model_used
  Never log question text or answer content
  audit_service stores only character lengths, not raw text
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from time import perf_counter
from typing import TYPE_CHECKING

from backend.config import Settings
from backend.evaluation.scorer import compute_confidence
from backend.observability.metrics import record_rag_retrieval
from backend.rag.embedder import EmbedderProtocol
from backend.rag.generator import GeneratorProtocol
from backend.rag.retriever import RetrieverProtocol
from backend.refusal.logic import evaluate_retrieval
from backend.schemas.query import CitationInfo, QueryResponse
from backend.safety.decision_engine import SafetyDecisionEngine
from backend.safety.models import SafetyDecision
from backend.utils.logger import get_logger

if TYPE_CHECKING:
    from backend.services.audit_service import AuditService

logger = get_logger(__name__)

INSUFFICIENT_EVIDENCE_ANSWER = (
    "The retrieved evidence is not strong enough to answer this question safely. "
    "Please upload more relevant clinical documents or ask a question that is directly "
    "supported by the indexed content."
)
CLARIFICATION_ANSWER = (
    "The retrieved documents contain conflicting evidence for this question. "
    "Please refine the request, narrow the document scope, or ask a human reviewer to adjudicate the discrepancy."
)
SAFETY_REFUSAL_ANSWER = (
    "This request cannot be answered safely because the safety layer detected a policy violation or unsupported output condition."
)


class QueryService:
    def __init__(
        self,
        settings: Settings,
        embedder: EmbedderProtocol,
        retriever: RetrieverProtocol,
        generator: GeneratorProtocol,
        safety_engine: SafetyDecisionEngine,
        audit_service: "AuditService | None" = None,
    ) -> None:
        self._settings = settings
        self._embedder = embedder
        self._retriever = retriever
        self._generator = generator
        self._safety_engine = safety_engine
        self._audit = audit_service

    async def query(self, question: str, top_k: int | None = None, correlation_id: str | None = None) -> QueryResponse:
        started = perf_counter()
        query_id = str(uuid.uuid4())
        effective_top_k = top_k if top_k is not None else self._settings.retrieval_top_k
        sanitized_question = self._safety_engine.sanitize_question(question)
        input_decision = self._safety_engine.evaluate_input(sanitized_question)
        if input_decision.action != "answer":
            return self._build_response(
                query_id=query_id,
                question=sanitized_question,
                answer=SAFETY_REFUSAL_ANSWER,
                chunks=[],
                confidence_score=0.0,
                confidence_level="none",
                evidence_status="missing",
                model_used="not-called-safety-refusal",
                safety_decision=input_decision,
                correlation_id=correlation_id,
                processing_time_ms=int((perf_counter() - started) * 1000),
            )

        query_vector = self._embedder.embed(sanitized_question)
        chunks = self._retriever.search(query_vector, top_k=effective_top_k)

        decision = evaluate_retrieval(chunks, "backend/governance/rules.yml")
        conf = compute_confidence(chunks, min_threshold=decision.threshold)
        evidence_status = decision.evidence_status
        record_rag_retrieval(hit=evidence_status == "sufficient")
        safety_decision = self._safety_engine.evaluate_evidence(
            chunks=chunks,
            evidence_status=evidence_status,
            confidence_score=conf.score,
            confidence_level=conf.level,
        )

        generated = None
        final_decision = safety_decision
        if safety_decision.action == "answer":
            try:
                generated = await asyncio.wait_for(
                    asyncio.to_thread(self._generator.generate, sanitized_question, chunks),
                    timeout=self._settings.llm_timeout_seconds,
                )
            except TimeoutError:
                final_decision = self._safety_engine.timeout_decision()
            else:
                final_decision = self._safety_engine.evaluate_output(
                    answer=generated.answer,
                    citations=generated.citations,
                    chunks=chunks,
                    confidence_level=conf.level,
                )

        citations = _citation_info(generated.citations, chunks) if generated else _chunk_citation_info(chunks)

        answer = self._answer_for_decision(final_decision, generated.answer if generated else None)
        model_used = generated.model_used if generated else self._model_for_decision(final_decision)
        result = self._build_response(
            query_id=query_id,
            question=sanitized_question,
            answer=answer,
            chunks=chunks,
            confidence_score=conf.score,
            confidence_level=conf.level,
            evidence_status=evidence_status,
            model_used=model_used,
            safety_decision=final_decision,
            citations=citations,
            correlation_id=correlation_id,
            processing_time_ms=int((perf_counter() - started) * 1000),
        )

        if self._audit:
            self._audit.log_query(
                query_id=query_id, question=sanitized_question, answer=result.answer,
                retrieval_count=len(chunks), confidence_score=conf.score,
                confidence_level=conf.level, model_used=result.model_used,
                safety_decision=result.safety_decision,
                refusal_reason=result.refusal_reason,
                correlation_id=correlation_id,
                prompt_version=self._settings.prompt_version,
                retrieved_doc_ids=sorted({chunk.doc_id for chunk in chunks}),
                processing_time_ms=int((perf_counter() - started) * 1000),
                review_required=result.review_required,
            )

        logger.info(
            "Query evaluated by safety layer",
            extra={
                "query_id": query_id,
                "correlation_id": correlation_id,
                "prompt_version": self._settings.prompt_version,
                "model_version": result.model_used,
                "retrieved_doc_ids": sorted({chunk.doc_id for chunk in chunks}),
                "confidence_score": conf.score,
                "safety_decision": result.safety_decision,
                "refusal_reason": result.refusal_reason,
                "processing_time_ms": int((perf_counter() - started) * 1000),
            },
        )
        return result

    def _build_response(
        self,
        *,
        query_id: str,
        question: str,
        answer: str,
        chunks,
        confidence_score: float,
        confidence_level: str,
        evidence_status: str,
        model_used: str,
        safety_decision: SafetyDecision,
        citations: list[CitationInfo] | None = None,
        correlation_id: str | None = None,
        processing_time_ms: int | None = None,
    ) -> QueryResponse:
        return QueryResponse(
            query_id=query_id,
            question=question,
            answer=answer,
            citations=citations or [],
            retrieved_chunk=chunks[0].text if chunks else None,
            confidence_score=confidence_score,
            confidence_level=confidence_level,
            evidence_status=evidence_status,
            model_used=model_used,
            retrieval_count=len(chunks),
            created_at=datetime.now(timezone.utc),
            safety_decision=safety_decision.action,
            refusal_reason=safety_decision.refusal_reason,
            review_required=safety_decision.review_required,
            correlation_id=correlation_id,
        )

    def _answer_for_decision(self, decision: SafetyDecision, generated_answer: str | None) -> str:
        if decision.action == "answer" and generated_answer:
            return generated_answer
        if decision.action == "clarify":
            return CLARIFICATION_ANSWER
        if decision.action == "refuse":
            return SAFETY_REFUSAL_ANSWER
        return INSUFFICIENT_EVIDENCE_ANSWER

    def _model_for_decision(self, decision: SafetyDecision) -> str:
        if decision.action == "clarify":
            return "not-called-clarification"
        if decision.action == "refuse":
            return "not-called-safety-refusal"
        return "not-called-insufficient-evidence"


def _chunk_citation_info(chunks) -> list[CitationInfo]:
    return [
        CitationInfo(
            doc_id=chunk.doc_id,
            original_filename=chunk.original_filename,
            chunk_index=chunk.chunk_index,
            similarity_score=chunk.similarity_score,
            excerpt=chunk.text[:200],
            start_char=chunk.start_char,
            end_char=chunk.end_char,
        )
        for chunk in chunks
    ]


def _citation_info(citations, chunks) -> list[CitationInfo]:
    chunk_offsets = {(chunk.doc_id, chunk.chunk_index): (chunk.start_char, chunk.end_char) for chunk in chunks}
    return [
        CitationInfo(
            doc_id=citation.doc_id,
            original_filename=citation.original_filename,
            chunk_index=citation.chunk_index,
            similarity_score=citation.similarity_score,
            excerpt=citation.excerpt,
            start_char=chunk_offsets.get((citation.doc_id, citation.chunk_index), (0, 0))[0],
            end_char=chunk_offsets.get((citation.doc_id, citation.chunk_index), (0, 0))[1],
        )
        for citation in citations
    ]
