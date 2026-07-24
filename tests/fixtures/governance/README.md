# Governance Fixtures

This directory stores sample payloads for testing YAML governance rules.

Fixture cases should cover:

- blocking rules
- warning-only rules
- allowed payloads
- sensitive file names
- missing traceability
- large source text

These fixtures keep governance changes testable before they affect the
`/advisory/draft` advisory endpoint. The legacy `/agentic/draft` endpoint is
kept as a compatibility alias.
