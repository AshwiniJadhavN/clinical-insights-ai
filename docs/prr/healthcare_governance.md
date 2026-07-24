# Healthcare Governance and Data Handling Notes

Date: 2026-07-08

This project is a demonstration repository and not a clinical decision system.

## Intended Usage Assumptions

- Uploaded documents are used for technical demonstration and engineering evaluation.
- Outputs are advisory and require human judgment.
- Safety/refusal controls reduce risk but do not establish clinical efficacy.

## Current Handling of Uploaded Clinical Documents

As implemented today:
- Files are validated by extension and size before processing.
- Files are stored on disk under configured upload directory.
- Text is parsed and chunked for retrieval.
- Logging attempts to avoid raw PHI in operational logs.

## PHI/PII Considerations

Current safeguards:
- SQL query audit stores text lengths, not raw question/answer text.
- PHI scrubbing is applied to log/error text patterns.

Current limitations:
- Uploaded source files can still contain PHI/PII at rest.
- Extension-based validation is not equivalent to full DLP/de-identification.
- No complete de-identification pipeline is implemented.
- No formal key management, encryption-at-rest policy enforcement, or retention governance workflow is fully defined in code.

## Governance Positioning

Do not position this repository as HIPAA-compliant-by-default clinical infrastructure.

Position it as:
- an engineering demonstration of safety controls, traceability patterns, and production-readiness practices
- a baseline that still requires organizational security, privacy, and regulatory controls before real-world clinical use

## Recommended Next Steps (Documentation/Process)

1. Define explicit data classification and retention policy for uploads and audit trails.
2. Document approved deployment profiles (demo vs regulated environments).
3. Add PHI handling checklist to release process.
4. Add explicit "no real patient data" guidance for default local/demo workflows.
