# ADR 0007: Retrieval-Augmented Generation for Clinical Q&A

## Status

Accepted

## Context

Clinical-style question answering cannot rely on unconstrained model memory. The system needs evidence-grounded responses and explicit refusal behavior when support is weak.

## Decision

Use a retrieval-augmented generation (RAG) pipeline:

1. retrieve candidate evidence chunks
2. evaluate evidence strength
3. allow generation only when safety policy permits
4. return citations and evidence metadata

## Consequences

- Response quality is coupled to corpus quality and indexing quality, not only model quality.
- The system can fail closed (refuse/clarify) when evidence is weak.
- Reviewers can inspect supporting evidence and citations.

Trade-off:
- Retrieval tuning, chunking strategy, and embedding choices become operational responsibilities.
