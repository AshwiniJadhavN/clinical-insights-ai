#!/usr/bin/env python3
"""Simple API latency benchmark for portfolio-style evidence.

Example:
    python scripts/benchmark_api.py --url http://localhost:8000/health --requests 100 --warmup 10
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class Sample:
    latency_ms: float
    status_code: int | None
    error: str | None = None


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    index = (len(sorted_values) - 1) * (p / 100)
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def run_request(url: str, timeout: float) -> Sample:
    req = request.Request(url=url, method="GET")
    start = time.perf_counter()
    try:
        with request.urlopen(req, timeout=timeout) as response:
            latency_ms = (time.perf_counter() - start) * 1000
            return Sample(latency_ms=latency_ms, status_code=response.getcode())
    except error.HTTPError as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        return Sample(latency_ms=latency_ms, status_code=exc.code, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        latency_ms = (time.perf_counter() - start) * 1000
        return Sample(latency_ms=latency_ms, status_code=None, error=str(exc))


def summarize(samples: list[Sample]) -> dict[str, Any]:
    latencies = sorted(sample.latency_ms for sample in samples)
    failures = sum(1 for sample in samples if sample.error is not None)
    success = len(samples) - failures

    return {
        "total_requests": len(samples),
        "successful_requests": success,
        "failed_requests": failures,
        "error_rate_percent": round((failures / len(samples)) * 100, 2) if samples else 0.0,
        "latency_ms": {
            "min": round(min(latencies), 2) if latencies else 0.0,
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0.0,
            "median": round(statistics.median(latencies), 2) if latencies else 0.0,
            "p95": round(percentile(latencies, 95), 2) if latencies else 0.0,
            "p99": round(percentile(latencies, 99), 2) if latencies else 0.0,
            "max": round(max(latencies), 2) if latencies else 0.0,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple latency benchmark against one API endpoint.")
    parser.add_argument("--url", default="http://localhost:8000/health", help="Target URL to benchmark.")
    parser.add_argument("--requests", type=int, default=100, help="Number of benchmark requests to run.")
    parser.add_argument("--warmup", type=int, default=10, help="Warm-up requests before measurement.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-request timeout in seconds.")
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Write a timestamped JSON report to --output-dir.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/performance",
        help="Directory used when --save-json is enabled.",
    )
    parser.add_argument(
        "--output-prefix",
        default="benchmark",
        help="Filename prefix used when --save-json is enabled.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.requests <= 0:
        print("--requests must be greater than 0", file=sys.stderr)
        return 2

    if args.warmup < 0:
        print("--warmup must be 0 or greater", file=sys.stderr)
        return 2

    print(f"Benchmark target: {args.url}")
    print(f"Warmup requests: {args.warmup}")
    print(f"Measured requests: {args.requests}")

    for _ in range(args.warmup):
        run_request(url=args.url, timeout=args.timeout)

    samples = [run_request(url=args.url, timeout=args.timeout) for _ in range(args.requests)]
    result = summarize(samples)
    generated_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result["target_url"] = args.url
    result["generated_at_utc"] = generated_at_utc

    print("\nSummary")
    print(f"  Successful: {result['successful_requests']}/{result['total_requests']}")
    print(f"  Error rate: {result['error_rate_percent']}%")
    print("  Latency (ms):")
    print(f"    min={result['latency_ms']['min']}")
    print(f"    mean={result['latency_ms']['mean']}")
    print(f"    median={result['latency_ms']['median']}")
    print(f"    p95={result['latency_ms']['p95']}")
    print(f"    p99={result['latency_ms']['p99']}")
    print(f"    max={result['latency_ms']['max']}")

    print("\nJSON")
    print(json.dumps(result, indent=2))

    if args.save_json:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        output_path = output_dir / f"{args.output_prefix}_{timestamp}.json"
        output_path.write_text(f"{json.dumps(result, indent=2)}\n", encoding="utf-8")
        print(f"\nSaved JSON report: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
