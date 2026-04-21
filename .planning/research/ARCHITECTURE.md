# Architecture Patterns

**Domain:** GitHub Stars Gallery — static site with AI categorization pipeline
**Researched:** 2026-04-21
**Confidence:** HIGH (components are simple and well-understood; GitHub Models rate limit specifics are LOW — see notes)

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                        │
│             (daily cron 0 6 * * * + workflow_dispatch)           │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Stars        │    │ AI           │    │ HTML             │   │
│  │ Fetcher      │───▶│ Categorizer  │───▶│ Generator        │   │
│  │ (Python)     │    │ (Python)     │    │ (Python)         │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│         │                  │                      │              │
│    GitHub REST API    GitHub Models API      docs/index.html    │
│    (GITHUB_TOKEN)     (GITHUB_TOKEN)                            │
│                                                   │              │
│                                           ┌───────▼──────────┐  │
│                                           │ Git Commit       │  │
│                                           │ (only if changed)│  │
│                                           └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                                   │
                                                   ▼
                                         GitHub Pages
                                         (docs/index.html)
                                         static serving
```

---

## Component Boundaries

| Component | File(s) | Responsibility | Inputs | Outputs |
|-----------|---------|----------------|--------|---------|
| **Workflow** | `.github/workflows/update-gallery.yml` | Orchestrates all steps; sets env; handles permissions | cron / manual trigger | runs all components |
| **Stars Fetcher** | `scripts/fetch_stars.py` | Calls GitHub Stars REST API; paginates; emits structured repo list | `GITHUB_TOKEN`, `GITHUB_ACTOR` (username) | `_data/repos.json` |
| **AI Categorizer** | `scripts/categorize.py` | Batches all repos into one prompt; calls GitHub Models; emits category mapping | `_data/repos.json`, `GITHUB_TOKEN` | `_data/categories.json` |
| **HTML Generator** | `scripts/generate.py` | Merges repos + categories; renders Stitch-aesthetic HTML | `_data/repos.json`, `_data/categories.json` | `docs/index.html` |
| **Git Commit step** | workflow inline | Diffs output; skips commit if no change; pushes | `docs/index.html` | committed file |
| **GitHub Pages** | repo settings | Serves static HTML from `docs/` on `main` branch | `docs/index.html` | public URL |

---

## Data Flow

```
1. TRIGGER
   GitHub Actions cron (0 6 * * *) or workflow_dispatch
        │
        ▼
2. FETCH STARS
   GET https://api.github.com/users/{actor}/starred?per_page=100&page={n}
   Auth: Bearer GITHUB_TOKEN
   Rate limit: 5000 req/hour authenticated — 370 repos = ~4 pages = no concern
   Output: _data/repos.json
   Schema: [{ "name", "full_name", "html_url", "description",
               "language", "stargazers_count" }, ...]
        │
        ▼
3. AI CATEGORIZE
   POST https://models.inference.ai.azure.com/chat/completions
   Auth: Bearer GITHUB_TOKEN
   Strategy: ONE batched call — all repos in single prompt
     • Prompt includes repo name + description for all ~370 repos
     • Instructs model to return JSON: { "full_name": { "category", "subcategory" } }
     • Uses starred_repos.md taxonomy as few-shot examples in system prompt
   Output: _data/categories.json
        │
        ▼
4. GENERATE HTML
   Python reads repos.json + categories.json
   Groups repos by category → subcategory
   Renders self-contained index.html:
     • Stitch brutalist theme (Tailwind CDN, JetBrains Mono, Safety Orange)
     • Embedded JS for category nav (click → scroll to section)
     • Each repo card: name (link), ★ count, language badge, description
   Output: docs/index.html
        │
        ▼
5. COMMIT (conditional)
   git diff --quiet docs/index.html || git commit -m "chore: update gallery"
   Skips empty commits when stars haven't changed
        │
        ▼
6. SERVE
   GitHub Pages reads docs/index.html from main branch
   No build step — file is already rendered HTML
```

---

## Suggested Build Order

Dependencies flow strictly left-to-right. Build in this order:

```
Phase 1: Stars Fetcher
   └─ No dependencies. Testable in isolation with: gh api /users/{user}/starred
   └─ Validates: auth works, pagination works, output schema correct

Phase 2: HTML Generator (with mock data)
   └─ Depends on: output schema from Phase 1 (repos.json structure)
   └─ Use hardcoded mock categories.json during development
   └─ Validates: Stitch theme renders correctly, category nav works

Phase 3: AI Categorizer
   └─ Depends on: repos.json schema (Phase 1) + categories.json schema (Phase 2)
   └─ Must finalize prompt → output structure before generator relies on it
   └─ Validates: GitHub Models accessible from Actions, batching works

Phase 4: Workflow Integration
   └─ Wires Phase 1 → 3 → 2 → commit
   └─ Adds conditional commit (no-op when unchanged)
   └─ Validates: full end-to-end run succeeds

