# Frontend Design System

## Design Goal

The Clinical Insights AI frontend uses a calm, professional clinical software
style. The interface is intentionally focused on the evidence workflow rather
than broad dashboard analytics.

## Principles

- Trust through clarity and restraint
- Evidence and confidence visible at the point of use
- Light clinical interface with strong contrast
- Minimal visual noise
- Consistent spacing and readable type
- Purposeful motion only

## Palette

| Role | Color |
|---|---|
| Background | `#F8FAFC` |
| Surface | `#FFFFFF` |
| Primary text | `#0B1F33` |
| Secondary text | `#475569` |
| Primary blue | `#173B57` |
| Teal accent | `#0F766E` |
| Border | `#D7E4EC` |
| Success | `#16A34A` |
| Warning | `#D97706` |
| Critical | `#E11D48` |
| Information | `#0284C7` |

## Typography

- Primary font: Inter/system UI
- Monospace: SFMono-Regular, Consolas, Liberation Mono
- Page titles: 28-32px
- Section titles: 20-24px
- Body: 14-16px
- Captions: 12-13px

## Spacing

The UI follows a 4px spacing base:

```text
4, 8, 12, 16, 24, 32, 48, 64
```

## Components

### AppShell

Provides the application header, product identity, guided/explore controls, and
reset action.

### DocumentWorkspace

Primary workflow view for document upload, document selection, query entry,
response rendering, and query history.

### AiResponseCard

Displays the answer and safety metadata:

- summary/answer
- citations
- retrieved evidence
- confidence
- evidence status
- safety decision
- refusal reason
- review requirement

### ClinicalDocumentViewer

Presents uploaded document context and evidence excerpts where needed.

### Shared UI

`ui.tsx` contains the reusable foundation:

- `Card`
- `PremiumCard`
- `Button`
- `Badge`
- `Alert`
- `EmptyState`
- `LoadingPulse`
- `StatusIndicator`
- `Grid`
- `Divider`

## Interaction Rules

- Buttons must have clear actions.
- Status color must support, not replace, readable labels.
- Loading states should use skeletons or inline progress language.
- Motion should be short and should reinforce state changes.
- The interface should remain usable with keyboard navigation.

## Removed Scope

The frontend no longer includes standalone risk dashboards, traceability
dashboards, chart-heavy command centers, interactive diagram tooling, or
theme-switching controls. Those concepts remain represented in architecture and
safety documentation where appropriate.
