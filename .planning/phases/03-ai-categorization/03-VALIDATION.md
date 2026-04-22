---
phase: 3
slug: 03-ai-categorization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-22
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pytest.ini` (exists — `testpaths = tests`) |
| **Quick run command** | `python -m pytest tests/ -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -v`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| categorize-01 | 03-01 | 0 | AI-01 | — | Bearer token not logged/leaked | unit | `pytest tests/test_categorize.py::TestCallModel -x` | ❌ W0 | ⬜ pending |
| categorize-02 | 03-01 | 0 | AI-02 | — | N/A | unit | `pytest tests/test_categorize.py::TestCategorizeAll -x` | ❌ W0 | ⬜ pending |
| categorize-03 | 03-01 | 0 | AI-03 | — | N/A | unit | `pytest tests/test_categorize.py::TestBuildMessages -x` | ❌ W0 | ⬜ pending |
| categorize-04 | 03-01 | 0 | AI-04 | — | N/A | unit | `pytest tests/test_categorize.py::TestParseWithRetry -x` | ❌ W0 | ⬜ pending |
| categorize-05 | 03-01 | 0 | AI-05 | — | N/A | unit | `pytest tests/test_categorize.py::TestCategoryToSlug -x` | ❌ W0 | ⬜ pending |
| generate-01 | 03-02 | 0 | D-01 | — | N/A | unit | `pytest tests/test_generate.py::TestRenderSectionsHierarchical -x` | ❌ W0 | ⬜ pending |
| generate-02 | 03-02 | 0 | D-02 | — | N/A | unit | `pytest tests/test_generate.py::TestRenderSubcategoryHeader -x` | ❌ W0 | ⬜ pending |
| generate-03 | 03-02 | 0 | D-04 | — | N/A | unit | `pytest tests/test_generate.py::TestGroupByCategoriesHierarchical -x` | ❌ W0 | ⬜ pending |
| generate-04 | 03-02 | 0 | D-06 | — | N/A | unit | `pytest tests/test_generate.py::TestCategoryMetaLookup -x` | ❌ W0 | ⬜ pending |
| regression-01 | 03-02 | 1 | Fallback | — | N/A | regression | `pytest tests/test_generate.py::TestOutputFileCreated -x` | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_categorize.py` — stubs for AI-01, AI-02, AI-03, AI-04, AI-05
- [ ] `tests/test_generate.py` — new test classes for D-01, D-02, D-04, D-06

*Existing infrastructure (pytest.ini, conftest if any) covers the framework — only new test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| categories.json matches starred_repos.md taxonomy names | AI-03 | Requires live GitHub Models API call | Run `GITHUB_TOKEN=... python scripts/categorize.py` and inspect `_data/categories.json` — category names should match starred_repos.md sections |
| API calls ≤ 40 per run | AI-02/AI-05 (Success Criterion 5) | Requires counting live API calls | Run with `GITHUB_TOKEN=...`, count log lines `"Categorizing batch"` — must be ≤ 40 |
| Same category/anchor IDs on two successive runs | AI-05 (Success Criterion 3) | Requires live API + comparison | Run pipeline twice, `diff docs/index.html docs/index.html.bak` — 0 category/section ID differences |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
