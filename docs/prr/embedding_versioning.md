# Embedding and Chunking Versioning Review

Date: 2026-07-08

## Current Behavior

Ingestion pipeline (`backend/services/document_service.py`) uses runtime settings:
- `chunk_size`
- `chunk_overlap`
- `embedding_model`

Retrieved vectors are indexed, but version metadata for chunking profile and embedding model is not consistently persisted and enforced as a compatibility boundary across all retrieval paths.

## What Happens If Chunk Size Changes

- New documents are chunked with the new settings.
- Existing indexed documents remain chunked with prior settings unless manually reprocessed.
- Retrieval operates over a mixed-granularity corpus.

Risk:
- similarity ranking behavior and citation granularity can drift.

## What Happens If Embedding Model Changes

- New vectors are generated with the new embedding model.
- Existing vectors remain from the old model unless manually reindexed.
- Retrieval quality may degrade or become inconsistent when vectors are mixed.

Risk:
- silent relevance degradation and non-obvious behavior changes.

## Current Operational Limitation

There is no built-in hard guard that prevents mixed-version corpora from serving queries.

## Recommended Approach (Incremental)

1. Add metadata fields per indexed chunk/document:
   - embedding model identifier
   - embedding dimension
   - chunk profile version (`size`, `overlap`)
2. Add compatibility checks at query time:
   - warn or fail when mixed incompatible versions exceed threshold
3. Add a documented reindex workflow:
   - version bump -> bulk reindex -> validation -> switch
4. Add CI/runtime checks that detect drift between configured model and indexed corpus metadata.

These changes can be introduced without redesigning the retrieval architecture.
