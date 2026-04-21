# Roadmap — AI Stars Gallery

*Granularity: standard | Phases: 4 | Coverage: 28/28 v1 requirements*

---

## Phases

- [ ] **Phase 1: Static Shell + GitHub Pages Live** — Stitch-themed HTML with hardcoded sample data served on the live Pages URL; proves aesthetic and hosting before any pipeline code
- [ ] **Phase 2: Live Data Pipeline (no AI)** — Python fetch + generate scripts run end-to-end; real starred repos appear in the gallery under a single "All Repos" grouping
- [ ] **Phase 3: AI Categorization** — GitHub Models batching categorizes all repos; page displays full hierarchical taxonomy with stable anchor IDs
- [ ] **Phase 4: Automated Daily Action** — GitHub Action runs on schedule; gallery self-updates, no-change guard prevents noise commits, `[skip ci]` prevents loops

---

## Phase Details

### Phase 1: Static Shell + GitHub Pages Live

**Goal**: A live public URL serves a visually complete Stitch-themed gallery page with hardcoded sample repos — proving the aesthetic, layout, and Pages hosting before writing any pipeline code

**Depends on**: Nothing (first phase) — but requires SETUP-01 prerequisite: repo must be on the correct GitHub account before Phase 4 automation

**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04, HTML-02, HTML-03, HTML-04, HTML-05, HTML-06

**Success Criteria** (what must be TRUE when this phase completes):
1. Visiting the GitHub Pages URL returns a styled page — not a 404, not a raw file listing
2. Page displays Safety Orange accent, JetBrains Mono font, deep-black dark background, zero border-radius, and a scanline animation overlay — visually matching `stitch_example/code.html`
3. Dark mode activates automatically when the OS is set to dark (no JavaScript toggle)
4. Status strip at the top shows a serial number, hardcoded repo count, and a last-updated timestamp
5. At least 10 hardcoded sample repo cards render correctly: name as a clickable link (new tab), K-formatted star count, language badge with color dot, description text

**Plans**: 2 plans

Plans:
- [ ] 01-01-PLAN.md — Create docs/index.html (full Stitch HTML shell, 12 hardcoded repo cards, 6 sections) + update .gitignore
- [ ] 01-02-PLAN.md — Enable GitHub Pages from docs/ on main branch + human-verify live URL

**UI hint**: yes

---

### Phase 2: Live Data Pipeline (no AI)

**Goal**: Real starred repos populate the gallery automatically — a Python fetch script pulls live data and a generator script produces the HTML, with repos grouped by their GitHub-reported language as a stand-in category structure

**Depends on**: Phase 1 (live Pages URL + HTML shell structure)

**Requirements**: FETCH-01, FETCH-02, FETCH-03, HTML-01, HTML-07, HTML-08, HTML-09

**Success Criteria** (what must be TRUE when this phase completes):
1. Running `python scripts/fetch_stars.py` produces `_data/repos.json` containing all starred repos (not just the first 30 or 100 — pagination verified by count matching the star count on the GitHub profile)
2. Forked repos and archived repos are absent from the generated `_data/repos.json`
3. Running `python scripts/generate.py` after the fetch produces `docs/index.html` with all repos appearing in category sections, each section headed by a name, emoji marker, and repo count badge
4. Repos within each section are ordered from highest to lowest star count
5. The category navigation (sidebar or inline) lists all sections with anchor links that scroll to the correct section on click
6. The `_data/` directory is not committed — only `docs/index.html` changes in git

**Plans**: TBD
**UI hint**: yes

---

### Phase 3: AI Categorization

**Goal**: GitHub Models intelligently groups all starred repos into the taxonomy from `starred_repos.md` — replacing language-buckets with meaningful AI & ML, Self-Hosting, Dev Tools, and other human-legible categories that remain stable across daily runs

**Depends on**: Phase 2 (`_data/repos.json` schema established; generate.py accepts category input)

**Requirements**: AI-01, AI-02, AI-03, AI-04, AI-05

