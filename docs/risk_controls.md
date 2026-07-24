# Risk Controls

This project is a demonstration repository only. It is not a medical device and must not be used for clinical decision-making.

## Safety Controls

- Medical disclaimer is included in the README and API responses.
- Query input is screened by guardrails before retrieval or generation.
- Answers are generated only from retrieved context.
- The LLM is not called when retrieved evidence is missing or below the configured threshold.
- Citations are returned with generated answers.
- The top retrieved text is exposed as `retrieved_chunk` for visual evidence review.
- Confidence scoring communicates retrieval strength.
- `evidence_status` communicates whether evidence is `sufficient`, `weak`, or `missing`.

## Security Controls

- No hardcoded API keys.
- Environment variables are loaded through `pydantic-settings`.
- Uploads are validated before parsing.
- Logs avoid raw clinical text.
- CI builds the Docker image and runs Trivy vulnerability scanning.

## Advisory Automation Controls

- Advisory automation is draft-only.
- YAML governance rules run before draft automation.
- Sensitive files such as `.pem`, `.key`, and `.env` are blocked.
- Large source payloads produce non-blocking warnings.
- Traceability requires source context and an `audit_id` reference.
- AI findings require exact evidence references.
- Missing evidence returns `INSUFFICIENT_EVIDENCE`.
- Invalid structured output returns `INVALID_OUTPUT`.
- Human review is required before applying generated code, tests, fixes, pipeline changes, or documentation changes.
- Production deploy, merge, delete, and destructive operations are prohibited.
- Audit records are written to `data/agentic_audit.jsonl`.

## Known Demo Limitations

- This is not HIPAA-certified infrastructure.
- The default Docker Compose setup uses local PostgreSQL storage.
- Human clinical review is always required for any real-world medical workflow.
