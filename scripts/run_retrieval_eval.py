#!/usr/bin/env python3
"""Run deterministic retrieval evaluation against sample documents."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.retrieval_eval import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
