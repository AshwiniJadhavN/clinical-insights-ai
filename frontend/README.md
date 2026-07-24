# Clinical Insights AI Frontend

Focused React interface for the Clinical Insights AI evidence workspace.

The frontend is intentionally narrow: it supports document upload, clinical
question entry, evidence-grounded responses, confidence display, citations, and
recent query history. It avoids extra dashboard surfaces so the demo stays
clear and aligned with the platform's core safety story.

## Design Direction

- Light, professional clinical software interface
- Deep medical blue, teal, slate, white, and soft grey palette
- Inter typography with clear hierarchy
- Guided workflow by default with optional explore mode
- Accessible focus states, semantic controls, and responsive layout
- Purposeful Framer Motion transitions

## Key Features

- Evidence workspace for document upload and review
- Clinical question workflow backed by the FastAPI API
- AI response cards with citations, evidence status, confidence, and safety metadata
- Recent query history for demo continuity
- Health-aware API integration with graceful fallback states
- Reset control for repeatable demos

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Production Build

```bash
npm run build
npm run preview
```

## Technology Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- Framer Motion
- Lucide React
- clsx
- tailwind-merge

## Current Source Layout

```text
src/
├── App.tsx
├── main.tsx
├── styles.css
├── components/
│   ├── AiResponseCard.tsx
│   ├── AppShell.tsx
│   ├── ClinicalDocumentViewer.tsx
│   └── ui.tsx
├── views/
│   └── DocumentWorkspace.tsx
├── lib/
│   ├── api.ts
│   └── utils.ts
└── data/
    └── mock.ts
```

## Backend Integration

The Vite dev server proxies API calls to the FastAPI backend.

Primary endpoints:

- `GET /health`
- `GET /documents`
- `POST /documents/upload`
- `POST /query`

## Verification

```bash
npm run build
```

The root repository CI also validates Python tests, coverage, type checking,
security gates, Docker build readiness, and smoke tests.
