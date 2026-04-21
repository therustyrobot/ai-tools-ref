# Requirements — AI Stars Gallery

*Generated: 2026-04-21 | Coverage: 28 v1 requirements across 6 categories*

---

## V1 Requirements

### SETUP — Project Scaffolding & Prerequisites

| ID | Requirement | Notes |
|----|-------------|-------|
| SETUP-01 | ⚠️ **Prerequisite:** Repo must live on the same GitHub account that owns the starred repos | `GITHUB_TOKEN` is scoped to the repo owner; stars fetched will be *that* account's stars — cannot cross account boundaries |
| SETUP-02 | GitHub Pages enabled to serve from `docs/` directory on `main` branch | No Actions deployment action needed; Pages auto-serves a root `index.html` inside `docs/`; configure in repo Settings → Pages |
| SETUP-03 | `_data/` added to `.gitignore` | Intermediate pipeline files (`repos.json`, `categories.json`) are ephemeral runner artifacts; never commit them |
| SETUP-04 | Initial `docs/index.html` committed so Pages has a valid entry point before automation runs | Required for Pages to activate; a minimal placeholder is fine — Phase 1 replaces it with the real shell |

---

### FETCH — Stars Data Pipeline

| ID | Requirement | Notes |
|----|-------------|-------|
| FETCH-01 | `scripts/fetch_stars.py` fetches all starred repos via `GET /user/starred?per_page=100` authenticated with `GITHUB_TOKEN`; paginates via `Link: rel="next"` header until exhausted | Default `per_page=30` silently drops repos; always use 100; 370 repos = 4 pages = 4 API calls (negligible against 5,000 req/hr limit) |
| FETCH-02 | Filter out repos where `fork == true` or `archived == true` before writing output | Forks are personal throwaway copies; archived repos may be defunct; both dilute gallery signal |
| FETCH-03 | Write `_data/repos.json`: JSON array of objects with keys `full_name`, `name`, `html_url`, `description`, `language`, `stargazers_count` | This schema is the contract between fetch and generate; all downstream scripts depend on it |

---

### AI — Categorization Script

| ID | Requirement | Notes |
|----|-------------|-------|
| AI-01 | `scripts/categorize.py` calls GitHub Models API at `https://models.github.ai/inference/chat/completions` using `GITHUB_TOKEN` as Bearer auth; model: `openai/gpt-4o-mini` | No external API keys; `models: read` workflow permission required; confirmed endpoint from official GitHub Models quickstart docs |
| AI-02 | Batch repos at **10 per API call** (≤ 37 calls for 370 repos, well within 150 req/day free-tier limit for Low-tier models) | 1 call per repo = 370 calls = pipeline fails; batch of 50 risks 8,000-token input limit; batch of 10 ≈ 1,000–2,000 tokens (safe) and uses 37 calls/run |
| AI-03 | System prompt seeds taxonomy from `starred_repos.md` — include the 13 top-level categories and 30+ subcategories as reference; instruct model to use existing names before inventing new ones | Prevents taxonomy drift: without seeding, "Machine Learning" becomes "AI/ML" then "Deep Learning" on successive runs; `starred_repos.md` is the authoritative quality bar |
| AI-04 | Request `response_format: {"type": "json_object"}`; strip markdown code fences (` ```json...``` `) before `json.loads()`; on `JSONDecodeError`, retry once with a clarifying message ("Return only valid JSON, no preamble"); log the raw response to stdout on second failure | Models sometimes wrap JSON in fences or prepend preamble text even with json_object mode; silent parse failures cause entire batches to vanish from the gallery |
| AI-05 | Write `_data/categories.json`: dict mapping `"owner/repo"` → `{"category": "...", "subcategory": "...", "slug": "..."}` where `slug` is a lowercase-hyphenated stable identifier derived from the canonical category name | Slugs become HTML anchor IDs — they must not change between runs for the same category name, or bookmarks break; derive once and lock: `"AI & ML"` → `"ai-ml"` |

---

### HTML — Page Design & Generator Script

