# AGENTS.md

## Project
- Purpose: Dependency-free Python CLI that checks website and API health, latency, and failures.
- Primary language: Python.
- Important frameworks: Python standard library only.

## Repository Structure
- `api_status_checker.py` — complete application source code.
- `README.md` — usage and project documentation.
- `urls.example.txt` — example URL input file.

## Development Commands
- Run: `python api_status_checker.py example.com`
- Test syntax: `python -m py_compile api_status_checker.py`
- Help: `python api_status_checker.py --help`

## Engineering Rules
- Follow the existing code style before introducing new patterns.
- Make the smallest change needed for the task.
- Do not modify unrelated files.
- Keep the project dependency-free unless a dependency is clearly justified.
- Never commit secrets, tokens, or private endpoint credentials.
