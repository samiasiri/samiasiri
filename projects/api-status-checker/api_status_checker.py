#!/usr/bin/env python3
"""A small dependency-free CLI for checking website and API health."""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT = 10.0
DEFAULT_WORKERS = 8


@dataclass
class CheckResult:
    url: str
    status: str
    status_code: int | None
    response_time_ms: float | None
    error: str | None = None


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("URL cannot be empty")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value


def load_urls(direct_urls: Iterable[str], file_path: str | None) -> list[str]:
    urls: list[str] = []

    for value in direct_urls:
        urls.append(normalize_url(value))

    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"URL file not found: {path}")

        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(normalize_url(line))

    # Keep order while removing duplicates.
    return list(dict.fromkeys(urls))


def check_url(url: str, timeout: float) -> CheckResult:
    started = time.perf_counter()
    request = Request(
        url,
        method="GET",
        headers={"User-Agent": "api-status-checker/1.0"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            elapsed = round((time.perf_counter() - started) * 1000, 2)
            code = response.getcode()
            status = "UP" if 200 <= code < 400 else "DOWN"
            return CheckResult(url, status, code, elapsed)

    except HTTPError as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        return CheckResult(url, "DOWN", exc.code, elapsed, f"HTTP {exc.code}")

    except URLError as exc:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        reason = getattr(exc, "reason", exc)
        return CheckResult(url, "DOWN", None, elapsed, str(reason))

    except TimeoutError:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        return CheckResult(url, "DOWN", None, elapsed, "Request timed out")

    except Exception as exc:  # Keep one bad target from stopping the whole run.
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        return CheckResult(url, "DOWN", None, elapsed, str(exc))


def run_checks(urls: list[str], timeout: float, workers: int) -> list[CheckResult]:
    results_by_url: dict[str, CheckResult] = {}

    with ThreadPoolExecutor(max_workers=min(workers, len(urls))) as pool:
        futures = {pool.submit(check_url, url, timeout): url for url in urls}
        for future in as_completed(futures):
            result = future.result()
            results_by_url[result.url] = result

    return [results_by_url[url] for url in urls]


def print_results(results: list[CheckResult]) -> None:
    print("\nAPI STATUS CHECKER")
    print("=" * 72)

    for result in results:
        code = str(result.status_code) if result.status_code is not None else "---"
        latency = (
            f"{result.response_time_ms:.2f} ms"
            if result.response_time_ms is not None
            else "n/a"
        )
        print(f"[{result.status:<4}] {code:<3}  {latency:>11}  {result.url}")
        if result.error:
            print(f"       error: {result.error}")

    up = sum(result.status == "UP" for result in results)
    down = len(results) - up
    successful_times = [
        result.response_time_ms
        for result in results
        if result.status == "UP" and result.response_time_ms is not None
    ]

    print("-" * 72)
    print(f"Total: {len(results)} | Up: {up} | Down: {down}")
    if successful_times:
        average = sum(successful_times) / len(successful_times)
        print(f"Average response time (UP targets): {average:.2f} ms")


def save_json_report(path: str, results: list[CheckResult]) -> None:
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": len(results),
        "up": sum(result.status == "UP" for result in results),
        "down": sum(result.status == "DOWN" for result in results),
        "results": [asdict(result) for result in results],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check websites and APIs from the command line without extra packages."
    )
    parser.add_argument(
        "urls",
        nargs="*",
        help="URLs to check. Missing schemes default to https://.",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="Text file containing one URL per line. Lines starting with # are ignored.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout per request in seconds (default: {DEFAULT_TIMEOUT:g}).",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Maximum parallel checks (default: {DEFAULT_WORKERS}).",
    )
    parser.add_argument(
        "--json",
        metavar="PATH",
        help="Save a machine-readable JSON report to PATH.",
    )
    parser.add_argument(
        "--fail-on-down",
        action="store_true",
        help="Exit with status 1 when any target is down (useful in CI).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be greater than 0")
    if args.workers <= 0:
        parser.error("--workers must be greater than 0")

    try:
        urls = load_urls(args.urls, args.file)
    except (ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))

    if not urls:
        parser.error("provide at least one URL or use --file")

    results = run_checks(urls, args.timeout, args.workers)
    print_results(results)

    if args.json:
        save_json_report(args.json, results)
        print(f"JSON report saved to: {args.json}")

    if args.fail_on_down and any(result.status == "DOWN" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
