# Confidence Signal Review

Date: 2026-07-08

## Summary

The current `confidence_score` is a retrieval-strength heuristic derived from similarity scores of retrieved chunks.

It is not a calibrated statistical probability that the answer is correct.

## How It Is Calculated Today

Implementation source: `backend/evaluation/scorer.py`

- Input: retrieved chunk similarity scores (`0.0` to `1.0`)
- Score: arithmetic mean of chunk similarities
- Bands:
  - `high` if mean >= 0.70
  - `medium` if mean >= 0.45
  - `low` otherwise
  - `none` when no chunks are retrieved
- Additional count: number of chunks above a risk-based minimum threshold

In query orchestration (`backend/services/query_service.py`):
- The score contributes to safety decisions and metadata.
- The score is logged/audited as telemetry.

## Correct Interpretation

`confidence_score` represents retrieval similarity concentration in the current retrieved set.

It does not represent:
- probability of factual correctness
- uncertainty bounds
- calibrated model confidence
- clinical safety or treatment validity

## Current Risks

- Similarity can be high while evidence is incomplete or contextually wrong.
- Similarity can be low for correct but poorly chunked or paraphrased evidence.
- Mean score can hide outlier chunks with contradictory evidence.

## Wording Guidance

Use:
- "retrieval confidence heuristic"
- "retrieval-strength signal"
- "similarity-based confidence score"

Avoid:
- "model certainty"
- "probability of correctness"
- "clinical confidence"

## Recommended Non-Breaking Improvements

1. Add API field description clarifying non-probabilistic semantics.
2. Track per-domain calibration notes in evaluation docs.
3. Add drift monitoring for score distribution changes after ingestion/config updates.
4. Add offline benchmark reporting that compares score bands to labeled QA quality.
