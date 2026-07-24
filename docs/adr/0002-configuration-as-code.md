# ADR 0002: Configuration as Code

## Status

Accepted

## Context

Model names, retrieval settings, prompt templates, and logging defaults should
be visible without reading Python internals.

## Decision

Store non-secret defaults in top-level YAML files:

- `config/model_config.yaml`
- `config/retrieval_config.yaml`
- `config/prompt_templates.yaml`
- `config/logging_config.yaml`

Secrets and deployment-specific overrides remain environment variables loaded
through Pydantic settings.

## Consequences

The system is easier to review, safer to demo, and more agent-friendly. Runtime
settings still fail fast through typed validation.
