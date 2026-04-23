---
phase: 03-ai-categorization
plan: "01"
subsystem: categorize
tags: [ai-categorization, github-models, batch-processing, tdd, python]
dependency_graph:
  requires: [scripts/fetch_stars.py, _data/repos.json]
  provides: [scripts/categorize.py, _data/categories.json]
  affects: [scripts/generate.py, tests/test_categorize.py]
tech_stack:
  added: [requests (already installed), json, re, os - all stdlib/pre-installed]
  patterns:
    - Bearer auth header for GitHub Models API (not "token " prefix)
    - Batch processing loop (range(0, len, BATCH_SIZE))
    - JSON parse + retry + Other fallback on double failure
    - importlib.util.spec_from_file_location test bootstrap
    - MagicMock session.post with side_effect for multi-response mocking
key_files:
  created:
    - scripts/categorize.py
    - tests/test_categorize.py
    - tests/fixtures/sample_categories.json
  modified: []
decisions:
  - key: slug-derivation-in-python
    choice: "Python always derives slug from canonical category name via category_to_slug(); model output slug field ignored"
    rationale: "AI-05 requirement; prevents category drift across runs; model output is untrusted"
  - key: bearer-not-token-prefix
    choice: "Authorization: Bearer $GITHUB_TOKEN (not 'token ' prefix)"
    rationale: "GitHub Models API requires Bearer format; REST API uses 'token ' - different endpoints"
  - key: batch-size-10
    choice: "BATCH_SIZE = 10 per API call"
    rationale: "D-03 locked; stays within 150 req/day free tier for ~370 repos (≤37 calls)"
metrics:
  duration: "2m 24s"
  completed_date: "2026-04-23"
  tasks_completed: 2
  tasks_total: 2
  files_created: 3
  files_modified: 0
  tests_added: 17
  tests_total_after: 31
---

# Phase 3 Plan 1: Categorize Pipeline + Unit Tests Summary

**One-liner:** AI batch categorization pipeline using GitHub Models API (gpt-4o-mini) with JWT-style Bearer auth, 10-repo batching, JSON-mode response parsing with retry, and Python-side slug derivation.

## What Was Built

### scripts/categorize.py (164 lines)

Eight public functions implementing the full AI categorization pipeline:

| Function | Purpose |
|----------|---------|
| `category_to_slug(name)` | Derives URL-safe slug from canonical category name (identical logic to `language_to_slug`) |
| `build_session(token)` | Creates `requests.Session` with `Authorization: Bearer` header (GitHub Models requires Bearer, not `token `) |
| `call_model(session, messages)` | POSTs to `https://models.github.ai/inference/chat/completions` with `response_format: json_object`; raises before `.json()` |
| `strip_fences(raw)` | Strips ` ```json ... ``` ` markdown wrapping from API responses |
| `build_messages(batch)` | Constructs `[system, user]` message array embedding full taxonomy from `starred_repos.md` |
| `parse_with_retry(session, messages, batch_names)` | Calls model; on `JSONDecodeError` logs `[WARN]` and retries once; on 2nd failure logs `[ERROR]` and assigns batch to "Other" |
| `categorize_all(repos, session)` | Main pipeline: slices repos into batches of `BATCH_SIZE=10`, calls model per batch, derives slug in Python (never from model output) |
| `write_categories(cat_map, path)` | Creates `_data/` directory, writes `categories.json` with `ensure_ascii=False` |

**Security (T-03-01):** `GITHUB_TOKEN` only appears as `os.environ["GITHUB_TOKEN"]` in `__main__`. The value is passed to `build_session()` which injects it into the `Authorization` header. The token string never flows to any `print()` or log call.

### tests/test_categorize.py (181 lines)

Six test classes, 17 tests total — zero live API calls:

| Class | Tests |
|-------|-------|
| `TestCategoryToSlug` | 3 — known slugs (AI & ML→ai-ml, etc.), empty→other, None→other |
| `TestStripFences` | 3 — no fences unchanged; ` ```json ``` ` stripped; bare ` ``` ``` ` stripped |
| `TestCallModel` | 4 — content string returned; `raise_for_status` called once; correct URL; `response_format` in payload |
| `TestParseWithRetry` | 3 — success on first; `[WARN]`+retry on JSONDecodeError; Other fallback on 2nd fail |
| `TestCategorizeAll` | 3 — 25 repos → 3 calls (10+10+5); slug from Python not model ("WRONG" ignored); missing repo no crash |
| `TestWriteCategories` | 1 — creates `_data/` dir; writes valid parseable JSON |

### tests/fixtures/sample_categories.json

Fixture containing all 5 repos from `sample_repos.json` assigned to `Dev Tools & CLI` subcategories. Required by Plan 03-02's `TestOutputFileHierarchical` integration test.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED | `3a0478e` — `test(03-01): add failing test for categorize.py` | ✅ Tests failed with FileNotFoundError |
| GREEN | `9820a28` — `feat(03-01): implement categorize.py AI batch categorization pipeline` | ✅ Minimal tests passed |
| FULL | `2ab2c5b` — `feat(03-01): full test suite for categorize.py + sample_categories.json fixture` | ✅ 17/17 tests passed |

## Verification Results

```
python3 -m pytest tests/ -v
31 passed, 1 warning in 0.04s
```

- New tests: 17 (test_categorize.py)
- Existing tests: 14 (test_fetch.py: 6, test_generate.py: 8) — all still green

## Deviations from Plan

None - plan executed exactly as written.

The plan described a two-task TDD flow where Task 1 creates the implementation and Task 2 creates the comprehensive tests. This was executed as: RED stub test → GREEN implementation → full test expansion, which satisfies both the TDD gate requirement and the task ordering in the plan.

## Known Stubs

None. All 8 functions are fully implemented with real logic. The fixture `sample_categories.json` uses real category assignments (not placeholder data).

## Threat Flags

No new security surfaces beyond those documented in the plan's threat model. The three tracked threats (T-03-01 through T-03-03) are addressed:
- T-03-01: Token never printed — verified by grep check
- T-03-02: HTML escaping deferred to generate.py render functions (Wave 2, per plan)
- T-03-03: JSONDecodeError fallback implemented in `parse_with_retry()`

## Self-Check: PASSED

Files exist:
- ✅ `scripts/categorize.py`
- ✅ `tests/test_categorize.py`
- ✅ `tests/fixtures/sample_categories.json`

Commits exist:
- ✅ `3a0478e` — test RED
- ✅ `9820a28` — feat GREEN
- ✅ `2ab2c5b` — feat full suite + fixture
