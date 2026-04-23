---
phase: 03-ai-categorization
verified: 2026-04-23T10:00:00Z
status: human_needed
score: 13/15 must-haves verified (2 require live API run)
overrides_applied: 0
human_verification:
  - test: "Run `GITHUB_TOKEN=<token> python scripts/categorize.py` against real _data/repos.json"
    expected: "_data/categories.json created with every repo mapped; category names match starred_repos.md taxonomy (e.g. 'AI & ML', 'Self-Hosting & Homelab', 'Dev Tools & CLI'); no crash"
    why_human: "GitHub Models API requires a real GITHUB_TOKEN with models:read permission; cannot mock a live network call programmatically"
  - test: "Run full pipeline twice in a row: fetch → categorize → generate; diff the two docs/index.html files"
    expected: "Category names and anchor IDs are identical across both runs, confirming slug stability and taxonomy seeding prevents drift"
    why_human: "Taxonomy stability across consecutive live runs requires real API calls with real model responses — cannot be simulated deterministically in unit tests"
---

# Phase 3: AI Categorization — Verification Report

**Phase Goal:** GitHub Models intelligently groups all starred repos into the taxonomy from `starred_repos.md` — replacing language-buckets with meaningful AI & ML, Self-Hosting, Dev Tools, and other human-legible categories that remain stable across daily runs

