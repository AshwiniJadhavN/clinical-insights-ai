"""Deterministic local retrieval evaluation for the sample document corpus."""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.rag.chunker import chunk_text  # noqa: E402
from backend.rag.embedder import EmbeddingVector  # noqa: E402
from backend.rag.retriever import RetrievedChunk  # noqa: E402

TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")
DEFAULT_DATASET_PATH = ROOT / "evals" / "test_queries.json"
DEFAULT_DOCS_DIR = ROOT / "data" / "sample_docs"
VECTOR_DIMENSION = 64


@dataclass(frozen=True)
class RetrievalEvalCase:
    case_id: str
    question: str
    expected_doc_ids: tuple[str, ...]
    expected_sources: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalCaseResult:
    case_id: str
    question: str
    expected_doc_ids: tuple[str, ...]
    expected_sources: tuple[str, ...]
    top_doc_ids: tuple[str, ...]
    top_sources: tuple[str, ...]
    top_1_hit: bool
    top_3_hit: bool
    latency_ms: float


@dataclass(frozen=True)
class RetrievalEvalReport:
    total_cases: int
    top_1_accuracy: float
    top_3_accuracy: float
    average_latency_ms: float
    missing_evidence_cases: tuple[str, ...]
    case_results: tuple[RetrievalCaseResult, ...]

    @property
    def passed(self) -> bool:
        return not self.missing_evidence_cases


class LocalVectorRetriever:
    def __init__(self, docs_dir: Path, vector_dimension: int = VECTOR_DIMENSION) -> None:
        self._embedder = DeterministicTokenEmbedder(vector_dimension)
        self._chunks = _load_documents(docs_dir)
        self._indexed_chunks = [
            _IndexedChunk(chunk=chunk, embedding=self._embedder.embed(chunk.text))
            for chunk in self._chunks
        ]

    def search(self, question: str, top_k: int) -> list[RetrievedChunk]:
        query_vector = self._embedder.embed(question)
        ranked_chunks = sorted(
            (
                _ScoredChunk(chunk=indexed.chunk, score=_cosine_similarity(query_vector, indexed.embedding))
                for indexed in self._indexed_chunks
            ),
            key=lambda item: (-item.score, item.chunk.doc_id, item.chunk.chunk_index),
        )
        return [
            RetrievedChunk(
                text=scored.chunk.text,
                doc_id=scored.chunk.doc_id,
                chunk_index=scored.chunk.chunk_index,
                original_filename=scored.chunk.original_filename,
                similarity_score=round(scored.score, 4),
                start_char=scored.chunk.start_char,
                end_char=scored.chunk.end_char,
            )
            for scored in ranked_chunks[:top_k]
            if scored.score > 0.0
        ]


class DeterministicTokenEmbedder:
    def __init__(self, dimension: int) -> None:
        self._dimension = dimension

    def embed(self, text: str) -> EmbeddingVector:
        vector = [0.0] * self._dimension
        for token in _tokens(text):
            slot = sum(ord(char) for char in token) % self._dimension
            vector[slot] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [round(value / norm, 6) for value in vector]


@dataclass(frozen=True)
class _ChunkRecord:
    text: str
    doc_id: str
    chunk_index: int
    original_filename: str
    start_char: int
    end_char: int


@dataclass(frozen=True)
class _IndexedChunk:
    chunk: _ChunkRecord
    embedding: EmbeddingVector


@dataclass(frozen=True)
class _ScoredChunk:
    chunk: _ChunkRecord
    score: float


@dataclass(frozen=True)
class _TopDocs:
    doc_ids: tuple[str, ...]
    sources: tuple[str, ...]


class RetrievalHarness:
    def __init__(self, docs_dir: Path) -> None:
        self._retriever = LocalVectorRetriever(docs_dir, VECTOR_DIMENSION)

    def search(self, question: str, top_k: int) -> _TopDocs:
        chunks = self._retriever.search(question, top_k=top_k * 3)
        doc_ids: list[str] = []
        sources: list[str] = []
        for chunk in chunks:
            if chunk.doc_id not in doc_ids:
                doc_ids.append(chunk.doc_id)
                sources.append(chunk.original_filename)
            if len(doc_ids) >= top_k:
                break
        return _TopDocs(doc_ids=tuple(doc_ids), sources=tuple(sources))


