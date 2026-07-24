# Security Policy

## Supported Versions

Security fixes are applied to the latest repository state on the main branch.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately by opening a GitHub security advisory or contacting the repository maintainer directly.

Do not open public issues for security-sensitive findings.

## Security Expectations

- Secrets must never be committed to the repository.
- Container images and dependencies are scanned in CI.
- Production deployments should use environment-specific secrets and least-privilege access.