**Verified:** 2026-04-23T10:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | categorize.py exists with all 8 functions: category_to_slug, build_session, call_model, strip_fences, parse_with_retry, build_messages, categorize_all, write_categories | ✓ VERIFIED | `grep "^def " scripts/categorize.py` returns all 8; file is 170 lines with substantive implementations |
| 2 | BATCH_SIZE = 10 (D-03) | ✓ VERIFIED | Line 10: `BATCH_SIZE = 10`; TestCategorizeAll::test_batch_count_25_repos confirms 3 API calls for 25 repos (10+10+5) |
| 3 | Bearer auth (NOT "token " prefix) — critical for GitHub Models API | ✓ VERIFIED | Line 72: `"Authorization": f"Bearer {token}"` — correct format for GitHub Models API |
| 4 | parse_with_retry: JSONDecodeError → [WARN] + retry → second failure → [ERROR] + Other fallback (no crash) | ✓ VERIFIED | Lines 116, 125: `[WARN]` on first failure, `[ERROR] … Assigning batch to Other` on second; TestParseWithRetry::test_fallback_to_other_on_two_failures passes |
| 5 | categorize_all: repos omitted from model response get Other/Other (WR-01) | ✓ VERIFIED | Lines 145–148: explicit `if name not in cat_map` guard with `[WARN]` log and Other fallback; TestCategorizeAll::test_missing_from_result_gets_other passes |
| 6 | Slugs derived by Python (category_to_slug()) — never from model output | ✓ VERIFIED | categorize_all() calls `category_to_slug(info.get("category", "Other"))` — model's slug field is ignored; TestCategorizeAll::test_slug_derived_from_category_not_model feeds `"slug": "WRONG"` and asserts `"ai-ml"` wins |
| 7 | GITHUB_TOKEN value is never printed or logged | ✓ VERIFIED | Token is read via `os.environ["GITHUB_TOKEN"]` and passed to `build_session()` only; no print/log of the token string anywhere in categorize.py |
| 8 | CATEGORY_META dict with exactly 14 entries as 2-tuples (display_name, icon_name) | ✓ VERIFIED | `len(CATEGORY_META)` = 14; TestCategoryMetaLookup::test_all_14_slugs_present and test_values_are_2_tuples both pass |
| 9 | group_by_categories_hierarchical(), render_subcategory_header(), render_sections_hierarchical(), render_nav_hierarchical() all exist in generate.py | ✓ VERIFIED | All 4 functions present; each substantive (not stubs) — group_by_categories_hierarchical is 25 lines, render_subcategory_header uses bg-[#FF5F1F], render_sections_hierarchical iterates subcats, render_nav_hierarchical uses CATEGORY_META |
| 10 | render_subcategory_header uses Safety Orange (#FF5F1F) | ✓ VERIFIED | Line 294: `bg-[#FF5F1F]`; TestRenderSubcategoryHeader::test_orange_background_class passes |
| 11 | render_section() checks CATEGORY_META first, then LANG_META, then fallback | ✓ VERIFIED | Lines 253–258: `if slug in CATEGORY_META: … else: LANG_META.get(slug, (cat_name, …))` — D-06 comment confirms intent |
| 12 | __main__ has if cat_map: branch → hierarchical path; else → language grouping fallback | ✓ VERIFIED | Lines 574–581: `if cat_map:` → hierarchical path; `else:` → `group_by_language` fallback; TestOutputFileCreated and TestOutputFileHierarchical both pass |
| 13 | html_url escaped before href insertion (IN-01) and marquee uses html.unescape() → .upper() → html.escape() (IN-02) | ✓ VERIFIED | Line 214: `safe_url = html.escape(repo["html_url"])`; Lines 419–422: `raw_name = html.unescape(…); marquee_parts.append(raw_name.upper()); … html.escape(marquee_text * 4)` |
| 14 | Running categorize.py calls GitHub Models API and produces _data/categories.json | ? HUMAN NEEDED | Code correct and all unit tests pass with mocked API; cannot confirm live API authentication without real GITHUB_TOKEN |
| 15 | Running full pipeline twice produces identical category names and anchor IDs (taxonomy stability) | ? HUMAN NEEDED | Slug derivation is deterministic (category_to_slug is pure Python); SYSTEM_PROMPT seeds taxonomy from starred_repos.md — but live stability requires an actual model run to confirm |

**Score:** 13/15 truths verified (2 require live API execution)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/categorize.py` | AI batch categorization pipeline | ✓ VERIFIED | 170 lines; 8 public functions; BATCH_SIZE=10; Bearer auth; parse_with_retry; write_categories |
| `tests/test_categorize.py` | Unit tests for all categorize.py functions (mocked) | ✓ VERIFIED | 17 tests across 6 test classes (TestCallModel, TestStripFences, TestParseWithRetry, TestCategorizeAll, TestWriteCategories, TestCategoryToSlug); zero live API calls |
| `tests/fixtures/sample_categories.json` | Fixture for generate.py integration tests | ✓ VERIFIED | 5 repos (torvalds/linux, microsoft/vscode, golang/go, neovim/neovim, psf/requests) with proper category/subcategory/slug structure |
| `scripts/generate.py` | Hierarchical HTML generation with AI categories | ✓ VERIFIED | CATEGORY_META (14 entries), group_by_categories_hierarchical, render_subcategory_header, render_sections_hierarchical, render_nav_hierarchical — all present and substantive |
| `tests/test_generate.py` | Tests for new hierarchical functions + regression | ✓ VERIFIED | TestCategoryMetaLookup (3), TestGroupByCategoriesHierarchical (3), TestRenderSubcategoryHeader (4), TestRenderNavHierarchical (3), TestOutputFileHierarchical (1) = 14 new tests |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `categorize_all()` | `_data/categories.json` | `write_categories()` | ✓ WIRED | `write_categories(cat_map)` called in `__main__`; json.dump writes the file |
| `categorize_all()` | `call_model()` | `range(0, len(repos), BATCH_SIZE)` | ✓ WIRED | Line 132: `for i in range(0, len(repos), BATCH_SIZE):` → calls `parse_with_retry()` → calls `call_model()` |
| `parse_with_retry()` | Other fallback | Two consecutive JSONDecodeError | ✓ WIRED | Line 125: `[ERROR] … Assigning batch to Other` → `return {name: {"category": "Other", …} for name in batch_names}` |
| `generate.py __main__` | `group_by_categories_hierarchical()` | `if cat_map:` branch | ✓ WIRED | Line 574: `if cat_map:` → calls `group_by_categories_hierarchical(repos, cat_map)` |
| `render_sections_hierarchical()` | `render_subcategory_header()` | inner loop over subcats.items() | ✓ WIRED | Line 342: `section_lines.append(render_subcategory_header(subcat_name, …))` |
| `render_section()` | `CATEGORY_META` | slug in CATEGORY_META lookup | ✓ WIRED | Line 253: `if slug in CATEGORY_META:` — returns 2-tuple with icon_name for Material Icons span |
| `render_nav_hierarchical()` | `CATEGORY_META` | material-icons span for known slugs | ✓ WIRED | Lines 383–386: `if slug in CATEGORY_META: … icon_html = f'<span class="material-icons …">{icon_name}</span>'` |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 45 tests pass (17 categorize + 7 fetch + 21 generate) | `python3 -m pytest tests/ -x -q --tb=short` | 45 passed, 1 warning in 0.05s | ✓ PASS |
| BATCH_SIZE = 10 produces correct API call count | TestCategorizeAll::test_batch_count_25_repos | 3 calls for 25 repos | ✓ PASS |
| Python slug overrides model's wrong slug | TestCategorizeAll::test_slug_derived_from_category_not_model | `result["owner/repo0"]["slug"] == "ai-ml"` (not "WRONG") | ✓ PASS |
| Missing repos from model response get Other/Other | TestCategorizeAll::test_missing_from_result_gets_other | `result["owner/repo1"]["category"] == "Other"` | ✓ PASS |
| Safety Orange subcategory header rendered | TestOutputFileHierarchical::test_hierarchical_output_file_created | `assertIn("bg-[#FF5F1F]", content)` passes | ✓ PASS |
| Bearer auth confirmed (not "token " prefix) | `grep "Bearer" scripts/categorize.py` | `"Authorization": f"Bearer {token}"` | ✓ PASS |
| GITHUB_TOKEN not logged | `grep -n "token" scripts/categorize.py` excluding auth line | Only assignment + build_session() call | ✓ PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| AI-01 | 03-01 | GitHub Models API at correct URL, Bearer auth | ✓ SATISFIED | `GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"`; `Authorization: Bearer {token}` |
| AI-02 | 03-01 | Batch 10 repos per API call | ✓ SATISFIED | `BATCH_SIZE = 10`; verified by test_batch_count_25_repos (3 calls for 25 repos) |
| AI-03 | 03-01 | System prompt seeds taxonomy from starred_repos.md | ✓ SATISFIED | SYSTEM_PROMPT contains full 14-category taxonomy with 30+ subcategories from starred_repos.md |
| AI-04 | 03-01 | parse_with_retry with [WARN] + retry + [ERROR] + Other fallback | ✓ SATISFIED | parse_with_retry() at lines 110–126; [WARN]/[ERROR] prefixes confirmed; all 3 TestParseWithRetry cases pass |
| AI-05 | 03-01, 03-02 | Python-side slug derivation; never from model | ✓ SATISFIED | category_to_slug() used in categorize_all(); model's slug field ignored; slug regenerated from canonical category name |

**All 5 Phase 3 requirements satisfied.**

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No TODOs, FIXMEs, placeholder returns, or empty implementations found in any Phase 3 files. All stubs replaced with real implementations.

---

### Human Verification Required

#### 1. Live GitHub Models API End-to-End Run

**Test:** With a valid `GITHUB_TOKEN` (models:read + contents:write permissions), run:
```bash
python scripts/fetch_stars.py          # produces _data/repos.json
python scripts/categorize.py           # calls GitHub Models, produces _data/categories.json
python scripts/generate.py             # produces docs/index.html
```
**Expected:**
- `_data/categories.json` created with every repo mapped to a category, subcategory, and slug
- Category names recognizably match starred_repos.md taxonomy (e.g. "AI & ML", "Self-Hosting & Homelab", "Dev Tools & CLI" — not "Machine Learning" or "Infrastructure")
- `docs/index.html` contains hierarchical sections with Safety Orange subcategory dividers and Material Icons in nav
- Pipeline completes without error; total API calls = `ceil(repo_count / 10)` (verify in stdout batch log lines)

**Why human:** GitHub Models API requires a real `GITHUB_TOKEN` with `models: read` permission. The sandbox environment does not have this credential. All code-level correctness is verified; only the live network authentication remains unconfirmed.

#### 2. Taxonomy Stability Across Two Consecutive Runs

**Test:** After completing the live run above, run the full pipeline a second time without changing any starred repos:
```bash
python scripts/fetch_stars.py
python scripts/categorize.py
python scripts/generate.py
diff docs/index.html docs/index.html.bak  # (save index.html before second run)
```
**Expected:** Zero differences in category names and anchor IDs between the two generated HTML files. The same repos land in the same categories; slugs are identical.

**Why human:** Taxonomy stability across live model responses cannot be confirmed without running the real GitHub Models API twice. The slug derivation is deterministic in Python (verified), but the model's category name outputs must actually be stable with the seeded taxonomy prompt. This confirms ROADMAP SC-3.

---

### Gaps Summary

No gaps blocking goal achievement. All 13 programmatically-verifiable must-haves pass. The 2 human verification items are integration/environment checks that confirm the code works with real credentials — they do not indicate code defects.

**Phase 3 code is complete and correct.** The implementation delivers:
- Full AI batch categorization pipeline (`categorize.py`) with proper GitHub Models API integration
- Hierarchical HTML generation (`generate.py`) with Safety Orange subcategory dividers and Material Icons nav
- 45/45 tests passing (17 categorize, 7 fetch, 21 generate) with zero live API calls
- All 5 AI requirements (AI-01 through AI-05) satisfied
- Security: Bearer auth, GITHUB_TOKEN not logged, html_url escaped, marquee injection-safe

---

_Verified: 2026-04-23T10:00:00Z_
_Verifier: the agent (gsd-verifier)_
