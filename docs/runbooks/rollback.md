# Rollback runbook

## Goal

Restore a previous known-good application image quickly when a release introduces regressions.

## Procedure

1. Identify the last known-good image tag or digest.
2. Update the deployment target to that image.
3. Verify the service health endpoint and key API paths.
4. Keep the failed image tagged for investigation.

## Useful commands

```bash
docker pull ghcr.io/<owner>/clinical-insights-ai-service:<tag>
docker run --rm -p 8000:8000 ghcr.io/<owner>/clinical-insights-ai-service:<tag>
```

## Operational note

Rollbacks should be driven by image versioning and environment promotion rather than manual code changes in production.
