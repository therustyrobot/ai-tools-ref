# Phase 01 — Validation Strategy

**Phase:** 01-static-shell-github-pages-live
**Date:** 2026-04-21
**Nyquist validation:** enabled

---

## Test Framework

| Property | Value |
|----------|-------|
| Framework | None — static HTML; no test runner applicable |
| Config file | N/A |
| Quick run command | `curl -s -o /dev/null -w "%{http_code}" https://therustyrobot.github.io/ai-tools-ref/` |
| Full suite command | Automated greps + manual visual checklist (see below) |

> **Note:** `nyquist_validation: true` is configured, but Phase 1 produces a single static HTML file with no logic to unit test. Validation is done via HTTP checks (automated) and browser visual inspection (manual). No Wave 0 test files needed.

---

## Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SETUP-02 | Pages URL returns HTTP 200 | smoke | `curl -s -o /dev/null -w "%{http_code}" https://therustyrobot.github.io/ai-tools-ref/` | ✅ (curl, no file needed) |
| SETUP-03 | `_data/` in `.gitignore` | git check | `grep "_data/" .gitignore` | ✅ |
| SETUP-04 | `docs/index.html` committed | git check | `git ls-files docs/index.html` | ✅ Wave 0: create the file |
| HTML-02 | Tailwind CDN script tag present | grep | `grep "cdn.tailwindcss.com" docs/index.html` | ✅ Wave 0: create the file |
| HTML-02 | Google Fonts link tags present | grep | `grep "fonts.googleapis.com" docs/index.html` | ✅ Wave 0: create the file |
| HTML-03 | Safety Orange token present | grep | `grep "FF5F1F" docs/index.html` | ✅ Wave 0: create the file |
| HTML-03 | borderRadius 0px config present | grep | `grep "borderRadius" docs/index.html` | ✅ Wave 0: create the file |
| HTML-03 | Scanline animation present | grep | `grep "scanline" docs/index.html` | ✅ Wave 0: create the file |
| HTML-04 | darkMode: media (not class) | grep | `grep '"media"' docs/index.html` | ✅ Wave 0: create the file |
| HTML-05 | Status strip present | grep | `grep "SYSTEM_ACTIVE" docs/index.html` | ✅ Wave 0: create the file |
| HTML-06 | ≥10 star count entries (K-format) | grep + count | `grep -c "★" docs/index.html` (expect ≥10) | ✅ Wave 0: create the file |
| HTML-06 | Language badges present | grep + count | `grep -c 'style="background-color' docs/index.html` (expect ≥10) | ✅ Wave 0: create the file |

---

## Sampling Rate

- **Per task commit:** `grep "cdn.tailwindcss.com" docs/index.html && grep '"media"' docs/index.html && grep "_data/" .gitignore`
- **Per wave merge:** All grep checks above + `curl -I https://therustyrobot.github.io/ai-tools-ref/`
- **Phase gate:** Live URL returns HTTP 200 AND manual visual checklist passes before `/gsd-verify-work`

---

## Manual Visual Checklist (Phase Gate)

```
□ 1. Page loads at https://therustyrobot.github.io/ai-tools-ref/ — no 404, no raw HTML
□ 2. Safety Orange accent visible (nav hover, star counts, status values)
□ 3. JetBrains Mono font renders (monospace, not system default)
□ 4. Deep-black background in dark mode (set OS to dark)
□ 5. Zero border-radius — all containers have sharp corners
□ 6. Scanline animation visible (thin orange line sweeping top to bottom)
□ 7. Dark mode auto-activates at OS level — no button needed
□ 8. Status strip: SERIAL NO, TOTAL_REPOS, UPDATED timestamp all visible
□ 9. ≥10 repo cards render with name link, ★ K-count, language dot, description
□ 10. Category sidebar nav visible; clicking a link smooth-scrolls to section
```

---

## Wave 0 Gaps

- [ ] `docs/index.html` — the only deliverable; does not exist yet → create in Wave 1
- [ ] `.gitignore` entry `_data/` → add in same commit as index.html

---

*Validation strategy: 2026-04-21*