Phase 5: GitHub Pages
   └─ Enable Pages (docs/ on main) in repo settings
   └─ Validates: public URL serves correctly
```

---

## Key Architectural Decisions

### Decision 1: Single-Batch AI Call
**What:** Send all repo names + descriptions in ONE prompt to GitHub Models.
**Why:** GitHub Models has strict daily request limits (low single-digit to double-digit per day on free tier — **LOW confidence on exact numbers; verify at runtime**). Batching everything into one call eliminates the risk of quota exhaustion regardless of the limit.
**Tradeoff:** Requires model with large context window (≥32K tokens). GPT-4o / gpt-4o-mini support 128K — easily handles 370 repos × ~100 chars ≈ ~9K tokens.
**Risk if wrong:** If one call fails, no partial state to resume from. Acceptable: old HTML stays live.

### Decision 2: Full Regeneration Every Run
**What:** Re-fetch all stars and re-categorize all repos on every run.
**Why:** PROJECT.md explicitly calls this out. Eliminates category drift. No state management complexity.
**Tradeoff:** Wastes 1 AI API call if nothing changed. Mitigated by: checking git diff before committing — the page only updates when content actually changes.
**When to reconsider:** If stars count grows to thousands AND GitHub Models free tier proves insufficient.

### Decision 3: Intermediate JSON Files on Runner
**What:** Stars Fetcher writes `_data/repos.json`; Categorizer reads it and writes `_data/categories.json`.
**Why:** Decouples components. Each script is independently testable. Runner filesystem is ephemeral — files live only for the duration of the job.
**Alternative rejected:** Piping between scripts — harder to debug and test in isolation.
**Note:** These `_data/` files are NOT committed to the repo (add to `.gitignore`).

### Decision 4: `docs/` Directory for Pages
**What:** HTML output goes to `docs/index.html`. GitHub Pages configured for `docs/` on `main`.
**Why:** Keeps generated output isolated from source files. Alternative (root index.html) pollutes the repo root.
**Implication:** Workflow must `git add docs/index.html` specifically, not `git add -A`.

### Decision 5: Category Nav Embedded in Page (no top bar)
**What:** Navigation is a sidebar or inline section list within the page body.
**Why:** PROJECT.md requirement — "embedded in the page layout (not a top header menu)".
**Implementation:** Fixed left sidebar with JS scroll-to-section on click, OR anchor links inline within the hero area. Pure HTML/CSS/vanilla JS — no framework.

### Decision 6: GITHUB_TOKEN for Both APIs
**What:** Use the workflow's built-in `GITHUB_TOKEN` for both the Stars REST API and the GitHub Models API.
**Why:** No external secrets needed. `GITHUB_TOKEN` is automatically provided and authenticates to both endpoints.
**Required permission:** `contents: write` (to commit). Declare explicitly in workflow `permissions:` block.

---

## Component Details

### Stars Fetcher
```python
# Pseudocode
GET /users/{GITHUB_ACTOR}/starred
  params: per_page=100, page=1..N
  headers: Authorization: Bearer {GITHUB_TOKEN}
           Accept: application/vnd.github.star+json  # includes starred_at timestamp
Loop until response is empty list
Serialize: [{ name, full_name, html_url, description, language, stargazers_count }]
Write: _data/repos.json
```

### AI Categorizer
```python
# Pseudocode — single batch call
system_prompt = """
You are a taxonomy engine. Categorize each GitHub repo into a category and subcategory.
Use this reference taxonomy (from starred_repos.md):
  AI & ML / Agent Frameworks, MCP Servers, LLM UIs, ...
  Self-Hosting & Homelab / Dashboards, Monitoring, ...
  Dev Tools & CLI / Terminal, Documentation, ...
  [etc.]

Return ONLY valid JSON: {"owner/repo": {"category": "...", "subcategory": "..."}, ...}
"""
user_prompt = "\n".join([f"{r['full_name']}: {r['description']}" for r in repos])

POST https://models.inference.ai.azure.com/chat/completions
  headers: Authorization: Bearer {GITHUB_TOKEN}
  body: { model: "gpt-4o-mini", messages: [system, user], response_format: json_object }

Parse response → write _data/categories.json
```

### HTML Generator
```
Input:  _data/repos.json + _data/categories.json
Logic:  group repos by category → subcategory (sorted by category, then by ★ desc within)
Output: single self-contained docs/index.html
        - <link> Google Fonts (JetBrains Mono, Inter)
        - <script src="https://cdn.tailwindcss.com"> with brutalist config
        - Tailwind config inline (colors, fonts, borderRadius: 0)
        - Scanline animation CSS
        - Category nav (sidebar or inline)
        - Repo cards per section
        - Vanilla JS for nav interaction
```

### Workflow Skeleton
```yaml
name: Update Stars Gallery
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: '3.12' }

      - name: Install deps
        run: pip install requests

      - name: Fetch stars
        env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
        run: python scripts/fetch_stars.py

      - name: Categorize with AI
        env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
        run: python scripts/categorize.py

      - name: Generate HTML
        run: python scripts/generate.py

      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/index.html
          git diff --cached --quiet || git commit -m "chore: update stars gallery [skip ci]"
          git push
