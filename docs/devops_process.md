# DevOps Process

The project includes local and CI checks for the API, safety logic, container build, and runtime health.

## CI/CD Gates

GitHub Actions runs on push and pull request. The pipeline is split into specialized DevOps gates:

- Code Review Gate: runs Ruff lint checks
- Test Gate: runs pytest
- Coverage Gate: enforces backend test coverage at 78%
- Architecture Gate: validates required safety and deployment structure
- Secret Scan Gate: checks for leaked credentials
- Dependency Security Gate: scans Python dependencies and publishes an audit report
- API Contract Gate: validates health and OpenAPI contracts
- Governance Check Gate: validates YAML governance rules through the local CLI
- Compose Integration Gate: validates Compose and database health
- Build Gate: builds the Docker image
- Security Gate: scans the image with Trivy
- Compose and Script Check: validates Docker Compose and local scripts
- CI Summary: assembles gate reports into a final CI artifact

The checks are deterministic CI jobs. This keeps the build and test path repeatable.

## Build Automation

Local scripts mirror the CI workflow:

- `scripts/run_local.sh` starts the API locally
- `scripts/test.sh` runs linting and tests
- `scripts/build_image.sh` builds the Docker image
- `scripts/deploy_local.sh` starts the Docker Compose deployment

The `Makefile` exposes the same common operations:

- `make lint`
- `make test`
- `make build`
- `make deploy-local`
- `make ci-local`

## Operational Readiness

The API exposes `/health` for service checks. Docker and Docker Compose both use this endpoint to report container health.
The API also exposes `/metrics` and returns `X-Request-ID` on responses for traceability.
The API exposes `/governance/rules` so loaded governance rules can be inspected at runtime.
