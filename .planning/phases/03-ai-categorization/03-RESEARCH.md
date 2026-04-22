# Phase 3: AI Categorization - Research

**Researched:** 2026-04-22
**Domain:** GitHub Models API · Python batch prompt engineering · Hierarchical HTML generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Hierarchical Display:**
- **D-01:** Subcategories render as **nested sub-sections** within each top-level category section in the HTML — not flat with subcategory badges on cards.
- **D-02:** Subcategory headers use **Safety Orange (#FF5F1F) background** with white text.
- **D-03:** Sidebar navigation shows **top-level categories only** (with repo counts).
- **D-04:** `generate.py` needs `group_by_categories_hierarchical()` returning `{category: {subcategory: [repos]}}`, and `render_subcategory_header()`. Existing `group_by_categories()` and `group_by_language()` remain for backward compatibility.

**Category Metadata in generate.py:**
- **D-05:** New `CATEGORY_META` dict in `generate.py` (separate from `LANG_META`), keyed by slug → `(display_name, material_icon_name)`.
- **D-06:** `render_section()` checks `CATEGORY_META` first → `LANG_META` → fallback `("Unknown", "category")`.
- **D-07:** Icons rendered as Material Icons ligature spans (already loaded in `<head>`). No new CDN dependency.
- **D-08:** Full `CATEGORY_META` mapping locked (14 categories):

```python
CATEGORY_META = {
    "ai-ml":                  ("AI & ML",                "smart_toy"),
    "self-hosting-homelab":   ("Self-Hosting & Homelab", "dns"),
    "dev-tools-cli":          ("Dev Tools & CLI",         "terminal"),
    "devops-infra":           ("DevOps & Infra",          "cloud"),
    "security":               ("Security",                "lock"),
    "web-frontend":           ("Web & Frontend",          "web"),
    "data-analytics":         ("Data & Analytics",        "bar_chart"),
    "productivity-notes":     ("Productivity & Notes",    "edit_note"),
    "media-entertainment":    ("Media & Entertainment",   "movie"),
    "networking":             ("Networking",              "router"),
    "mobile-desktop":         ("Mobile & Desktop",        "devices"),
    "awesome-lists":          ("Awesome Lists",           "star"),
    "esp32-hardware":         ("ESP32 & Hardware",        "developer_board"),
    "other":                  ("Other",                   "category"),
}
```

### the agent's Discretion

- **Fallback behavior:** If `categories.json` is absent or a repo's `full_name` is not found in it, fall back to language-based grouping (existing Phase 2 behavior).
- **Test strategy for categorize.py:** Mock `requests.post`. Test all non-API logic with mocked responses. No real API calls in tests.
- **JSON parse error handling:** On `JSONDecodeError`, log the raw model response and retry once with a clarifying message. On second failure, assign all repos in the batch to "Other" — do not crash.
- **Repo-to-category assignment format:** Model returns JSON object where each key is `"owner/repo"` with value `{"category": "...", "subcategory": "..."}`. `slug` is derived by `categorize.py` from the canonical category name.

### Deferred Ideas (OUT OF SCOPE)

- Subcategory anchor links in sidebar (V2) — D-03 locks sidebar to top-level only.
- Emoji as category icons — replaced by Material Icons per D-07.
- Category caching / incremental re-categorization — V2-03.
- Search / filter bar — explicitly Out of Scope (PROJECT.md).

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AI-01 | `scripts/categorize.py` calls `https://models.github.ai/inference/chat/completions` using `GITHUB_TOKEN` as Bearer auth; model: `openai/gpt-4o-mini` | API endpoint and auth header confirmed in existing STACK.md research [VERIFIED]. Bearer format confirmed. |
| AI-02 | Batch repos at **10 per API call** (≤37 calls for 370 repos) | Batch slicing logic: `repos[i:i+10]` loop. Slug derivation verified to cover all batches. |
| AI-03 | System prompt seeds taxonomy from `starred_repos.md` — 13 top-level + 30+ subcategories | Full taxonomy extracted: 9 + 9 + 6 subcategories under first 3 top-level categories; remaining 11 categories are flat. System prompt template provided below. |
| AI-04 | Request `response_format: {"type": "json_object"}`; strip markdown fences before `json.loads()`; retry once on `JSONDecodeError`; log raw response on second failure | JSON mode confirmed for gpt-4o-mini. Strip pattern: `re.sub(r'\`\`\`json\s*|\s*\`\`\`', '', raw).strip()`. Retry appends clarifying user message. |
| AI-05 | Write `_data/categories.json` mapping `"owner/repo"` → `{"category": "...", "subcategory": "...", "slug": "..."}` with stable slugs derived from canonical category name | Slug derivation verified in Python: all 14 top-level category names and all 30+ subcategory names produce stable, unique slugs using existing `language_to_slug()` logic. |

</phase_requirements>

---

## Summary

Phase 3 adds two distinct deliverables: (1) `scripts/categorize.py` — a new script that reads `_data/repos.json`, batches repos in groups of 10, calls the GitHub Models API to assign each repo a `category` and `subcategory` from the `starred_repos.md` taxonomy, and writes `_data/categories.json`; (2) an upgrade to `scripts/generate.py` that switches from flat language grouping to hierarchical AI category rendering when `categories.json` is present.

The GitHub Models API accepts OpenAI-compatible request JSON with `Authorization: Bearer $GITHUB_TOKEN` and `response_format: {"type": "json_object"}`. The `language_to_slug()` function already in `generate.py` produces correct, stable slugs for all 14 top-level category names and all 30+ subcategory names — **this exact function can be imported from `generate.py` directly in `categorize.py`** (no shared utility extraction needed, as both scripts are in the same `scripts/` directory but loaded via importlib). The cleanest approach is to duplicate the 3-line slug function in `categorize.py` to keep scripts self-contained.

The generate.py changes are additive: new `CATEGORY_META` dict, new `group_by_categories_hierarchical()`, new `render_subcategory_header()`, and a branched entry point. Existing `group_by_language()`, `group_by_categories()`, `render_section()`, `render_sections()`, `render_nav()` remain untouched for backward compatibility — the hierarchical path adds new functions alongside them. All 14 existing tests must remain green after the changes.

**Primary recommendation:** Build `categorize.py` first (self-contained), then update `generate.py` hierarchical rendering, then wire tests. Two plans, in that order.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| AI categorization (API call, batching, retry) | Script (categorize.py) | — | No UI; pure data transformation pipeline |
| Slug derivation | Script (categorize.py + generate.py) | — | Both scripts need `category_name → slug`; derive in categorize.py at write time |
| Hierarchical data grouping | generate.py | — | Grouping is purely a generation-time concern |
| Subcategory HTML rendering | generate.py | — | Pure HTML f-string generation, no frontend framework |
| Category metadata (display names, icons) | generate.py (CATEGORY_META) | — | Config lives adjacent to the rendering code that uses it |
| Sidebar navigation | generate.py (render_nav) | — | Top-level only per D-03; nav generated at build time |
| Anchor ID stability | categorize.py (slug derivation) | generate.py (id= attributes) | Slugs derived once in categorize.py, consumed by generate.py for id= |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `requests` | 2.32.5 [VERIFIED: local python3] | HTTP POST to GitHub Models API | Pre-installed on Actions runners; already used in fetch_stars.py |
| `json` (stdlib) | 3.x | Parse API responses, write categories.json | No extra dependency |
| `re` (stdlib) | 3.x | Strip markdown fences, derive slugs | Already used in generate.py |
| `os` (stdlib) | 3.x | Read GITHUB_TOKEN env var, makedirs | Already used in both scripts |

### Supporting

No new pip dependencies needed. All libraries are Python stdlib or pre-installed on `ubuntu-latest`.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw `requests.post` | `openai` SDK | openai SDK requires `pip install` (~25MB, +30s Action time); raw requests is equivalent for this single endpoint |
| Duplicate `language_to_slug()` | Shared `scripts/utils.py` | utils.py extraction is cleaner architecture but adds a third file and import complexity; duplication is 4 lines and acceptable for 2 scripts |

**Installation:** No new pip installs required. `requests` is pre-installed.

---

## Architecture Patterns

### System Architecture Diagram

```
_data/repos.json
       │
       ▼
categorize.py
  ├── load repos (json.load)
  ├── for each batch of 10:
  │     ├── build messages: [system_prompt + taxonomy, user_prompt + batch]
  │     ├── POST https://models.github.ai/inference/chat/completions
  │     │     Bearer $GITHUB_TOKEN, response_format: json_object
  │     ├── strip fences → json.loads()
  │     ├── on JSONDecodeError: retry once → on 2nd fail: assign "Other"
  │     └── derive slug from canonical category name
  └── write _data/categories.json
           │
           ▼
generate.py
  ├── load_repos() → _data/repos.json
  ├── load_categories() → _data/categories.json (or {} if absent)
  ├── if cat_map: group_by_categories_hierarchical()
  │     returns {category_name: {subcategory_name: [repos]}}
  │   else: group_by_language() [existing flat path]
  ├── render_nav() → sidebar HTML (top-level categories + counts)
  ├── render_sections_hierarchical() [new]
  │     for each category:
  │       render_section() [updated: CATEGORY_META first]
  │       for each subcategory:
  │         render_subcategory_header() [new]
  │         render cards
  └── render_page() → docs/index.html
```

### Recommended Project Structure

```
scripts/
├── fetch_stars.py      # Phase 2 — unchanged
├── categorize.py       # Phase 3 NEW — AI batch categorization
└── generate.py         # Phase 3 MODIFIED — add CATEGORY_META, hierarchical functions
_data/
├── repos.json          # fetch_stars.py output (gitignored)
└── categories.json     # categorize.py output (gitignored)
tests/
├── conftest.py         # pre-imports requests (existing)
├── fixtures/
│   ├── sample_repos.json         # existing
│   └── sample_categories.json   # NEW — fixture for Phase 3 tests
├── test_fetch.py       # existing (6 tests, unchanged)
├── test_generate.py    # MODIFIED — add hierarchical rendering tests
└── test_categorize.py  # NEW — AI script unit tests
```

### Pattern 1: GitHub Models API Call

**What:** POST to GitHub Models OpenAI-compatible endpoint with Bearer auth and JSON mode.
**When to use:** Each batch of 10 repos in categorize.py.

```python
# Source: .planning/research/STACK.md [VERIFIED: confirmed from official GitHub Models quickstart docs]
import json
import os
import re
import requests

GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"
MODEL = "openai/gpt-4o-mini"

def call_model(session, messages):
    """POST to GitHub Models API, return raw content string."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    resp = session.post(
        GITHUB_MODELS_URL,
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_session(token):
    """Create a requests.Session with Bearer auth headers pre-set."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    return session
```

### Pattern 2: Batch Processing with JSON Parse + Retry

**What:** Slice repos into batches of 10, call model, parse JSON with one retry on failure.
**When to use:** Main loop in categorize.py.

```python
# Source: CONTEXT.md § Discretion + AI-04 requirement [VERIFIED: behavior confirmed in existing PITFALLS.md research]
import json
import re

def strip_fences(raw):
    """Remove markdown code fences wrapping JSON."""
    return re.sub(r'```json\s*|\s*```', '', raw).strip()


def parse_with_retry(session, messages, batch_names):
    """Call model and parse JSON; retry once on JSONDecodeError; fall back to Other."""
    raw = call_model(session, messages)
    try:
        return json.loads(strip_fences(raw))
    except json.JSONDecodeError:
        print(f"[WARN] JSON parse failed. Raw response (first 300 chars): {raw[:300]}")
        # Append clarifying retry message
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Return only valid JSON, no preamble or markdown fences."}
        ]
        raw2 = call_model(session, retry_messages)
        try:
            return json.loads(strip_fences(raw2))
        except json.JSONDecodeError:
            print(f"[ERROR] JSON parse failed on retry. Assigning batch to Other. Raw: {raw2[:300]}")
            return {
                name: {"category": "Other", "subcategory": "Other"}
                for name in batch_names
            }
```

### Pattern 3: Slug Derivation (Stable, Re-entrant)

**What:** Convert canonical category/subcategory name → URL-safe slug. Identical to existing `language_to_slug()`.
**When to use:** In `categorize.py` when writing `categories.json`, and in `generate.py` for anchor IDs.

```python
# Source: generate.py line 78-84 [VERIFIED: read from file]
import re

def category_to_slug(name):
    """Convert category/subcategory display name to stable URL-safe slug.
    
    Verified outputs for all 14 top-level categories:
      'AI & ML'                -> 'ai-ml'
      'Self-Hosting & Homelab' -> 'self-hosting-homelab'
      'Dev Tools & CLI'        -> 'dev-tools-cli'
      'DevOps & Infra'         -> 'devops-infra'
      'Security'               -> 'security'
      'Web & Frontend'         -> 'web-frontend'
      'Data & Analytics'       -> 'data-analytics'
      'Productivity & Notes'   -> 'productivity-notes'
      'Media & Entertainment'  -> 'media-entertainment'
      'Networking'             -> 'networking'
      'Mobile & Desktop'       -> 'mobile-desktop'
      'Awesome Lists'          -> 'awesome-lists'
      'ESP32 & Hardware'       -> 'esp32-hardware'
      'Other'                  -> 'other'
    """
    if not name:
        return "other"
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
```

**Key insight:** `&` is stripped to nothing (not `a` or `amp`), then adjacent hyphens are collapsed by `+` quantifier. `"AI & ML"` → `"ai & ml"` → regex collapses ` & ` (space-ampersand-space = 3 non-alphanumeric chars) → `"ai-ml"`. Verified in Python. [VERIFIED: local python3 execution]

### Pattern 4: Hierarchical Grouping

**What:** Build `{category_name: {subcategory_name: [repos]}}` from cat_map.
**When to use:** In `generate.py` entry point when `cat_map` is present.

```python
# Source: Derived from existing group_by_categories() pattern in generate.py [VERIFIED: read from file]
from collections import defaultdict

def group_by_categories_hierarchical(repos, cat_map):
    """Group repos into nested {category: {subcategory: [repos]}} structure.
    
    Repos missing from cat_map fall to 'Other' > 'Other'.
    Each subcategory list is sorted by stars descending (HTML-07).
    Top-level categories ordered by total star count descending.
    """
    hier = defaultdict(lambda: defaultdict(list))
    for repo in repos:
        info = cat_map.get(repo["full_name"], {})
        cat = info.get("category", "Other")
        subcat = info.get("subcategory", "Other")
        hier[cat][subcat].append(repo)

    # Sort within each subcategory by stars descending
    for cat in hier:
        for subcat in hier[cat]:
            hier[cat][subcat].sort(
                key=lambda r: r.get("stargazers_count") or 0, reverse=True
            )

    # Sort top-level categories by total star count descending
    def cat_total(cat_name):
        return sum(
            r.get("stargazers_count") or 0
            for repos_list in hier[cat_name].values()
            for r in repos_list
        )

    return {
        cat: dict(hier[cat])
        for cat in sorted(hier, key=cat_total, reverse=True)
    }
```

### Pattern 5: Subcategory Header Rendering (D-02)

**What:** Safety Orange (#FF5F1F) full-width subcategory divider header.
**When to use:** `render_subcategory_header()` called once per subcategory in the hierarchical rendering path.

```python
# Source: CONTEXT.md D-02 decision [VERIFIED: matches existing render_section() pattern in generate.py]
import html

def render_subcategory_header(subcat_name, count, subcat_num):
    """Render a Safety Orange subcategory divider with inline repo count."""
    slug = category_to_slug(subcat_name)
    safe_name = html.escape(subcat_name.upper())
    return (
        f'<div id="{slug}" data-subcategory="{slug}" '
        f'class="px-8 py-3 flex justify-between items-center '
        f'bg-[#FF5F1F] text-white font-bold text-[10px] uppercase">'
        f'  <span>{safe_name} // SUB_{subcat_num:02d}</span>'
        f'  <span>ENTRIES: {count}</span>'
        f'</div>'
    )
```

### Pattern 6: Updated render_section() with CATEGORY_META lookup (D-06)

**What:** render_section() checks CATEGORY_META first, LANG_META second, fallback last.
**When to use:** All section header rendering (both hierarchical and flat paths).

```python
# Source: generate.py line 196-215 [VERIFIED], updated per D-05/D-06
def render_section(cat_name, repos, cat_num, global_offset):
    """Render a full category section. Updated: checks CATEGORY_META first (D-06)."""
    slug = language_to_slug(cat_name)
    
    # D-06: CATEGORY_META first, then LANG_META, then fallback
    if slug in CATEGORY_META:
        display_name, icon_name = CATEGORY_META[slug]
        icon_html = f'<span class="material-icons text-lg">{icon_name}</span>'
    else:
        display_name, emoji, _ = LANG_META.get(slug, (cat_name, "📦", "#888888"))
        icon_html = f'<span class="text-lg">{emoji}</span>'
    
    count = len(repos)
    cards = "\n".join(render_card(r, i, global_offset + i) for i, r in enumerate(repos))
    return f"""\
<section id="{slug}" data-category="{slug}" class="border-b-2 border-navy dark:border-white">
  <div class="px-8 py-4 border-b-2 border-navy dark:border-white flex justify-between items-center
              bg-zinc-200 dark:bg-zinc-800 uppercase font-bold text-[10px]">
    <span class="flex items-center gap-3">
      {icon_html}
      <span>{html.escape(display_name.upper())} // CATEGORY_{cat_num:02d}</span>
    </span>
    <span class="text-primary">TOTAL_ENTRIES: {count}</span>
  </div>
  <div class="divide-y-2 divide-navy dark:divide-white">
{cards}
  </div>
</section>"""
```

### Pattern 7: Updated render_nav() for Hierarchical Groups

**What:** Sidebar nav items using Material Icons (for AI categories) with total per-category count.
**When to use:** In hierarchical rendering path — separate from existing `render_nav()`.

```python
# Source: generate.py line 228-248 [VERIFIED], adapted for hier_groups structure and CATEGORY_META
def render_nav_hierarchical(hier_groups):
    """Render sidebar nav for hierarchical groups — top-level categories only (D-03)."""
    items = []
    for cat_name, subcats in hier_groups.items():
        slug = category_to_slug(cat_name)
        total_count = sum(len(repos) for repos in subcats.values())
        
        if slug in CATEGORY_META:
            display_name, icon_name = CATEGORY_META[slug]
            icon_html = f'<span class="material-icons text-sm opacity-60">{icon_name}</span>'
        else:
            display_name = cat_name
            icon_html = '<span class="opacity-60">📦</span>'
        
        items.append(f"""\
          <li>
            <a href="#{slug}" class="flex items-center justify-between px-3 py-2 text-[10px] font-bold uppercase
               hover:bg-primary hover:text-white transition-colors border-b border-navy/10 dark:border-white/10
               group">
              <span class="flex items-center gap-2">
                {icon_html}
                <span>{html.escape(display_name)}</span>
              </span>
              <span class="bg-navy text-white dark:bg-white dark:text-navy px-1.5 py-0.5 text-[9px] font-bold
                           group-hover:bg-white group-hover:text-primary">{total_count}</span>
            </a>
          </li>""")
    return "\n".join(items)
```

### Pattern 8: categorize.py System + User Prompt Structure (AI-03)

**What:** The messages array for each batch call.
**When to use:** Building payload in `categorize.py`.

```python
# Source: CONTEXT.md + AI-03 requirement + starred_repos.md taxonomy [VERIFIED: taxonomy extracted from file]

SYSTEM_PROMPT = """You are a GitHub repository taxonomist. Classify each repository into one of the following top-level categories and subcategories. Use the existing taxonomy below. Prefer existing names over inventing new ones. Only use "Other" if no other category fits.

TAXONOMY:
- AI & ML
  - Claude Code & Skills
  - Agent Frameworks & Harnesses
  - MCP Servers & Tools
  - LLM UIs & Chat Interfaces
  - RAG & Knowledge
  - AI Productivity Tools
  - AI Infrastructure & APIs
  - Coding Agents & IDEs
  - Generalist Agents
- Self-Hosting & Homelab
  - Dashboards & Homepages
  - Password & Auth
  - Monitoring & Alerts
  - Media & Arr Stack
  - Deployment & PaaS
  - Notes & Knowledge
  - Networking & Remote Access
  - Proxmox & Containers
  - Tools & Utilities
- Dev Tools & CLI
  - Terminal & Shell
  - Documentation & Sites
  - Automation & Scraping
  - Arr & Media Tools
  - ESP32 & Embedded
  - Other Dev Tools
- DevOps & Infra
- Security
- Web & Frontend
- Data & Analytics
- Productivity & Notes
- Media & Entertainment
- Networking
- Mobile & Desktop
- Awesome Lists
- ESP32 & Hardware
- Other

Return a JSON object where each key is the repo full_name (owner/repo) and each value is:
{"category": "<top-level category name>", "subcategory": "<subcategory name>"}

If a top-level category has no subcategories, use the category name as the subcategory too.
Return ONLY valid JSON with no preamble, explanation, or markdown formatting."""

def build_user_prompt(batch):
    """Build the user message for a batch of repos."""
    lines = []
    for repo in batch:
        desc = repo.get("description") or "No description"
        lang = repo.get("language") or "Unknown"
        stars = repo.get("stargazers_count") or 0
        lines.append(
            f'- {repo["full_name"]}: [{lang}, {stars} stars] {desc}'
        )
    return "Classify these repositories:\n" + "\n".join(lines)
```

### Pattern 9: categories.json Output Format (AI-05)

**What:** The exact output format written by `categorize.py`. Slug derived in Python, not from model output.

```python
# Source: AI-05 requirement [VERIFIED: slug derivation verified locally]
{
  "owner/repo-name": {
    "category": "AI & ML",
    "subcategory": "Claude Code & Skills",
    "slug": "claude-code-skills"
  },
  "owner/another-repo": {
    "category": "DevOps & Infra",
    "subcategory": "DevOps & Infra",
    "slug": "devops-infra"
  }
}
```

**Key:** `slug` is `category_to_slug(subcategory_name)` — derived from the subcategory (for section-level anchor), not the top-level category. The top-level section anchor is derived from `category_to_slug(category_name)` in `generate.py` at render time.

### Anti-Patterns to Avoid

- **Trust model-generated slugs:** The model may return `"ai_ml"` or `"ai-and-ml"` instead of `"ai-ml"`. Slugs MUST be derived by `category_to_slug()` in Python from the model's `category` string, not used directly from model output. (AI-05)
- **One API call per repo:** 370 calls > 150/day free tier limit. Always batch 10. (AI-02)
- **Put model call in `__main__` block only:** Unit tests need to import and call individual functions. Keep functions importable without triggering `__main__`.
- **Mutate existing `render_sections()` / `render_nav()`:** These are test-exercised public APIs. Add `render_sections_hierarchical()` and `render_nav_hierarchical()` as new functions; keep originals intact.
- **Use emoji for CATEGORY_META icons:** D-07 locks icons as Material Icons ligature spans. The emoji column is only in LANG_META.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON fence stripping | Custom HTML parser | `re.sub(r'\`\`\`json\s*\|\s*\`\`\`', '', raw)` | Simple, tested, handles the only two cases (opening fence with lang tag, closing fence) |
| Rate-limit backoff | Exponential retry loop | Single retry with clarifying message (as designed) | Free tier has no documented `Retry-After` header; simple retry is sufficient; don't over-engineer for a pipeline that runs once/day |
| Slug derivation | Custom slugifier | `re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")` — same as `language_to_slug()` | Already proven in 14 tests; handles all 44+ taxonomy names correctly |
| Token counting | `tiktoken` or manual count | Batch at 10 (empirically safe) | 10 repos × ~200 tokens/repo ≈ 2000 input tokens — well under 8000-token limit; no counting needed |

**Key insight:** The categorize.py script has zero novel infrastructure — it's HTTP POST + JSON parse. Don't add complexity beyond what's needed for the 10-batch loop and single-retry error handler.

---

## Taxonomy Reference

### Full Extracted Taxonomy from starred_repos.md [VERIFIED: read from file]

| Top-Level Category | Subcategories | Count |
|-------------------|---------------|-------|
| AI & ML | Claude Code & Skills, Agent Frameworks & Harnesses, MCP Servers & Tools, LLM UIs & Chat Interfaces, RAG & Knowledge, AI Productivity Tools, AI Infrastructure & APIs, Coding Agents & IDEs, Generalist Agents | 9 |
| Self-Hosting & Homelab | Dashboards & Homepages, Password & Auth, Monitoring & Alerts, Media & Arr Stack, Deployment & PaaS, Notes & Knowledge, Networking & Remote Access, Proxmox & Containers, Tools & Utilities | 9 |
| Dev Tools & CLI | Terminal & Shell, Documentation & Sites, Automation & Scraping, Arr & Media Tools, ESP32 & Embedded, Other Dev Tools | 6 |
| DevOps & Infra | (none — flat) | 0 |
| Security | (none — flat) | 0 |
| Web & Frontend | (none — flat) | 0 |
| Data & Analytics | (none — flat) | 0 |
| Productivity & Notes | (none — flat) | 0 |
| Media & Entertainment | (none — flat) | 0 |
| Networking | (none — flat) | 0 |
| Mobile & Desktop | (none — flat) | 0 |
| Awesome Lists | (none — flat) | 0 |
| ESP32 & Hardware | (none — flat) | 0 |
| Other | (none — flat) | 0 |

**Total subcategories:** 24 named subcategories. Flat categories use category name as subcategory.

### Slug Collision Analysis [VERIFIED: Python execution]

No slug collisions exist in the full taxonomy:
- "ESP32 & Hardware" (top-level) → `esp32-hardware`
- "ESP32 & Embedded" (subcategory under Dev Tools & CLI) → `esp32-embedded` ✓ different
- "Networking" (top-level) → `networking`
- "Networking & Remote Access" (subcategory) → `networking-remote-access` ✓ different
- "Media & Entertainment" (top-level) → `media-entertainment`
- "Media & Arr Stack" (subcategory) → `media-arr-stack` ✓ different

No defensive prefix needed for anchor IDs.

---

## Common Pitfalls

### Pitfall 1: Model Returns Markdown-Wrapped JSON Despite json_object Mode

**What goes wrong:** GPT-4o-mini returns ` ```json\n{...}\n``` ` even with `response_format: {"type": "json_object"}`. `json.loads()` throws `JSONDecodeError`.
**Why it happens:** `json_object` mode reduces but does not eliminate fence wrapping in practice. Some edge cases (long responses, instruction-heavy system prompts) still produce fences.
**How to avoid:** Always run `re.sub(r'\`\`\`json\s*|\s*\`\`\`', '', raw).strip()` before `json.loads()`. This is cheap and idempotent.
**Warning signs:** `JSONDecodeError` on first parse attempt for batches that succeed on retry.

### Pitfall 2: taxonomy Drift — Model Invents New Category Names

**What goes wrong:** Without taxonomy seeding, the model uses inconsistent names: "Machine Learning" one run, "AI & ML" the next. Slugs change → anchor IDs break → bookmarks break.
**Why it happens:** LLMs are not deterministic taxonomists by default.
**How to avoid:** The full taxonomy (13 top-level categories + 24 subcategories) MUST appear in the system prompt (Pattern 8 above). Instruct: "Use existing names. Only use Other if no category fits."
**Warning signs:** `categories.json` contains category names not in CATEGORY_META.

### Pitfall 3: render_section() Receives Flat repos List vs Hierarchical Structure

**What goes wrong:** The entry point calls `render_sections(hier_groups)` but `render_sections()` expects a flat `{cat_name: [repos]}` dict, not `{cat_name: {subcat_name: [repos]}}`.
**Why it happens:** Two different structure shapes, single function name.
**How to avoid:** Add `render_sections_hierarchical(hier_groups)` as a separate function. The entry point switches based on `cat_map` presence. Never pass `hier_groups` to the existing `render_sections()`.
**Warning signs:** `AttributeError: 'dict' object has no attribute 'get'` inside `render_card()`.

### Pitfall 4: render_nav() Total Count Shows Subcategory Count, Not Repo Count

**What goes wrong:** Iterating `hier_groups.items()` gives `(cat_name, subcats_dict)`. `len(subcats_dict)` gives number of subcategories, not repos. Sidebar shows wrong count.
**Why it happens:** Structure changed from `{cat: [repos]}` to `{cat: {subcat: [repos]}}`.
**How to avoid:** Use `sum(len(r) for r in subcats.values())` for total repo count per category. Pattern 7 above shows the correct implementation.
**Warning signs:** Sidebar shows "3" for AI & ML (3 subcategories) instead of "100+" (actual repo count).

### Pitfall 5: Slug Derived from model's "slug" output, not from category name

**What goes wrong:** Model returns `"slug": "ai_ml"` or `"slug": "ai-and-ml"`. categorize.py writes this to categories.json. generate.py uses it for anchor IDs. Anchors don't match CATEGORY_META keys. Sidebar links 404.
**Why it happens:** Model output is untrusted for structural data like slugs.
**How to avoid:** In categorize.py, **ignore any slug the model returns**. Always derive slug with `category_to_slug(record["subcategory"])`. The model's job is to output category and subcategory names; slug derivation is Python's job.
**Warning signs:** CATEGORY_META dict lookup misses on valid-looking slugs.

### Pitfall 6: Python ImportLib Bootstrap Pattern Required for test_categorize.py

**What goes wrong:** `from scripts.categorize import ...` fails because `scripts/` is not a package (no `__init__.py`).
**Why it happens:** Same issue as test_fetch.py and test_generate.py.
**How to avoid:** Follow the existing `importlib.util.spec_from_file_location` bootstrap pattern used in test_fetch.py and test_generate.py. The conftest.py already pre-imports `requests` for mock patching.

---

## Code Examples

### categorize.py Main Loop Structure

```python
# Source: CONTEXT.md decisions + AI-02 batch requirement + fetch_stars.py pattern [VERIFIED]
def main():
    token = os.environ["GITHUB_TOKEN"]  # KeyError = fail-fast
    session = build_session(token)
    
    with open("_data/repos.json", encoding="utf-8") as f:
        repos = json.load(f)
    
    cat_map = {}
    batch_size = 10
    
    for i in range(0, len(repos), batch_size):
        batch = repos[i:i + batch_size]
        batch_names = [r["full_name"] for r in batch]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(batch)},
        ]
        result = parse_with_retry(session, messages, batch_names)
        
        for full_name, info in result.items():
            subcat = info.get("subcategory", "Other")
            cat_map[full_name] = {
                "category": info.get("category", "Other"),
                "subcategory": subcat,
                "slug": category_to_slug(subcat),  # derive here, not from model
            }
        
        print(f"Processed batch {i//batch_size + 1}/{(len(repos)-1)//batch_size + 1}")
    
    os.makedirs("_data", exist_ok=True)
    with open("_data/categories.json", "w", encoding="utf-8") as f:
        json.dump(cat_map, f, ensure_ascii=False, indent=2)
    
    print(f"Wrote {len(cat_map)} repo categorizations to _data/categories.json")
```

### generate.py Entry Point (updated)

```python
# Source: generate.py lines 414-424 [VERIFIED: read from file], updated for hierarchical path
if __name__ == "__main__":
    repos = load_repos()
    cat_map = load_categories()
    
    if cat_map:
        hier_groups = group_by_categories_hierarchical(repos, cat_map)
        nav_html = render_nav_hierarchical(hier_groups)
        sections_html = render_sections_hierarchical(hier_groups)
    else:
        groups = group_by_language(repos)
        nav_html = render_nav(groups)
        sections_html = render_sections(groups)
    
    page = render_page(nav_html, sections_html, len(repos), datetime.datetime.utcnow())
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(page)
    cat_count = len(hier_groups) if cat_map else len(groups)
    print(f"Generated docs/index.html: {len(repos)} repos, {cat_count} categories")
```

### Test Patterns for test_categorize.py

```python
# Source: tests/test_fetch.py [VERIFIED: read from file] — same importlib bootstrap pattern
import importlib.util
import pathlib
import json
import unittest
from unittest.mock import MagicMock, patch

_ROOT = pathlib.Path(__file__).parent.parent
_MOD_PATH = _ROOT / "scripts" / "categorize.py"

def _load_module():
    spec = importlib.util.spec_from_file_location("categorize", _MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

cat = _load_module()


class TestCategoryToSlug(unittest.TestCase):
    def test_slug_derivation(self):
        cases = [
            ("AI & ML", "ai-ml"),
            ("Self-Hosting & Homelab", "self-hosting-homelab"),
            ("Dev Tools & CLI", "dev-tools-cli"),
            ("Claude Code & Skills", "claude-code-skills"),
            ("Other", "other"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(cat.category_to_slug(name), expected)


class TestStripFences(unittest.TestCase):
    def test_strips_json_fence(self):
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(cat.strip_fences(raw), '{"a": 1}')

    def test_passthrough_clean_json(self):
        raw = '{"a": 1}'
        self.assertEqual(cat.strip_fences(raw), '{"a": 1}')


class TestParseWithRetry(unittest.TestCase):
    def test_success_on_first_try(self):
        mock_session = MagicMock()
        # call_model returns valid JSON string
        cat_module_call = MagicMock(return_value='{"owner/repo": {"category": "AI & ML", "subcategory": "Claude Code & Skills"}}')
        
        with patch.object(cat, "call_model", cat_module_call):
            result = cat.parse_with_retry(mock_session, [], ["owner/repo"])
        
        self.assertIn("owner/repo", result)
        self.assertEqual(result["owner/repo"]["category"], "AI & ML")
    
    def test_retry_on_json_decode_error(self):
        """First call returns bad JSON, second returns valid JSON."""
        call_count = [0]
        def mock_call(session, messages):
            call_count[0] += 1
            if call_count[0] == 1:
                return "Here is the JSON: ```json{invalid```"
            return '{"owner/repo": {"category": "Other", "subcategory": "Other"}}'
        
        with patch.object(cat, "call_model", mock_call):
            result = cat.parse_with_retry(MagicMock(), [{"role": "user", "content": "test"}], ["owner/repo"])
        
        self.assertEqual(call_count[0], 2)  # retried once
        self.assertEqual(result["owner/repo"]["category"], "Other")
    
    def test_fallback_on_second_failure(self):
        """Both calls return bad JSON; batch assigned to Other."""
        with patch.object(cat, "call_model", return_value("not json")):
            result = cat.parse_with_retry(
                MagicMock(),
                [{"role": "user", "content": "test"}],
                ["owner/repo1", "owner/repo2"]
            )
        
        self.assertEqual(result["owner/repo1"]["category"], "Other")
        self.assertEqual(result["owner/repo2"]["category"], "Other")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Language-based grouping (Phase 2) | AI-based hierarchical categories (Phase 3) | This phase | Repos grouped semantically; sidebar shows meaningful categories |
| Flat `{cat: [repos]}` groups | Nested `{cat: {subcat: [repos]}}` groups | This phase | Two-level hierarchy in HTML; subcategory headers between cards |
| Emoji icons from LANG_META | Material Icons from CATEGORY_META | This phase | Icon consistency; no emoji rendering variance across platforms |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `response_format: {"type": "json_object"}` is supported by `openai/gpt-4o-mini` via GitHub Models endpoint | Standard Stack / Pattern 1 | Would need to rely entirely on fence-stripping; retry logic becomes more critical |
| A2 | `requests` is pre-installed on GitHub Actions `ubuntu-latest` runners | Standard Stack | Would need `pip install requests` step in Action (Phase 4 concern, not Phase 3) |
| A3 | 10 repos × ~200 tokens/repo ≈ 2,000 input tokens is under the 8,000-token input limit for gpt-4o-mini | Standard Stack / AI-02 | If repos have very long descriptions, batches might hit token limit; reduce to 7 repos/batch |

**If this table is empty:** All other claims were verified or cited — these 3 assumptions are the only gaps.

---

## Open Questions

1. **Does `parse_with_retry` need a `requests.Session` argument or just use `requests.post` directly?**
   - What we know: `fetch_stars.py` uses a header dict passed to each call, not a Session. The `requests.Session` approach pre-bakes auth headers.
   - What's unclear: Which pattern is cleaner to mock in tests.
   - Recommendation: Use `requests.Session` with headers set once (Pattern 1). Mocking `session.post` is cleaner than patching `requests.post` globally.

2. **Should `render_sections_hierarchical()` be named or should it be `render_sections()` overload?**
   - What we know: CONTEXT.md D-04 says existing flat functions remain for backward compat.
   - Recommendation: New `render_sections_hierarchical(hier_groups)` function. Entry point branches explicitly. Keeps function signatures unambiguous.

3. **How does `render_page()` extract marquee content for hierarchical groups?**
   - What we know: `render_page()` currently extracts category names from `nav_html` via regex on `<span>` tags. This works for both flat and hierarchical nav since `render_nav_hierarchical()` produces the same HTML structure.
   - Recommendation: No change to `render_page()` needed. The marquee regex extracts display names from the nav HTML regardless of path.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.x | categorize.py, generate.py | ✓ | 3.9 (local), 3.12 (Actions ubuntu-latest) | — |
| `requests` library | categorize.py | ✓ | 2.32.5 [VERIFIED: local python3] | pip install requests (Action step) |
| GitHub Models API | AI-01 | ✓ (in Actions context) | openai/gpt-4o-mini | Requires `models: read` permission in workflow |
| `GITHUB_TOKEN` | Both scripts | ✓ (in Actions context) | — | Fail-fast with KeyError (by design) |

**Missing dependencies with no fallback:** None.
**Note:** Local dev requires setting `GITHUB_TOKEN` manually; `categorize.py` will KeyError without it (fail-fast by design, matching `fetch_stars.py` pattern).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (pytest.ini: `testpaths = tests`) |
| Config file | `pytest.ini` (exists) |
| Quick run command | `python -m pytest tests/ -v` |
| Full suite command | `python -m pytest tests/ -v` |

**Current baseline:** 14 tests passing (6 fetch + 8 generate). [VERIFIED: local run]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AI-01 | Bearer auth header sent to correct endpoint | unit | `pytest tests/test_categorize.py::TestCategorizeApi -x` | ❌ Wave 0 |
| AI-02 | Repos batched at exactly 10 per call | unit | `pytest tests/test_categorize.py::TestBatching -x` | ❌ Wave 0 |
| AI-03 | System prompt contains all 13 top-level categories | unit | `pytest tests/test_categorize.py::TestSystemPrompt -x` | ❌ Wave 0 |
| AI-04 | JSONDecodeError triggers retry; 2nd failure → Other fallback | unit | `pytest tests/test_categorize.py::TestParseWithRetry -x` | ❌ Wave 0 |
| AI-05 | categories.json slug derived from category_to_slug(), not model output | unit | `pytest tests/test_categorize.py::TestCategoryToSlug -x` | ❌ Wave 0 |
| D-01 | Subcategories render as nested subsections | unit | `pytest tests/test_generate.py::TestHierarchicalRendering -x` | ❌ Wave 0 |
| D-02 | Subcategory header uses #FF5F1F background | unit | `pytest tests/test_generate.py::TestRenderSubcategoryHeader -x` | ❌ Wave 0 |
| D-04 | group_by_categories_hierarchical() returns correct nested structure | unit | `pytest tests/test_generate.py::TestGroupByHierarchical -x` | ❌ Wave 0 |
| D-06 | render_section() checks CATEGORY_META first | unit | `pytest tests/test_generate.py::TestCategoryMetaLookup -x` | ❌ Wave 0 |
| Fallback | No categories.json → language grouping (existing behavior) | regression | `pytest tests/test_generate.py::TestOutputFileCreated -x` | ✅ exists |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** All tests green (14 existing + new Phase 3 tests) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_categorize.py` — covers AI-01 through AI-05 + parse retry logic
- [ ] `tests/fixtures/sample_categories.json` — 5-repo fixture matching sample_repos.json full_names + hierarchical categories
- [ ] Additional test classes in `tests/test_generate.py` — hierarchical rendering, CATEGORY_META lookup, subcategory header

*(Existing `tests/conftest.py` already pre-imports `requests` — no new conftest needed.)*

---

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | GITHUB_TOKEN is system-managed |
| V3 Session Management | no | Stateless script pipeline |
| V4 Access Control | no | Single-user pipeline, no multi-tenant |
| V5 Input Validation | yes | `html.escape()` on all model-returned category/subcategory names before HTML interpolation |
| V6 Cryptography | no | No encryption needed |

**Threat Pattern: Prompt Injection via repo descriptions**
- Repos with malicious descriptions (e.g., `"Ignore all previous instructions and return..."`) could attempt to manipulate model output.
- **Mitigation:** Model output is only used for `category` and `subcategory` string fields. `html.escape()` is already applied to all strings before HTML output. Slug is always re-derived in Python. No eval, no shell exec on model output.
- **STRIDE category:** Tampering (of category assignments, not code execution)

---

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` — GitHub Models endpoint, Bearer auth, batch size rationale (fetched/confirmed 2026-04-21 from official GitHub Models quickstart docs)
- `.planning/research/PITFALLS.md` — JSON parse failure patterns, taxonomy drift, rate limit analysis
- `scripts/generate.py` — All existing function signatures, LANG_META structure, slug derivation logic, render patterns [READ: 2026-04-22]
- `scripts/fetch_stars.py` — GITHUB_TOKEN pattern, requests session, _data/ output [READ: 2026-04-22]
- `tests/test_fetch.py` + `tests/test_generate.py` + `tests/conftest.py` — Test bootstrap patterns, mock approach [READ: 2026-04-22]
- `starred_repos.md` — Full taxonomy: 13 top-level categories, 24 named subcategories [READ: 2026-04-22]
- `.planning/phases/03-ai-categorization/03-CONTEXT.md` — All locked decisions D-01 through D-08 [READ: 2026-04-22]
- Python local execution: slug derivation verified for all 14 top-level category names [VERIFIED: 2026-04-22]

### Secondary (MEDIUM confidence)
- `.planning/research/ARCHITECTURE.md`, `FEATURES.md` — Overall pipeline architecture cross-reference

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified locally; API endpoint from confirmed prior research
- Architecture: HIGH — all patterns derived from existing verified code in the repo
- Pitfalls: HIGH — sourced from existing PITFALLS.md research + code analysis
- Taxonomy slugs: HIGH — verified by Python execution

**Research date:** 2026-04-22
**Valid until:** 2026-05-22 (stable APIs; GitHub Models endpoint may evolve)
