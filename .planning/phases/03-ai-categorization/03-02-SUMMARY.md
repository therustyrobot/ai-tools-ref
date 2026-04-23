---
phase: 03-ai-categorization
plan: "02"
subsystem: generate
tags: [html-generation, hierarchical, category-meta, material-icons, safety-orange, security]
dependency_graph:
  requires: ["03-01"]
  provides: ["hierarchical-html-output", "category-rendering"]
  affects: ["docs/index.html", "scripts/generate.py"]
tech_stack:
  added: []
  patterns:
    - "CATEGORY_META 2-tuple dict for Material Icons category rendering"
    - "Hierarchical nested grouping (cat → subcat → repos)"
    - "Safety Orange (#FF5F1F) subcategory divider headers"
    - "3-way icon lookup: CATEGORY_META → LANG_META → emoji fallback"
    - "JSONDecodeError fallback in load_categories() for graceful degradation"
key_files:
  modified:
    - scripts/generate.py
    - tests/test_generate.py
decisions:
  - "Used plan-canonical CATEGORY_META slugs (dev-tools-cli, devops-infra, etc.) matching 03-PATTERNS.md and test expectations"
  - "Added JSONDecodeError guard to load_categories() for T-03-03 threat mitigation"
  - "render_section() updated to check CATEGORY_META first ensuring category icons override language emojis"
metrics:
  duration: "~4 minutes"
  completed: "2026-04-23"
  tasks_completed: 2
  files_modified: 2
---

# Phase 03 Plan 02: Generate.py Hierarchical Upgrade Summary

**One-liner:** Hierarchical HTML generation with Safety Orange subcategory dividers, Material Icons category nav, and graceful fallback to language grouping when categories.json absent.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add hierarchical functions to generate.py | `58ee1c8` | scripts/generate.py |
| 2 | Add hierarchical test classes to test_generate.py | `78c7c59` | tests/test_generate.py |

## What Was Built

### scripts/generate.py additions:
- **`CATEGORY_META`** — 14-entry dict mapping slugs to `(display_name, icon_name)` 2-tuples for Material Icons rendering
- **`load_categories()` T-03-03 fix** — now catches `json.JSONDecodeError` and returns `{}` so generate.py gracefully falls back to language grouping on malformed JSON
- **`render_section()` update** — 3-way CATEGORY_META → LANG_META → fallback lookup; known categories render `<span class="material-icons">` instead of emoji
- **`group_by_categories_hierarchical(repos, cat_map)`** — groups into `{category: {subcategory: [repos]}}`, repos sorted by stars, categories sorted by total stars, missing repos fall to `Other > Other`
- **`render_subcategory_header(subcat_name, count, subcat_num)`** — Safety Orange `bg-[#FF5F1F]` divider with `data-subcategory` attribute and ENTRIES count; applies `html.escape()` (T-03-02)
- **`render_sections_hierarchical(hier_groups)`** — full section HTML with gray category headers + orange subcategory dividers
- **`render_nav_hierarchical(hier_groups)`** — top-level-only nav with summed repo counts and Material Icons; `html.escape()` on display names (T-03-02)
- **`__main__` update** — `if cat_map:` branch uses hierarchical path; else falls back to language grouping (D-04)

### tests/test_generate.py additions:
- `CATEGORIES_FIXTURE_PATH` constant
- `TestCategoryMetaLookup` — validates 14 slugs, 2-tuple values, ai-ml entry
- `TestGroupByCategoriesHierarchical` — nesting structure, Other fallback, star sort order
- `TestRenderSubcategoryHeader` — Safety Orange color, ENTRIES count, data-subcategory slug, XSS escape
- `TestRenderNavHierarchical` — top-level anchors only (no subcategory hrefs), summed counts, material-icons span
- `TestOutputFileHierarchical` — integration test using sample_categories.json fixture

## Test Results

```
45 passed, 1 warning in 0.05s
```

- 8 original tests: ✅ all pass
- 14 new test methods across 5 new classes: ✅ all pass
- Full suite (test_generate.py + test_categorize.py + test_fetch.py): ✅ 45 passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added JSONDecodeError guard to load_categories()**
- **Found during:** Task 1
- **Issue:** T-03-03 threat in plan's threat model requires `load_categories()` to return `{}` on malformed JSON, but the existing implementation only guarded against file absence
- **Fix:** Added `try/except json.JSONDecodeError: return {}` around `json.load(f)`
- **Files modified:** scripts/generate.py
- **Commit:** 58ee1c8

None other — plan executed as written.

## Known Stubs

None — all functions are fully wired with real data from categories.json.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced beyond what the plan's threat model already covers (T-03-02, T-03-03).

## Self-Check: PASSED

- [x] `scripts/generate.py` modified — FOUND
- [x] `tests/test_generate.py` modified — FOUND
- [x] Commit `58ee1c8` exists — FOUND
- [x] Commit `78c7c59` exists — FOUND
- [x] `python3 -m pytest tests/ -x -q` → 45 passed
