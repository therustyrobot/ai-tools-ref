---
phase: 02-live-data-pipeline-no-ai
plan: 02
subsystem: html-generator
tags: [python, html-generation, jinja-free, tailwind, pytest]
dependency_graph:
  requires: [02-01]
  provides: [scripts/generate.py, docs/index.html]
  affects: [docs/index.html, GitHub Pages output]
tech_stack:
  added: [html (stdlib), re (stdlib), collections.defaultdict]
  patterns: [f-string HTML generation, language-slug mapping, barcode cycle pattern]
key_files:
  created:
    - scripts/generate.py
    - tests/test_generate.py
    - tests/fixtures/sample_repos.json
  modified:
    - docs/index.html
decisions:
  - "Grouped by language (not categories) since no categories.json present — group_by_categories() available for future AI categorization phase"
  - "render_sections() is public API (wraps render_section per group) — needed by tests"
  - "marquee content dynamically built from nav_html span extraction — avoids duplicate data"
  - "BARCODE_STYLES cycled by global_index so patterns vary across all cards, not just within each section"
metrics:
  duration: ~8 minutes
  completed: 2026-04-22T18:29:05Z
  tasks_completed: 5
  files_changed: 4
---

# Phase 02 Plan 02: HTML Generator (generate.py) Summary

**One-liner:** Pure-Python HTML generator that reads repos.json, groups by language with star-sorted sections, and writes a fully-styled docs/index.html preserving Phase 1's visual identity.

## Objective

Create `scripts/generate.py` to close the data pipeline: `fetch_stars.py` → `_data/repos.json` → `generate.py` → `docs/index.html` → GitHub Pages. Replace Phase 1's hardcoded static HTML with a live-generated page.

## What Was Built

### scripts/generate.py (12 public functions)

| Function | Purpose |
|----------|---------|
| `fmt_stars(n)` | Human-readable star count (1200→"1.2K", 1.5M→"1.5M") |
| `language_to_slug(lang)` | GitHub language → URL-safe slug (C++→cpp, C#→csharp) |
| `lang_badge_html(language)` | Colored `<span>` language badge matching Phase 1 pattern |
| `load_repos(path)` | Load repos.json with json.load |
| `load_categories(path)` | Load optional categories.json (returns {} if absent) |
| `group_by_language(repos)` | Group by language, sorted by total stars desc |
| `group_by_categories(repos, cat_map)` | Group by AI category map (future use) |
| `render_card(repo, index, global_index)` | Single repo card HTML with HTML-escaped content |
| `render_section(cat_name, repos, cat_num, global_offset)` | Full category section with header + cards |
| `render_sections(groups)` | All sections (public API for tests) |
| `render_nav(groups)` | Sidebar nav anchor links with count badges |
| `render_page(nav_html, sections_html, total, generated_at)` | Complete page with identical Phase 1 head block |

### Key Design Choices

- **Zero templating dependencies** — pure Python f-strings, no Jinja2/Mako
- **f-string safety** — all CSS `{...}` blocks use `{{` `}}` escaping; only dynamic values use single braces
- **XSS protection** — `html.escape()` applied to `description`, `name`, and `owner` in `render_card()` before interpolation (T-02-02)
- **Sidebar replaces filter buttons** — `<aside>` with sticky nav (HTML-09 compliant) replaces Phase 1's JS-driven filter panel

### docs/index.html (regenerated)

Generated from 5-repo fixture (4 language groups: C, TypeScript, Go, Python):
- 4 `data-category=` sections with emoji headers + TOTAL_ENTRIES counts
- 5 repo cards with FILE: #NNN numbering
- Sticky sidebar nav with 4 anchor links
- Dynamic marquee from actual language names
- Phase 1 CDN URLs and Tailwind config preserved identically

## Test Results

```
tests/test_generate.py::TestFmtStars::test_fmt_stars PASSED
tests/test_generate.py::TestLanguageToSlug::test_language_to_slug PASSED
tests/test_generate.py::TestGroupByLanguage::test_group_by_language_sort_order PASSED
tests/test_generate.py::TestGroupByLanguage::test_group_ordering_by_total_stars PASSED
tests/test_generate.py::TestRenderNav::test_render_nav_contains_slug PASSED
tests/test_generate.py::TestRenderSection::test_render_section_header PASSED
tests/test_generate.py::TestHtmlEscape::test_html_escape_in_card PASSED
tests/test_generate.py::TestOutputFileCreated::test_output_file_created PASSED

14 passed (6 fetch + 8 generate), 0 failed
```

## Pipeline Verification

| Check | Result |
|-------|--------|
| All 12 functions importable | ✅ OK |
| `data-category=` sections in output | ✅ 4 sections |
| `file-num` cards in output | ✅ 5 repo cards |
| CDN tailwindcss.com preserved | ✅ Identical to Phase 1 |
| `&amp;` HTML-escaped in output | ✅ Present (neovim description) |
| `href="#` sidebar nav items | ✅ 4 items |
| `_data/` gitignored | ✅ Not in git status |
| feat(02-02) commit present | ✅ `6354e3f` |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all content is dynamically generated from repos.json input data.

## Next Steps

- **Phase 02-03** (if planned): Wire GitHub Actions to run fetch → generate pipeline daily
- **Phase 03** (AI categorization): Populate `_data/categories.json` via GitHub Models; `group_by_categories()` is already implemented and ready

## Self-Check: PASSED

- `scripts/generate.py` — ✅ exists, 12 functions, 220 lines
- `tests/test_generate.py` — ✅ exists, 8 tests, all passing
- `tests/fixtures/sample_repos.json` — ✅ exists, 5 repos
- `docs/index.html` — ✅ exists, regenerated from fixture
- Commit `6354e3f` — ✅ present in git log