| ID | Requirement | Notes |
|----|-------------|-------|
| HTML-01 | `scripts/generate.py` reads `_data/repos.json` + `_data/categories.json`, groups repos by category → subcategory, and writes a single self-contained `docs/index.html` | All data embedded at build time; no client-side GitHub API calls; single file commit to Pages |
| HTML-02 | Tailwind CSS loaded from `cdn.tailwindcss.com` with inline `tailwind.config` block; JetBrains Mono (monospace) + Inter (sans) from Google Fonts CDN; all custom theme tokens set inline | Zero build step; matches `stitch_example/code.html` exactly; do not use `npx tailwindcss` or add a Node build step to the workflow |
| HTML-03 | Stitch brutalist aesthetic: Safety Orange `#FF5F1F` primary accent, deep black `#0a0a0a` dark background, off-white light background, `borderRadius: 0` everywhere (no rounded corners), scanline animation CSS `@keyframes` overlay | Reference implementation: `stitch_example/code.html`; do not diverge from this aesthetic; scanline effect is the signature visual |
| HTML-04 | Dark mode via `prefers-color-scheme: dark` CSS media query using Tailwind `dark:` utility classes; no JavaScript toggle needed for v1 | Default to system preference; eliminates JS complexity; dev audience expects dark mode by default |
| HTML-05 | Page status strip at top: Stitch-style "SERIAL NO", total repo count (computed at build time), last-updated timestamp (UTC, injected at generation time), status indicator | Communicates data freshness and scale at a glance; mimics the `stitch_example` header band pattern |
| HTML-06 | Repo cards display: repo name as hyperlink (`target="_blank" rel="noopener noreferrer"`), K-formatted star count (`1.2K`, `42K` — not raw integers), language badge with colored dot (static color map for 15 common languages: Python, TypeScript, JavaScript, Go, Rust, Shell, C, C++, Java, Ruby, Swift, Kotlin, Vue, Svelte, Zig), description text | K-formatting in generate.py (≥1000 → round to 1 decimal + K/M); language color map is a hardcoded dict, not AI-generated |
| HTML-07 | Repos sorted by `stargazers_count` descending within each category/subcategory section | Applied in generate.py at grouping time; surfaces most battle-tested tools first; no runtime JS sorting needed |
| HTML-08 | Category and subcategory section headers include: emoji/icon marker (one per top-level category, defined in generate.py config dict), inline repo count badge, stable anchor `id` matching the category slug from `categories.json` | Emoji map hardcoded in generator (not AI-generated): `"ai-ml"` → 🤖, `"self-hosting"` → 🏠, `"dev-tools"` → 🛠️, etc.; anchor IDs enable direct linking |
| HTML-09 | Hierarchical category navigation embedded in page layout (sidebar column or inline section list) — **not** a top header menu; anchor links jump to corresponding section IDs; categories collapse or stack on mobile viewports | PROJECT.md explicit requirement; nav must be part of the page body flow, not a `<header>` navbar |

---

### DEPLOY — Git Commit & Pages Serving

| ID | Requirement | Notes |
|----|-------------|-------|
| DEPLOY-01 | Commit step uses native `git` commands: `git config`, `git add docs/index.html` (only this file — not `_data/`), `git commit`, `git push`; commit author set to `github-actions[bot]` | No third-party commit actions; `git add docs/index.html` explicitly — never `git add -A` |
| DEPLOY-02 | No-change guard: run `git diff --staged --quiet` after staging — if exit code 0 (no diff), skip the commit and push entirely; workflow exits cleanly with no commit | Prevents daily noise commits when stars haven't changed; avoids unnecessary Pages deployments; avoids growing git history with identical-content objects |
| DEPLOY-03 | Auto-commit message includes `[skip ci]` token (e.g. `"chore: regenerate stars gallery [skip ci]"`) | Prevents the auto-commit from re-triggering the workflow and creating an infinite loop — standard GitHub Actions convention |

---

### ACTION — GitHub Actions Workflow

