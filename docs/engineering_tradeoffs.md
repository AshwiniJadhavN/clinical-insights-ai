# Engineering Tradeoffs

This document records deliberate tradeoffs in the repository so readers can distinguish intentional scope choices from accidental omissions.

## Deterministic Evaluation vs Runtime Realism

- Retrieval and refusal evaluations are deterministic and local by design.
- This improves repeatability in CI and local development.
- It does not fully reproduce production vector search, provider latency, or model behavior.

## Conservative Refusal vs Higher Answer Rate

- The query path prefers refusal or insufficient-evidence responses over unsupported answers.
- This reduces apparent answer coverage in ambiguous cases.
- The tradeoff is intentional: stronger evidence discipline over broader answer volume.

## Local Developer Simplicity vs Production Parity

- The default runtime configuration supports local SQLite-based development and mock LLM mode.
- Docker Compose provides a PostgreSQL-backed path for more realistic integration behavior.
- The repository does not attempt to force full production parity for every local workflow.

## Advisory AI Automation vs Autonomous Approval

- The testing AI module generates scenarios, failure analysis, and test drafts.
- All outputs require human review.
- This avoids the governance risk of automated approval while still demonstrating AI-assisted engineering workflows.

## Coverage Gate Practicality vs Maximal Thresholds

- The CI coverage gate enforces a pragmatic minimum threshold while separate checks focus on safety-critical paths.
- This keeps the repository maintainable as a demonstration system.
- The tradeoff is that overall percentage alone should not be interpreted as the full quality bar.

## Documentation Breadth vs Maintenance Cost

- The repository includes ADRs, runbooks, safety documents, and architecture views to make engineering decisions reviewable.
- More documents improve traceability but increase drift risk.
- The preferred mitigation is to keep README concise and use focused supporting documents for deeper topics.