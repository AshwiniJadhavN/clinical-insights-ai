# Systems Safety Docs

This folder groups the systems-engineering and safety-engineering artifacts added to the project.

## Contents

- [safety_architecture.md](safety_architecture.md): Safety-layer structure, rationale, and PNG architecture diagrams.
- [hazard_analysis.md](hazard_analysis.md): Foreseeable hazards, controls, residual risks, and verification links.
- [safety_requirements.md](safety_requirements.md): Safety requirements mapped to rationale, implementation, and tests.
- [traceability_matrix.md](traceability_matrix.md): Hazard to requirement to implementation to test traceability.
- [verification_strategy.md](verification_strategy.md): Verification objectives and test strategy.
- [failure_modes.md](failure_modes.md): Failure detection, fail-safe behavior, and recovery view.
- [hazards.md](hazards.md): Lightweight entry point to the main hazard analysis.

## Why this folder exists

- Keeps design-control artifacts separate from general product docs.
- Makes safety evidence easier to review during architecture and CI gates.
- Improves maintainability by giving safety and traceability artifacts a stable location.