```

---

## Rate Limiting Analysis

| API | Limit | Our Usage | Risk |
|-----|-------|-----------|------|
| GitHub Stars REST | 5,000 req/hour (authenticated) | ~4 pages for 370 repos | None |
| GitHub Stars REST (pages) | 100 repos/page max | 4 requests for 370 repos | None |
| GitHub Models (free tier) | LOW CONFIDENCE: reportedly ~15–150 req/day depending on model | 1 request/run | Low if batching correctly |
| GitHub Actions minutes | 2,000 min/month (free) | ~2–5 min/run × 30 = ~150 min/month | None |

**Stars API pagination math:**
- 370 repos ÷ 100 per page = 4 API calls
- 5,000 limit per hour → completely safe even for 5,000 repos (50 pages)

**GitHub Models batching math:**
- 370 repos × avg 60 chars description = ~22,200 chars ≈ ~5,500 tokens input
- gpt-4o-mini: 128K context window → single call handles 10,000+ repos
- **Recommendation:** Always batch entire star list into ONE AI call

---

## Incremental vs Full Regeneration Tradeoffs

| Factor | Incremental | Full Regeneration | Winner |
|--------|-------------|-------------------|--------|
| Implementation complexity | High (diff state, cache) | Low (stateless) | Full |
| Category consistency | Risk of drift over time | Always consistent | Full |
| AI API calls/run | 0 if no new stars | 1 per run always | Incremental |
| Resilience to taxonomy changes | Must migrate old entries | Automatic | Full |
| Failure recovery | Partial state possible | Clean restart | Full |
| **Verdict** | | | **Full wins** |

**Exception:** If star count grows beyond ~2,000 and GitHub Models free rate limits become a real constraint, introduce a `categories-cache.json` file committed to the repo, and only re-categorize repos NOT already in the cache. This is Phase 2 optimization, not Phase 1.

---

## Scalability Considerations

| Concern | At 370 repos (now) | At 2K repos | At 10K repos |
|---------|-------------------|-------------|--------------|
| Stars API calls | 4 pages | 20 pages | 100 pages |
| AI prompt size | ~5K tokens | ~28K tokens | ~140K tokens |
| HTML file size | ~200KB | ~1MB | ~5MB |
| AI call strategy | Single batch | Single batch | Split into 2-3 batches with shared taxonomy |
| Incremental needed? | No | No | Maybe |

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: One AI Call Per Repo
**What:** Calling GitHub Models for each of 370 repos individually.
**Why bad:** Exhausts free tier rate limits immediately (even 15 req/day limit means only 15 repos categorized). Adds ~370× latency. Workflow times out.
**Instead:** Single batched prompt with all repos.

### Anti-Pattern 2: Committing `_data/*.json` Files
**What:** Committing `repos.json` and `categories.json` to the repo as build artifacts.
**Why bad:** Creates noise commits daily with raw API data. Not useful to version. Clutters history.
**Instead:** Add `_data/` to `.gitignore`. Only `docs/index.html` gets committed.

### Anti-Pattern 3: Using `actions/deploy-pages` for This Use Case
**What:** Using the GitHub Pages Actions deployment workflow instead of committing HTML directly.
**Why bad:** Adds complexity (artifact upload, separate deployment job, environment setup) for no benefit on a simple single-file output.
**Instead:** Commit `docs/index.html` to `main`. Configure Pages to serve from `docs/`. No Actions deployment needed.

### Anti-Pattern 4: JavaScript Framework for the Page
**What:** Building the gallery as a React/Vue/Svelte SPA.
**Why bad:** Requires a build step in the workflow. Adds npm dependencies. Pages CDN serves static HTML fine.
**Instead:** Pure HTML with Tailwind CDN + vanilla JS for category nav.

### Anti-Pattern 5: Skipping `[skip ci]` on Commit
**What:** Letting the auto-commit trigger another workflow run.
**Why bad:** Creates infinite loop — commit triggers workflow, workflow commits, triggers again.
**Instead:** Include `[skip ci]` in commit message, or add `if: github.actor != 'github-actions[bot]'` guard.

---

## Sources

- GitHub REST API rate limits: `https://docs.github.com/en/rest/rate-limit/rate-limit` — confirmed 5000 req/hr for authenticated (HIGH confidence)
- GitHub Stars endpoint: `https://docs.github.com/en/rest/activity/starring` (HIGH confidence)
- GitHub Actions cron syntax: `/websites/github_en_actions` via Context7 (HIGH confidence)
- GitHub Models endpoint: `https://models.inference.ai.azure.com` — confirmed reachable (requires auth) (HIGH confidence)
- GitHub Models free tier rate limits: Not found in official docs at time of research (LOW confidence — verify experimentally in Phase 1)
- `[skip ci]` behavior: Standard GitHub Actions convention (HIGH confidence)
