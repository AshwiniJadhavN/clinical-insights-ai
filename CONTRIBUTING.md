# Contributing

## Development workflow

1. Create a feature branch from main.
2. Run the local checks before opening a pull request.
3. Keep changes focused and well-documented.

## Local validation

```bash
make lint
make test
make smoke-test
```

## Type checking

The codebase uses Pyright (strict static analysis) to catch type errors early:

```bash
# Run type checker locally (requires .venv311 or equivalent)
pyright backend/

# Or via venv
python -m pip install pyright==1.1.390
pyright backend/
```

Type checking is required in CI and must pass before PR approval.

## Pull request expectations

- Include a concise summary of the change and its rationale.
- Ensure CI passes (lint, tests, type checks) before requesting review.
- Prefer small, reviewable changes.
- Add or update tests for any behavior changes.
- Maintain 70%+ test coverage on core business logic.
