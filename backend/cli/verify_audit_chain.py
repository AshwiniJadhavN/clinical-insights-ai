#!/usr/bin/env python3
"""Verify tamper-evident JSONL audit hash chains."""

from __future__ import annotations

import argparse
from pathlib import Path

from backend.audit.jsonl_writer import verify_hash_chain


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_file", nargs="?", default="data/agentic_audit.jsonl")
    args = parser.parse_args()

    ok, message = verify_hash_chain(Path(args.audit_file))
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
