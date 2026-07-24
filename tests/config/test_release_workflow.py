from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_container_release_uses_fresh_repository_package_name() -> None:
    workflow = (ROOT / ".github/workflows/cd.yml").read_text(encoding="utf-8")

    assert "IMAGE=ghcr.io/${OWNER_LOWER}/clinical-insights-ai-service" in workflow
