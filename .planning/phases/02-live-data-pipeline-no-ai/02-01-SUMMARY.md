---
phase: 02-live-data-pipeline-no-ai
plan: "01"
subsystem: data-pipeline
tags: [python, github-api, pytest, pagination, data-fetch]
dependency_graph:
  requires: []
  provides: [scripts/fetch_stars.py, _data/repos.json (runtime)]
  affects: [02-02 generate script reads _data/repos.json]
tech_stack:
  added: [pytest, requests]
  patterns: [paginated API fetch, unittest.mock patching, TDD RED/GREEN]
key_files:
  created:
    - scripts/fetch_stars.py
    - tests/test_fetch.py
    - tests/conftest.py
    - tests/__init__.py
    - scripts/__init__.py
    - pytest.ini
  modified: []
decisions:
  - "raise_for_status() called before .json() to surface HTTP errors before parsing"
  - "os.environ['GITHUB_TOKEN'] (KeyError on missing) — no empty-string default, fail-fast security"
  - "conftest.py pre-imports requests to ensure sys.modules has real module before test bootstrapper runs"
metrics:
  duration: "~3m"
  completed: "2026-04-22"
  tasks_completed: 5
  files_created: 6
---

# Phase 02 Plan 01: Fetch Stars Script + Unit Tests Summary

**One-liner:** Paginated GitHub API star fetcher (fork/archived filter, JSON output) with 6 pytest unit tests using unittest.mock — no real HTTP calls.

## Objective

Create `scripts/fetch_stars.py` — a fully working GitHub API client that fetches all starred repos for the authenticated user, filters out forks and archived repos, and writes `_data/repos.json`. Paired with `tests/test_fetch.py` (no real HTTP) and `pytest.ini`.

## What Was Built

### `scripts/fetch_stars.py`
- `get_next_url(response)` — parses `Link: rel="next"` header via regex
- `fetch_all_stars(token)` — paginates GitHub API (`per_page=100`), follows `Link` headers until exhausted
- `filter_repos(repos)` — excludes repos where `fork=True` or `archived=True`
- `write_repos(repos, path)` — projects to 6 fields, writes JSON array to `_data/repos.json`
- Security: `raise_for_status()` before `.json()`, `os.environ["GITHUB_TOKEN"]` (KeyError on missing)

### `tests/test_fetch.py`
6 unit tests, all passing, zero real HTTP calls:
- `test_per_page_100` — verifies first request URL contains `per_page=100`
- `test_pagination` — mocks 2 pages (5 repos each), verifies all 10 collected
- `test_filter_forks` — verifies `fork=True` repo excluded, clean repo kept
- `test_filter_archived` — verifies `archived=True` repo excluded, active repo kept
- `test_no_fork_no_archived_kept` — verifies clean repo retained after filter
- `test_output_schema` — verifies written JSON has exactly the 6 required keys

### `pytest.ini`
```ini
[pytest]
testpaths = tests
```

## Key Decisions

1. **`raise_for_status()` before `.json()`** — Surfaces HTTP 4xx/5xx errors immediately rather than attempting to parse an error response body as JSON.
2. **`os.environ["GITHUB_TOKEN"]`** — Raises `KeyError` on missing token (fail-fast). No silent empty-auth requests possible.
3. **`tests/conftest.py` pre-imports `requests`** — Ensures `sys.modules["requests"]` is the real module before `_load_module()` in the test bootstrapper checks it. See deviations below.

## Artifacts Created

| File | Lines | Purpose |
|------|-------|---------|
| `scripts/fetch_stars.py` | 58 | Paginated GitHub API fetch script |
| `tests/test_fetch.py` | 144 | 6 unit tests (no real HTTP) |
| `tests/conftest.py` | 6 | Pre-imports requests for test bootstrapper ordering |
| `tests/__init__.py` | 0 | Python package marker |
| `scripts/__init__.py` | 0 | Python package marker |
| `pytest.ini` | 2 | pytest configuration |

## Test Results

```
tests/test_fetch.py::TestFetchAllStars::test_pagination PASSED
tests/test_fetch.py::TestFetchAllStars::test_per_page_100 PASSED
tests/test_fetch.py::TestFilterRepos::test_filter_archived PASSED
tests/test_fetch.py::TestFilterRepos::test_filter_forks PASSED
tests/test_fetch.py::TestFilterRepos::test_no_fork_no_archived_kept PASSED
tests/test_fetch.py::TestWriteRepos::test_output_schema PASSED
6 passed, 1 warning in 0.02s
```

(Warning: urllib3 v2 OpenSSL/LibreSSL version mismatch on macOS — not a test failure.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `patch("requests.get", ...)` failed with AttributeError on fake requests stub**

- **Found during:** Task 4 (GREEN phase)
- **Issue:** `_load_module()` in the test bootstrapper checks `if "requests" not in sys.modules` and injects a bare `types.ModuleType("requests")` stub when the condition is True. Since the test file has no top-level `import requests`, the condition was True even though `requests` is installed — so the fake stub landed in `sys.modules["requests"]`. `patch("requests.get", ...)` then failed with `AttributeError: <module 'requests'> does not have the attribute 'get'`.
- **Fix:** Created `tests/conftest.py` that pre-imports `requests`. pytest loads `conftest.py` before test module-level code runs, ensuring `sys.modules["requests"]` holds the real module when `_load_module()` checks it.
- **Files modified:** `tests/conftest.py` (new)
- **Commit:** `a35a2ee`

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | `2cd80c5` | ✅ test(02-01): failing tests committed |
| GREEN (feat) | `2f6a662` | ✅ feat(02-01): implementation makes tests pass |
| Fix (deviation) | `a35a2ee` | ✅ fix(02-01): conftest.py for test infrastructure |

## Next Steps

- **Plan 02-02:** `scripts/generate.py` reads `_data/repos.json` and generates `docs/index.html`
- **Live run:** Requires `GITHUB_TOKEN` in environment: `GITHUB_TOKEN=<token> python3 scripts/fetch_stars.py`
- `_data/` is gitignored — `_data/repos.json` is runtime-only, never committed

## Self-Check: PASSED

- [x] `scripts/fetch_stars.py` exists and is importable
- [x] `tests/test_fetch.py` exists with 6 tests
- [x] `pytest.ini` exists with `testpaths = tests`
- [x] `tests/conftest.py` exists
- [x] All 4 commits present in git log: `0c8d9e3`, `2cd80c5`, `2f6a662`, `a35a2ee`
- [x] 6/6 pytest tests PASS
- [x] No GITHUB_TOKEN value in any committed file