**Success Criteria** (what must be TRUE when this phase completes):
1. Running `python scripts/categorize.py` calls GitHub Models and produces `_data/categories.json` mapping every repo to a `category`, `subcategory`, and stable `slug`
2. Category names recognizably match the `starred_repos.md` taxonomy (e.g. "AI & ML", "Self-Hosting & Homelab", "Dev Tools & CLI") — not arbitrary model-invented names — confirming taxonomy seeding works
3. Running the full pipeline twice in a row (fetch → categorize → generate) produces HTML with the same category names and the same anchor IDs both times — confirming taxonomy stability and slug stability
4. The workflow logs a parse-error message and retries when the model returns malformed JSON — and the pipeline still completes successfully on the retry
5. Total API calls to GitHub Models per full run does not exceed 40 (verified in Action logs), confirming the 10-repo batch size is respected

**Plans**: TBD

---

### Phase 4: Automated Daily Action

**Goal**: The gallery updates itself every day without any manual intervention — a GitHub Action runs the full pipeline on a schedule, commits only when content changed, and cannot trigger itself recursively

**Depends on**: Phase 3 (all three scripts functional end-to-end; `docs/index.html` generation verified)

**Requirements**: ACTION-01, ACTION-02, ACTION-03, ACTION-04, DEPLOY-01, DEPLOY-02, DEPLOY-03

**Success Criteria** (what must be TRUE when this phase completes):
1. The workflow appears in the Actions tab and can be triggered manually via `workflow_dispatch` — completing successfully with green checkmarks on all steps
2. After the workflow runs, `docs/index.html` is updated in git and the live GitHub Pages URL reflects the new content within ~10 minutes
3. Running the workflow twice in a row (with no star changes between runs) produces exactly one commit on the first run and zero commits on the second run — confirming the no-change guard works
4. The auto-commit message contains `[skip ci]` and does **not** trigger a new workflow run (verify in Actions tab — no child run spawned)
5. The workflow logs the authenticated `GITHUB_ACTOR` username in the first step output, making account mismatch immediately visible if the repo is ever moved

**Plans**: TBD

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Static Shell + GitHub Pages Live | 2/2 | Not started | — |
| 2. Live Data Pipeline (no AI) | 0/? | Not started | — |
| 3. AI Categorization | 0/? | Not started | — |
| 4. Automated Daily Action | 0/? | Not started | — |

---

## Coverage Map

| Requirement | Phase |
|-------------|-------|
| SETUP-01 | Phase 1 |
| SETUP-02 | Phase 1 |
| SETUP-03 | Phase 1 |
| SETUP-04 | Phase 1 |
| HTML-02 | Phase 1 |
| HTML-03 | Phase 1 |
| HTML-04 | Phase 1 |
| HTML-05 | Phase 1 |
| HTML-06 | Phase 1 |
| FETCH-01 | Phase 2 |
| FETCH-02 | Phase 2 |
| FETCH-03 | Phase 2 |
| HTML-01 | Phase 2 |
| HTML-07 | Phase 2 |
| HTML-08 | Phase 2 |
| HTML-09 | Phase 2 |
| AI-01 | Phase 3 |
| AI-02 | Phase 3 |
| AI-03 | Phase 3 |
| AI-04 | Phase 3 |
| AI-05 | Phase 3 |
| ACTION-01 | Phase 4 |
| ACTION-02 | Phase 4 |
| ACTION-03 | Phase 4 |
| ACTION-04 | Phase 4 |
| DEPLOY-01 | Phase 4 |
| DEPLOY-02 | Phase 4 |
| DEPLOY-03 | Phase 4 |

**Mapped: 28/28 ✓ — No orphaned requirements**

---

## Key Architectural Constraints (carry forward to every phase)

| Constraint | Implication |
|------------|-------------|
| Static HTML only (GitHub Pages) | No server, no build step, no `node_modules`; one Python script writes one HTML file |
| Tailwind CDN (not CLI build) | Inline `tailwind.config` block; custom theme tokens set there; never `npx tailwindcss` |
| GitHub Models free tier: 150 req/day (Low tier) | Batch at 10 repos/call → ≤37 calls; never 1 call per repo |
| `GITHUB_TOKEN` for both APIs | No external secrets; `models: read` + `contents: write` permissions required in workflow |
| `_data/*.json` are ephemeral runner files | Always in `.gitignore`; only `docs/index.html` is ever committed |
| Stable category slugs | Slugs derived from canonical names, never regenerated arbitrarily; protects bookmarks and anchor links |
| `[skip ci]` on auto-commits | Mandatory — prevents infinite Action loop |

---

*Last updated: 2026-04-21*
