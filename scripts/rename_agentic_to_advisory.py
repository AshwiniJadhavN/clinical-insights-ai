#!/usr/bin/env python3
"""
Safely rename agentic API language to advisory language.

Default mode is dry-run. Use --apply only after reviewing the planned file list.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDED_SUFFIXES = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".sh",
}
SKIP_PARTS = {".git", ".venv", ".venv311", "__pycache__", "data/chroma_db"}

REPLACEMENTS = [
    ("/agentic", "/advisory-draft"),
    ("Agentic", "Advisory"),
    ("AGENTIC", "ADVISORY"),
    ("agentic", "advisory"),
]


def _candidate(path: Path) -> bool:
    if path.suffix not in INCLUDED_SUFFIXES:
        return False
    return not any(part in SKIP_PARTS for part in path.parts)


def _replace(text: str) -> str:
    updated = text
    for old, new in REPLACEMENTS:
        updated = updated.replace(old, new)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to disk.")
    args = parser.parse_args()

    changed: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or not _candidate(path.relative_to(ROOT)):
            continue
        original = path.read_text(encoding="utf-8")
        updated = _replace(original)
        if updated == original:
            continue
        changed.append(path.relative_to(ROOT))
        if args.apply:
            path.write_text(updated, encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY RUN"
    print(f"{mode}: {len(changed)} files would change." if not args.apply else f"{mode}: {len(changed)} files changed.")
    for path in changed:
        print(f" - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
