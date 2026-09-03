# API Status Checker

A small, dependency-free Python CLI for checking website and API health.

It checks multiple targets in parallel and reports HTTP status, response time, failures, and an optional JSON report. It can also exit with a non-zero status when a target is down, which makes it useful in simple CI or automation workflows.

## Features

- No third-party packages
- Parallel URL checks
- HTTP status and latency reporting
- URL list files
- JSON report output
- CI-friendly `--fail-on-down` exit code
- Automatic `https://` prefix when a scheme is omitted

## Requirements

- Python 3.10+

## Usage

Check one or more URLs:

```bash
python api_status_checker.py https://api.github.com example.com
```

Check URLs from a file:

```bash
python api_status_checker.py --file urls.example.txt
```

Save a JSON report:

```bash
python api_status_checker.py example.com --json report.json
```

Fail the command when any target is down:

```bash
python api_status_checker.py example.com --fail-on-down
```

Adjust timeout and parallel workers:

```bash
python api_status_checker.py --file urls.example.txt --timeout 5 --workers 4
```

## Example output

```text
API STATUS CHECKER
========================================================================
[UP  ] 200    184.22 ms  https://api.github.com
[UP  ] 200    102.18 ms  https://example.com
------------------------------------------------------------------------
Total: 2 | Up: 2 | Down: 0
Average response time (UP targets): 143.20 ms
```

## Why this project exists

This project is intentionally small. The goal is to provide a useful command-line tool while practicing practical Python concepts: HTTP requests, error handling, concurrency, CLI arguments, JSON, files, and exit codes.

## License

MIT
