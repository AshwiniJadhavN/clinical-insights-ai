# Frontend Guide

## Purpose

The frontend provides a focused guided workflow for demonstrating Clinical
Insights AI. It is not a broad analytics dashboard. It exists to make the core
platform behavior visible:

1. Upload clinical source material.
2. Ask a focused question.
3. Review the evidence-grounded answer.
4. Inspect citations, confidence, evidence status, and safety metadata.

## Product Scope

The active UI contains one primary workspace:

- **Evidence Workspace**: document upload, document list, query input, response
  card, and recent query history.

Risk dashboards, traceability dashboards, chart-heavy command centers, and
interactive architecture views were removed from the active frontend to keep the
demo grounded and easy to explain. Systems safety and traceability remain
documented in the repository under `docs/`.

## Component Map

```text
src/
├── App.tsx                         # Workflow state and view routing
├── main.tsx                        # React entry point
├── components/
│   ├── AppShell.tsx                # Header, mode controls, reset action
│   ├── AiResponseCard.tsx          # Answer, citations, confidence, safety metadata
│   ├── ClinicalDocumentViewer.tsx  # Document/evidence presentation helper
│   └── ui.tsx                      # Shared cards, buttons, badges, alerts, states
├── views/
│   └── DocumentWorkspace.tsx       # Main evidence workflow
└── lib/
    ├── api.ts                      # Backend client
    └── utils.ts                    # Shared helpers
```

## Workflow Modes

- **Guided mode**: default mode for demos. It keeps the user focused on the
  upload-question-review loop.
- **Explore mode**: keeps the same workspace available without presenting the
  flow as step-by-step.

The UI no longer includes a dark-mode toggle. The current demo direction uses a
consistent light clinical interface.

## API Contract

The frontend expects the backend to expose:

- `GET /health`
- `GET /documents`
- `POST /documents/upload`
- `POST /query`

The response card displays:

- `answer`
- `citations`
- `retrieved_chunk`
- `confidence_score`
- `confidence_level`
- `evidence_status`
- `safety_decision`
- `refusal_reason`
- `review_required`
- `correlation_id`

## Design Principles

- Prefer clarity over decoration.
- Keep controls close to the workflow they affect.
- Show safety metadata without turning the UI into a monitoring dashboard.
- Use restrained color for status and confidence signals.
- Keep animations fast and purposeful.

## Verification

```bash
npm run build
```

The root repo verification also runs backend tests, coverage, Ruff, Pyright, and
CI-style gates.
