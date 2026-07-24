from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_example_environment_has_one_assignment_per_line() -> None:
    assignments = {}
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            key, separator, value = line.partition("=")
            assert separator, f"Invalid environment assignment: {line}"
            assignments[key] = value

    assert assignments["DATABASE_URL"].endswith("/clinical_insights")
    assert assignments["MOCK_LLM"] == "true"


def test_rag_dependencies_are_exactly_pinned() -> None:
    dependencies = (ROOT / "requirements-rag.txt").read_text(encoding="utf-8").splitlines()

    for dependency in dependencies:
        if not dependency or dependency.startswith(("#", "-r ")):
            continue
        assert "==" in dependency, f"Dependency must be exactly pinned: {dependency}"