def run_retrieval_eval(
    dataset_path: Path = DEFAULT_DATASET_PATH,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> RetrievalEvalReport:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    top_k = int(dataset.get("top_k", 3))
    cases = tuple(
        RetrievalEvalCase(
            case_id=str(case["id"]),
            question=str(case["question"]),
            expected_doc_ids=tuple(str(doc_id) for doc_id in case["expected_doc_ids"]),
            expected_sources=tuple(str(source) for source in case["expected_sources"]),
        )
        for case in dataset.get("cases", [])
    )
    retriever = RetrievalHarness(docs_dir)

    case_results: list[RetrievalCaseResult] = []
    top_1_hits = 0
    top_3_hits = 0
    missing_evidence_cases: list[str] = []
    total_latency_ms = 0.0

    for case in cases:
        started = perf_counter()
        top_docs = retriever.search(case.question, top_k=top_k)
        latency_ms = (perf_counter() - started) * 1000
        top_1_hit = bool(top_docs.doc_ids[:1] and top_docs.doc_ids[0] in case.expected_doc_ids)
        top_3_hit = any(doc_id in case.expected_doc_ids for doc_id in top_docs.doc_ids[:3])
        if top_1_hit:
            top_1_hits += 1
        if top_3_hit:
            top_3_hits += 1
        else:
            missing_evidence_cases.append(case.case_id)
        total_latency_ms += latency_ms
        case_results.append(
            RetrievalCaseResult(
                case_id=case.case_id,
                question=case.question,
                expected_doc_ids=case.expected_doc_ids,
                expected_sources=case.expected_sources,
                top_doc_ids=top_docs.doc_ids,
                top_sources=top_docs.sources,
                top_1_hit=top_1_hit,
                top_3_hit=top_3_hit,
                latency_ms=round(latency_ms, 3),
            )
        )

    total_cases = len(cases)
    return RetrievalEvalReport(
        total_cases=total_cases,
        top_1_accuracy=round(top_1_hits / total_cases, 4) if total_cases else 0.0,
        top_3_accuracy=round(top_3_hits / total_cases, 4) if total_cases else 0.0,
        average_latency_ms=round(total_latency_ms / total_cases, 3) if total_cases else 0.0,
        missing_evidence_cases=tuple(missing_evidence_cases),
        case_results=tuple(case_results),
    )


def render_report(report: RetrievalEvalReport) -> str:
    summary_rows = [
        ["Total cases", str(report.total_cases)],
        ["Top-1 retrieval accuracy", f"{report.top_1_accuracy:.2%}"],
        ["Top-3 retrieval accuracy", f"{report.top_3_accuracy:.2%}"],
        ["Missing evidence cases", str(len(report.missing_evidence_cases))],
        ["Average retrieval latency", f"{report.average_latency_ms:.3f} ms"],
    ]
    case_rows = [
        [
            result.case_id,
            ", ".join(result.expected_doc_ids),
            _clip(", ".join(result.top_doc_ids[:3]) or "none", 36),
            "yes" if result.top_1_hit else "no",
            "yes" if result.top_3_hit else "no",
            f"{result.latency_ms:.3f}",
        ]
        for result in report.case_results
    ]

    sections = [
        "Retrieval Evaluation Summary",
        _format_table(["Metric", "Value"], summary_rows),
        "Retrieval Evaluation Details",
        _format_table(
            ["Case", "Expected doc", "Top docs", "Top-1", "Top-3", "Latency ms"],
            case_rows,
        ),
    ]
    if report.missing_evidence_cases:
        sections.extend(
            [
                "Missing Evidence Cases",
                "\n".join(f"- {case_id}" for case_id in report.missing_evidence_cases),
            ]
        )
    return "\n\n".join(sections)


def main() -> int:
    report = run_retrieval_eval()
    print(render_report(report))
    return 0 if report.passed else 1


def _load_documents(docs_dir: Path) -> list[_ChunkRecord]:
    documents: list[_ChunkRecord] = []
    for path in sorted(docs_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        chunks = chunk_text(text, doc_id=path.stem)
        for chunk in chunks:
            documents.append(
                _ChunkRecord(
                    text=chunk.text,
                    doc_id=chunk.doc_id,
                    chunk_index=chunk.chunk_index,
                    original_filename=path.name,
                    start_char=chunk.start_char,
                    end_char=chunk.end_char,
                )
            )
    return documents


def _cosine_similarity(left: EmbeddingVector, right: EmbeddingVector) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(value.lower())
        if len(token) > 2 or token.isdigit()
    }


def _format_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def format_row(row: list[str]) -> str:
        return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    lines = [format_row(headers), separator]
    lines.extend(format_row(row) for row in rows)
    return "\n".join(lines)


def _clip(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length - 3]}..."


if __name__ == "__main__":
    raise SystemExit(main())