| ID | Requirement | Notes |
|----|-------------|-------|
| ACTION-01 | `.github/workflows/update-gallery.yml` — triggers on `schedule: cron: '0 6 * * *'` (daily 06:00 UTC) AND `workflow_dispatch` (manual trigger) | Daily schedule is the core automation; manual trigger enables first-run and ad-hoc testing |
| ACTION-02 | Workflow `permissions:` block explicitly declares `contents: write` (commit `docs/index.html`) and `models: read` (call GitHub Models API) | Missing `models: read` causes a silent auth failure at the categorization step; must be declared at workflow or job level |
| ACTION-03 | Workflow steps in order: `actions/checkout@v4` → `python scripts/fetch_stars.py` → `python scripts/categorize.py` → `python scripts/generate.py` → native git commit-if-changed | All Python scripts run with `GITHUB_TOKEN` in env; no `setup-python` step needed (Python 3.12 pre-installed on `ubuntu-latest`); no `pip install` needed (`requests` pre-installed on runners, verify on first run) |
| ACTION-04 | Workflow logs `GITHUB_ACTOR` at the start as an account verification signal; if the actor does not match the expected account, log a warning (do not hard-fail — allow manual override) | SETUP-01 prerequisite: if repo is on wrong account, `GITHUB_TOKEN` fetches the wrong person's stars silently; the log line makes debugging obvious without blocking legitimate runs |

---

## V2 Deferred

Features that are valuable but add complexity beyond v1 scope. Revisit after the daily Action is proven reliable.

| ID | Feature | Reason Deferred |
|----|---------|-----------------|
| V2-01 | "NEW" badge on repos starred within last 7 days | Requires storing previous-run repo ID list as a committed artifact; adds state management complexity |
| V2-02 | Sticky sidebar category navigation | CSS `position: sticky` layout gets complex with mobile breakpoints; defer to a polish pass |
| V2-03 | Categories cache for incremental re-categorization | Only needed if star count grows to 2,000+ and free-tier rate limits become a real constraint |
| V2-04 | Tailwind CLI static CSS build (replace CDN) | CDN is fine at single-page scale; avoids adding Node.js toolchain to the Action; revisit if CSP headers ever become an issue |
| V2-05 | Responsive mobile layout with collapsing nav accordion | Desktop-first is fine for a dev-audience reference page in v1 |

---

## Out of Scope

Explicitly excluded — will not be built.

| Feature | Reason |
|---------|--------|
| Search / filter bar | PROJECT.md explicit exclusion; category nav + browser Ctrl+F is sufficient |
| Multiple GitHub accounts | Architectural complexity for zero stated need |
| Backend / database | GitHub Pages is static-only; no server |
| Client-side live GitHub API calls | Rate limits, leaks access patterns, adds latency |
| JavaScript SPA framework (React, Vue, Svelte) | Requires build step; incompatible with static HTML constraint |
| Social features (comments, reactions) | Read-only personal reference page |
| User authentication / login | No private data; page is fully public |
| Pagination | Defeats the single-page browsable reference purpose |
| Infinite scroll | JS-dependent; breaks anchor navigation |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1 | Pending |
| SETUP-02 | Phase 1 | Pending |
| SETUP-03 | Phase 1 | Pending |
| SETUP-04 | Phase 1 | Pending |
| HTML-02 | Phase 1 | Pending |
| HTML-03 | Phase 1 | Pending |
| HTML-04 | Phase 1 | Pending |
| HTML-05 | Phase 1 | Pending |
| HTML-06 | Phase 1 | Pending |
| FETCH-01 | Phase 2 | Pending |
| FETCH-02 | Phase 2 | Pending |
| FETCH-03 | Phase 2 | Pending |
| HTML-01 | Phase 2 | Pending |
| HTML-07 | Phase 2 | Pending |
| HTML-08 | Phase 2 | Pending |
| HTML-09 | Phase 2 | Pending |
| AI-01 | Phase 3 | Pending |
| AI-02 | Phase 3 | Pending |
| AI-03 | Phase 3 | Pending |
| AI-04 | Phase 3 | Pending |
| AI-05 | Phase 3 | Pending |
| ACTION-01 | Phase 4 | Pending |
| ACTION-02 | Phase 4 | Pending |
| ACTION-03 | Phase 4 | Pending |
| ACTION-04 | Phase 4 | Pending |
| DEPLOY-01 | Phase 4 | Pending |
| DEPLOY-02 | Phase 4 | Pending |
| DEPLOY-03 | Phase 4 | Pending |

---

*28 v1 requirements · 5 v2 deferred · 9 out of scope*
*Last updated: 2026-04-21*
