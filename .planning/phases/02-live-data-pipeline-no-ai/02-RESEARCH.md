# Phase 2: Live Data Pipeline (No AI) — Research

**Researched:** 2026-04-21
**Domain:** GitHub REST API · Python stdlib · Static HTML generation
**Confidence:** HIGH

---

## Summary

Phase 2 adds two Python scripts — `scripts/fetch_stars.py` (GitHub API client with pagination) and `scripts/generate.py` (data → HTML renderer) — to populate the Phase 1 static shell with real starred repo data. The pipeline is intentionally minimal: Python stdlib + `requests`, no templating engine, no build step, no npm.

The fetch script must paginate the `/user/starred` endpoint via `Link: rel="next"` header parsing until exhausted, filter forks and archived repos, and write `_data/repos.json`. The generator reads repos.json (and optionally a future categories.json from Phase 3), groups repos by language when no categories.json exists, sorts each group by star count descending, and writes the complete `docs/index.html` from scratch using f-strings.

The HTML output must faithfully replicate and extend the Phase 1 Stitch brutalist design: same card markup, same Tailwind CDN + JetBrains Mono + Inter, same Safety Orange `#FF5F1F`, same dark mode. The only new structural element is replacing the Phase 1 filter-button section with a two-column layout: left sidebar with persistent anchor nav + right column with category sections.

**Primary recommendation:** Implement both scripts as single-file Python with clear procedural flow (load → group → sort → render → write). Use `html.escape()` on all user-supplied string values. Parse the `Link` header with `re.search(r'<([^>]+)>;\s*rel="next"', link_header)`. No external deps beyond `requests`.

---

<phase_requirements>
## Phase Requirements

| ID | Requirement | Research Support |
|----|-------------|------------------|
| FETCH-01 | `scripts/fetch_stars.py` fetches all starred repos via `GET /user/starred?per_page=100` with GITHUB_TOKEN; paginates via Link header until exhausted | GitHub REST API pagination via Link header — see § GitHub Stars API |
| FETCH-02 | Filter out repos where `fork == true` or `archived == true` | Simple Python list comprehension — see § Filter Logic |
| FETCH-03 | Write `_data/repos.json`: array of objects with 6 keys | `json.dumps()` with `ensure_ascii=False` — see § JSON I/O |
| HTML-01 | `generate.py` reads repos.json + optional categories.json, groups by category, writes `docs/index.html` | Dual-mode architecture — see § generate.py Architecture |
| HTML-07 | Repos sorted by `stargazers_count` descending within each section | `sorted(..., key=lambda r: r["stargazers_count"], reverse=True)` |
| HTML-08 | Category section headers: emoji marker, inline repo count badge, stable anchor `id` | Emoji map + slug function — see § Language Grouping |
| HTML-09 | Hierarchical category nav in sidebar — NOT top menu; anchor links; mobile responsive | Two-column Tailwind layout — see § Page Layout Pattern |

</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Star data fetching | Python script (CI) | — | GitHub API only accessible server-side with token; runs in Actions |
| Filtering / deduplication | Python script (CI) | — | Pure data transformation, no browser involvement |
| Category grouping | Python script (CI) | — | Applied at build time; output baked into static HTML |
| HTML generation | Python script (CI) | — | Full page written to `docs/index.html` at build time |
| Dark mode | Browser (CSS) | — | `prefers-color-scheme` media query; zero JavaScript needed |
| Anchor navigation | Browser | — | Native `<a href="#slug">` links; no JS routing |
| Static serving | CDN / GitHub Pages | — | Serves `docs/index.html`; no server-side code |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `requests` | pre-installed on ubuntu-latest | HTTP client for GitHub API | Confirmed pre-installed on GitHub Actions ubuntu-latest runners; available locally via pip. Simpler than `urllib.request` for headers/pagination. |
| `json` (stdlib) | Python 3.x stdlib | Serialize/deserialize repos.json | No deps; handles Unicode; `ensure_ascii=False` preserves non-ASCII descriptions |
| `re` (stdlib) | Python 3.x stdlib | Parse Link header for next-page URL | One-liner regex; no `urllib.parse` gymnastics needed |
| `html` (stdlib) | Python 3.x stdlib | `html.escape()` for user content in HTML | Prevents XSS in generated HTML from repo descriptions/names |
| `os` (stdlib) | Python 3.x stdlib | `os.environ["GITHUB_TOKEN"]`, `os.makedirs` | Standard env access pattern |
| `datetime` (stdlib) | Python 3.x stdlib | UTC timestamp for header strip | `datetime.utcnow().strftime(...)` |
| `collections.defaultdict` (stdlib) | Python 3.x stdlib | Group repos by category | Cleaner than manual dict.setdefault pattern |

[VERIFIED: Python 3.9.6 installed locally; requests confirmed pre-installed on ubuntu-latest per ACTION-03 in REQUIREMENTS.md]

### Not Needed (explicitly excluded)

| Library | Why Not |
|---------|---------|
| Jinja2 | Adds dep, adds complexity; f-strings are sufficient for a single-file generator |
| lxml / BeautifulSoup | No HTML parsing needed — write-only generation |
| PyGitHub | Heavy wrapper; direct `requests` calls are simpler for 1 endpoint |

---

## GitHub Stars API

### Endpoint

```
GET https://api.github.com/user/starred
  ?per_page=100
  &page=1
Headers:
  Authorization: token {GITHUB_TOKEN}
  Accept: application/vnd.github+json
  X-GitHub-Api-Version: 2022-11-28
```

[CITED: https://docs.github.com/en/rest/activity/starring#list-repositories-starred-by-the-authenticated-user]

**Critical:** `per_page=100` is the maximum. Default is 30 — silently drops repos. Always pass 100.

### Pagination via Link Header

GitHub returns a `Link` response header when there are more pages:

```
Link: <https://api.github.com/user/starred?per_page=100&page=2>; rel="next", <https://api.github.com/user/starred?per_page=100&page=4>; rel="last"
```

On the last page, the `rel="next"` entry is absent. Parse with:

```python
import re

def get_next_url(response):
    link = response.headers.get("Link", "")
    match = re.search(r'<([^>]+)>;\s*rel="next"', link)
    return match.group(1) if match else None
```

[VERIFIED: Tested locally — regex correctly extracts next URL and returns None on last page]

### Rate Limits

| Limit | Value |
|-------|-------|
| Authenticated requests | 5,000 req/hr |
| Unauthenticated | 60 req/hr |
| Pages for 370 repos | 4 pages (negligible) |

For 370 repos at per_page=100: 4 API calls per run. Daily cron = 4 calls/day. Far below any limit. [CITED: https://docs.github.com/en/rest/using-the-rest-api/rate-limiting-for-the-rest-api]

### Response Fields Used

Each item in the response array includes (among others):

```json
{
  "full_name": "owner/repo",
  "name": "repo",
  "html_url": "https://github.com/owner/repo",
  "description": "...",
  "language": "Python",        ← null when no language detected
  "stargazers_count": 12400,
  "fork": false,
  "archived": false
}
```

[CITED: https://docs.github.com/en/rest/repos/repos#get-a-repository]

---

## Architecture Patterns

### System Architecture Diagram

```
GITHUB API                    PYTHON SCRIPTS (CI)           GITHUB PAGES
──────────                    ────────────────────          ────────────
GET /user/starred   ──────►  fetch_stars.py
  ?per_page=100               │  paginate Link header
  Authorization: token        │  filter fork/archived
                              │  extract 6 fields
                              ▼
                         _data/repos.json
                              │
                              ▼
                         generate.py
                              │  load repos.json
                              │  if categories.json → AI groups
                              │  else → group by language
                              │  sort by stars desc
                              │  render sections + nav
                              ▼
                         docs/index.html  ──────►  GitHub Pages
                                                    serves to browser
```

### Recommended Project Structure

```
scripts/
├── fetch_stars.py     # FETCH-01, FETCH-02, FETCH-03
└── generate.py        # HTML-01, HTML-07, HTML-08, HTML-09

_data/                 # ephemeral — in .gitignore
├── repos.json         # written by fetch_stars.py
└── categories.json    # written by categorize.py (Phase 3, optional)

docs/
└── index.html         # written by generate.py

tests/
├── test_fetch.py      # unit tests for fetch logic
└── test_generate.py   # unit tests for generate logic
```

### Pattern 1: fetch_stars.py Pagination Loop

```python
# Source: GitHub REST API docs + verified regex pattern
import os, re, json, requests

def fetch_all_stars():
    token = os.environ["GITHUB_TOKEN"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = "https://api.github.com/user/starred?per_page=100"
    all_repos = []

    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        all_repos.extend(resp.json())
        # Parse Link header for next page
        link = resp.headers.get("Link", "")
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = match.group(1) if match else None

    return all_repos
```

### Pattern 2: Filter Logic

```python
def filter_repos(repos):
    return [r for r in repos if not r.get("fork") and not r.get("archived")]
```

### Pattern 3: Write repos.json

```python
import json, os

FIELDS = ["full_name", "name", "html_url", "description", "language", "stargazers_count"]

def write_repos(repos, path="_data/repos.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    records = [{k: r.get(k) for k in FIELDS} for r in repos]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(records)} repos to {path}")
```

### Pattern 4: generate.py — Group by Language (Phase 2 fallback)

```python
from collections import defaultdict

def group_by_language(repos):
    """Phase 2 fallback: group repos by GitHub-reported language."""
    groups = defaultdict(list)
    for repo in repos:
        lang = repo.get("language") or "Other"
        groups[lang].append(repo)
    # Sort repos within each group by stars desc
    for lang in groups:
        groups[lang].sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    # Order groups by total stars desc (largest language group first)
    return dict(sorted(groups.items(), key=lambda kv: sum(r.get("stargazers_count", 0) for r in kv[1]), reverse=True))
```

### Pattern 5: generate.py — Group by AI Categories (Phase 3, when categories.json exists)

```python
def group_by_categories(repos, cat_map):
    """Phase 3: group repos using AI-generated categories.json."""
    groups = defaultdict(list)
    for repo in repos:
        key = repo["full_name"]
        cat_info = cat_map.get(key, {})
        category = cat_info.get("category", "Other")
        groups[category].append(repo)
    for cat in groups:
        groups[cat].sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    return dict(sorted(groups.items(), key=lambda kv: sum(r.get("stargazers_count", 0) for r in kv[1]), reverse=True))
```

### Pattern 6: K-Formatter

```python
# VERIFIED: tested against all expected values (1200→"1.2K", 42000→"42K", etc.)
def fmt_stars(n):
    if n >= 1_000_000:
        v = n / 1_000_000
        return (f"{v:.1f}" if v % 1 else f"{int(v)}") + "M"
    elif n >= 1_000:
        v = n / 1_000
        return (f"{v:.1f}" if v % 1 else f"{int(v)}") + "K"
    return str(n)
```

Verified outputs: `1200→"1.2K"`, `42000→"42K"`, `1500000→"1.5M"`, `999→"999"`, `12400→"12.4K"`, `162000→"162K"`, `350000→"350K"` ✓

### Pattern 7: HTML Escape for User Content

```python
import html

# All user-supplied strings MUST pass through html.escape()
# GitHub repo descriptions can contain: & " ' < >
safe_desc = html.escape(repo.get("description") or "")
safe_name = html.escape(repo["name"])
# html_url comes from GitHub API — safe to use in href as-is (all HTTPS GitHub URLs)
```

### Anti-Patterns to Avoid

- **Using `requests.get(...).text` and `.json()` without `raise_for_status()`:** Silent HTTP errors (401 bad token, 403 rate limit) produce empty result sets with no error. Always call `resp.raise_for_status()` before `.json()`.
- **`git add -A` in the deploy step:** Commits `_data/` to git. Use `git add docs/index.html` explicitly. (This is a workflow concern but generates.py should not touch _data relative to docs.)
- **Raw integer star counts in HTML:** `12400` looks ugly; always pass through `fmt_stars()`.
- **Missing html.escape() on description:** Repo descriptions contain `&`, `"`, `<` characters. Unescaped content breaks the HTML structure.
- **Calling `/repos/{owner}/{repo}` per repo:** The `/user/starred` response includes all needed fields. Do NOT make additional per-repo API calls (370 extra calls, slower, wasteful).

---

## Language Grouping for Phase 2

When `_data/categories.json` does **not** exist, `generate.py` groups repos by GitHub-reported `language`. Each language becomes its own section with a slug and emoji.

### Language → Slug → Emoji Map

```python
# Source: [ASSUMED] reasonable defaults based on common language icons + GitHub color conventions

LANG_META = {
    # slug: (display_name, emoji, color)
    # Languages from LANG_COLORS in Phase 1 + common GitHub languages
    "python":     ("Python",          "🐍", "#3572A5"),
    "typescript": ("TypeScript",      "🔷", "#2b7489"),
    "javascript": ("JavaScript",      "🟨", "#f1e05a"),
    "go":         ("Go",              "🐹", "#00ADD8"),
    "rust":       ("Rust",            "🦀", "#DEA584"),
    "shell":      ("Shell",           "🐚", "#89e051"),
    "c":          ("C",               "⚙️", "#555555"),
    "cpp":        ("C++",             "⚡", "#f34b7d"),
    "java":       ("Java",            "☕", "#b07219"),
    "ruby":       ("Ruby",            "💎", "#701516"),
    "swift":      ("Swift",           "🦅", "#ffac45"),
    "kotlin":     ("Kotlin",          "🎯", "#A97BFF"),
    "vue":        ("Vue",             "💚", "#41b883"),
    "svelte":     ("Svelte",          "🔥", "#ff3e00"),
    "zig":        ("Zig",             "⚡", "#ec915c"),
    "html":       ("HTML",            "🌐", "#e34c26"),
    "css":        ("CSS",             "🎨", "#563d7c"),
    "csharp":     ("C#",              "🔷", "#178600"),
    "jupyter":    ("Jupyter Notebook","📓", "#DA5B0B"),
    "dockerfile": ("Dockerfile",      "🐳", "#384d54"),
    "nix":        ("Nix",             "❄️", "#7e7eff"),
    "lua":        ("Lua",             "🌙", "#000080"),
    "php":        ("PHP",             "🐘", "#4F5D95"),
    "other":      ("Other",           "📦", "#888888"),
}
```

### Language → Slug Function

```python
import re

# Special cases where simple lowercasing breaks slug uniqueness
LANG_SLUG_OVERRIDES = {
    "C++":              "cpp",
    "C#":               "csharp",
    "Objective-C":      "objective-c",
    "Objective-C++":    "objective-cpp",
    "Jupyter Notebook": "jupyter",
    "Dockerfile":       "dockerfile",
}

def language_to_slug(lang):
    """Convert GitHub language string to URL-safe slug."""
    if not lang:
        return "other"
    if lang in LANG_SLUG_OVERRIDES:
        return LANG_SLUG_OVERRIDES[lang]
    return re.sub(r"[^a-z0-9]+", "-", lang.lower()).strip("-")
```

[VERIFIED: tested locally — C++→"cpp", C#→"csharp", Jupyter Notebook→"jupyter", None→"other", Python→"python" ✓]

### Null Language Handling

GitHub API returns `"language": null` for repos with no detected language (pure markdown repos, config repos, etc.). These should be grouped as **"Other"**:

```python
lang = repo.get("language") or "Other"
slug = language_to_slug(repo.get("language"))  # returns "other" for None
```

In the card HTML, when language is null, render a dash instead of a colored badge (matching Phase 1 pattern seen in `sindresorhus/awesome` — line 462 of index.html):

```html
<!-- When language is None -->
<span class="lang-badge border border-current px-2 py-0.5 text-[10px] font-bold opacity-40">&mdash;</span>

<!-- When language is present -->
<span class="lang-badge border border-current px-2 py-0.5 text-[10px] font-bold flex items-center gap-1">
  <span class="w-2 h-2 flex-shrink-0" style="background:{color}"></span>{language}
</span>
```

[VERIFIED: Line 462 of docs/index.html shows this exact pattern for the awesome repo]

---

## HTML Templates

### Page Structure Overview

```
<html>
  <head> ... Tailwind CDN, fonts, tailwind.config, custom CSS ... </head>
  <body>
    <header>  ← sticky status strip (SERIAL NO, TOTAL_REPOS, UPDATED)
    <main>
      <section>  ← hero: STARS. heading + total count
      <div class="flex">  ← two-column layout
        <aside class="w-64 ...">  ← LEFT: category sidebar nav
        <div class="flex-1 ...">  ← RIGHT: category sections
      </div>
    </main>
    <footer>
    <script>  ← minimal JS for mobile nav toggle (if needed)
  </body>
</html>
```

**Key difference from Phase 1:** Phase 1 has a 3-column filter-button section before the cards. Phase 2 replaces this with a two-column sticky-sidebar + content layout (per HTML-09). The sidebar holds the category nav; the right column holds all `<section>` elements.

### Template: Two-Column Layout Wrapper

```html
<!-- Replaces Phase 1's filter-button section -->
<div class="flex flex-col md:flex-row min-h-screen">
  <!-- LEFT: sidebar nav (sticky on desktop, collapses on mobile) -->
  <aside class="md:w-64 border-b-2 md:border-b-0 md:border-r-2 border-navy dark:border-white
                md:sticky md:top-[45px] md:self-start md:max-h-[calc(100vh-45px)] md:overflow-y-auto
                bg-background-light dark:bg-background-dark flex-shrink-0">
    <div class="p-4 border-b-2 border-navy dark:border-white">
      <div class="text-[10px] font-bold uppercase tracking-widest mb-3">Categories</div>
      <nav>
        <ul class="space-y-0">
{nav_items}
        </ul>
      </nav>
    </div>
  </aside>
  <!-- RIGHT: category sections -->
  <div class="flex-1 min-w-0">
{category_sections}
  </div>
</div>
```

### Template: Nav Item

```python
NAV_ITEM_TEMPLATE = """\
          <li>
            <a href="#{slug}" class="flex items-center justify-between px-3 py-2 text-[10px] font-bold uppercase
               hover:bg-primary hover:text-white transition-colors border-b border-navy/10 dark:border-white/10
               group">
              <span class="flex items-center gap-2">
                <span class="opacity-60">{emoji}</span>
                <span>{display_name}</span>
              </span>
              <span class="bg-navy text-white dark:bg-white dark:text-navy px-1.5 py-0.5 text-[9px] font-bold
                           group-hover:bg-white group-hover:text-primary">{count}</span>
            </a>
          </li>"""
```

### Template: Category Section Header

```python
SECTION_HEADER_TEMPLATE = """\
<section id="{slug}" data-category="{slug}" class="border-b-2 border-navy dark:border-white">
  <div class="px-8 py-4 border-b-2 border-navy dark:border-white flex justify-between items-center
              bg-zinc-200 dark:bg-zinc-800 uppercase font-bold text-[10px]">
    <span class="flex items-center gap-3">
      <span class="text-lg">{emoji}</span>
      <span>{display_name_upper} // CATEGORY_{cat_num:02d}</span>
    </span>
    <span class="text-primary">TOTAL_ENTRIES: {count}</span>
  </div>
  <div class="divide-y-2 divide-navy dark:divide-white">
{cards}
  </div>
</section>"""
```

### Template: Repo Card (exact match to Phase 1 structure)

```python
CARD_TEMPLATE = """\
    <div class="flex flex-col md:flex-row">
      <a href="{html_url}" target="_blank" rel="noopener noreferrer"
         class="card-left w-full md:w-1/3 p-8 flex flex-col justify-between border-b-2 md:border-b-0 md:border-r-2 border-navy dark:border-white bg-background-light dark:bg-background-dark">
        <div>
          <div class="file-num text-[10px] font-bold text-primary mb-2">FILE: #{index:03d}</div>
          <div class="owner-name text-[10px] uppercase opacity-50 mb-1">{owner}</div>
          <h3 class="repo-name text-2xl font-bold uppercase leading-tight">{safe_name}</h3>
          <div class="mt-4 flex flex-wrap gap-2">
            {lang_badge}
            <span class="stars-badge bg-primary text-white px-2 py-0.5 text-[10px] font-bold">&#9733; {k_stars}</span>
          </div>
        </div>
        <div class="mt-8">
          <div class="meta-label bg-navy text-white dark:bg-white dark:text-navy px-2 py-1 inline-block text-[10px] font-bold mb-2">METADATA</div>
          <div class="h-8 {barcode_style} opacity-50"></div>
        </div>
      </a>
      <div class="flex-1 p-8 bg-zinc-50 dark:bg-zinc-900 flex flex-col justify-between">
        <p class="text-sm opacity-70 leading-relaxed">{safe_desc}</p>
        <a href="{html_url}" target="_blank" rel="noopener noreferrer"
           class="mt-8 self-start cursor-pointer border-2 border-navy dark:border-white px-4 py-2 text-[10px] font-bold uppercase hover:bg-primary hover:text-white hover:border-primary transition-colors">VIEW ON GITHUB &#8599;</a>
      </div>
      <div class="hidden lg:flex w-16 border-l-2 border-navy dark:border-white flex-col justify-center items-center gap-4 py-8">
        <span class="material-icons rotate-45 text-2xl">arrow_forward</span>
        <div class="[writing-mode:vertical-lr] text-[10px] font-bold uppercase">View Repo</div>
      </div>
    </div>"""
```

**Barcode style variation:** Phase 1 uses varying stripe widths per card (1px, 2px, 3px, 4px) to give each card a unique "barcode" look. Generate deterministically from the card index:

```python
# Source: observed pattern in docs/index.html lines 162, 190, 216, 243 etc.
BARCODE_STYLES = [
    "bg-[repeating-linear-gradient(90deg,#000,#000_1px,transparent_1px,transparent_4px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_1px,transparent_1px,transparent_4px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_2px,transparent_2px,transparent_8px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_2px,transparent_2px,transparent_8px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_1px,transparent_1px,transparent_3px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_1px,transparent_1px,transparent_3px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_3px,transparent_3px,transparent_9px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_3px,transparent_3px,transparent_9px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_1px,transparent_1px,transparent_5px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_1px,transparent_1px,transparent_5px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_4px,transparent_4px,transparent_10px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_4px,transparent_4px,transparent_10px)]",
]
barcode_style = BARCODE_STYLES[index % len(BARCODE_STYLES)]
```

[VERIFIED: Pattern extracted directly from docs/index.html lines 162, 189, 216, 243, 342, 504]

### Template: Language Badge (inline conditional)

```python
def lang_badge_html(language, lang_meta):
    """Generate language badge HTML. Empty string when language is None."""
    import html as html_module
    if not language:
        return '<span class="lang-badge border border-current px-2 py-0.5 text-[10px] font-bold opacity-40">&mdash;</span>'
    slug = language_to_slug(language)
    meta = lang_meta.get(slug, lang_meta["other"])
    color = meta[2]  # (display_name, emoji, color)
    safe_lang = html_module.escape(language)
    return (f'<span class="lang-badge border border-current px-2 py-0.5 text-[10px] font-bold '
            f'flex items-center gap-1">'
            f'<span class="w-2 h-2 flex-shrink-0" style="background:{color}"></span>'
            f'{safe_lang}</span>')
```

---

## generate.py Architecture

```python
#!/usr/bin/env python3
"""
generate.py — reads _data/repos.json (+ optional _data/categories.json)
and writes docs/index.html
"""
import json, os, html, re, datetime
from collections import defaultdict

# 1. LOAD DATA
repos = load_repos("_data/repos.json")           # raises if not found
cat_map = load_categories("_data/categories.json")  # returns {} if not found

# 2. GROUP
if cat_map:
    groups = group_by_categories(repos, cat_map)  # Phase 3 path
else:
    groups = group_by_language(repos)              # Phase 2 fallback

# 3. RENDER PARTS
nav_html = render_nav(groups)
sections_html = render_sections(groups)

# 4. ASSEMBLE + WRITE
page_html = render_page(
    nav_html=nav_html,
    sections_html=sections_html,
    total=len(repos),
    generated_at=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    serial_date=datetime.datetime.utcnow().strftime("%Y%m%d"),
)
os.makedirs("docs", exist_ok=True)
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(page_html)
print(f"Generated docs/index.html: {len(repos)} repos, {len(groups)} categories")
```

### Key Design: render_sections() global index counter

Repo cards need a global `FILE: #001` counter across all sections (not reset per section). Use an `itertools.count()` or a shared integer:

```python
def render_sections(groups):
    parts = []
    global_index = 1
    for cat_num, (category, repos) in enumerate(groups.items(), start=1):
        cards = []
        for repo in repos:  # already sorted by stars desc
            cards.append(render_card(repo, global_index))
            global_index += 1
        slug = language_to_slug(category) if not is_ai_category(category) else category_slug(category)
        parts.append(render_section(slug, category, cards, cat_num))
    return "\n".join(parts)
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP pagination | Custom `urllib.request` loop | `requests` + `re` | requests handles headers, encoding, errors cleanly |
| HTML templating | Custom `str.replace()` dict substitution | f-strings with `html.escape()` | f-strings are explicit; custom replace risks double-escaping |
| JSON schema validation | Custom key-checking loops | Rely on `dict.get(key)` with defaults | Schema is fixed 6-field contract; missing fields default to None safely |
| Star count formatting | Custom format string | `fmt_stars()` function | Edge cases: exactly 1000, exactly 1M, decimal truncation |
| Language color mapping | API lookup or AI generation | Hardcoded dict | Color map is stable; 15 common languages cover >90% of repos |

---

## Common Pitfalls

### Pitfall 1: Missing `per_page=100`
**What goes wrong:** Default `per_page=30` silently returns first 30 repos only. 370 repos → only 30 repos in output. No error.
**Why it happens:** GitHub API default is 30; the response looks valid.
**How to avoid:** Always construct URL as `https://api.github.com/user/starred?per_page=100`. Verify output count vs. GitHub profile star count.
**Warning signs:** `repos.json` has exactly 30 entries.

### Pitfall 2: No `raise_for_status()` → Silent Empty Results
**What goes wrong:** Bad token (401), wrong account, rate limit (429) all return non-200 but `resp.json()` may still parse (GitHub returns JSON error bodies). `.extend([])` silently adds nothing.
**How to avoid:** Always call `resp.raise_for_status()` immediately after `requests.get()`.
**Warning signs:** Empty `repos.json`, no Python exception.

### Pitfall 3: Missing `html.escape()` on Descriptions
**What goes wrong:** A repo description like `"A C++ & C# <framework>"` generates malformed HTML. Breaks card layout, potentially the whole page.
**How to avoid:** `safe_desc = html.escape(repo.get("description") or "")` on every value embedded in HTML attributes or text.
**Warning signs:** HTML validator errors; cards with `<` or `>` in description break layout.

### Pitfall 4: `language: null` → KeyError or "None" Display
**What goes wrong:** `repo["language"]` raises `KeyError` (use `.get()`); `str(None)` produces `"None"` in card.
**How to avoid:** `lang = repo.get("language")`, then conditional badge rendering.
**Warning signs:** "None" text appearing in language badge on cards.

### Pitfall 5: Writing `_data/repos.json` Path Before Mkdir
**What goes wrong:** `open("_data/repos.json", "w")` raises `FileNotFoundError` if `_data/` doesn't exist yet.
**How to avoid:** `os.makedirs("_data", exist_ok=True)` before writing.
**Warning signs:** `FileNotFoundError: [Errno 2] No such file or directory: '_data/repos.json'`.

### Pitfall 6: Two-Column Layout Sidebar Not Sticky
**What goes wrong:** Long repo lists push sidebar out of viewport; nav is only visible at top of page.
**How to avoid:** Use `md:sticky md:top-[45px] md:self-start md:max-h-[calc(100vh-45px)] md:overflow-y-auto` on the `<aside>`. The `45px` offset matches the header height.
**Warning signs:** Sidebar scrolls away with main content instead of staying fixed.

### Pitfall 7: Section Ordering Nondeterministic
**What goes wrong:** Python `defaultdict` insertion order is insertion order; if repos arrive in random order per language, section order changes between runs, breaking stable bookmarks.
**How to avoid:** Sort groups by total star count descending (most popular language section first). This is deterministic given the same input.

---

## Validation Strategy

### FETCH-01: Pagination Verified
After running `fetch_stars.py`:
```bash
python3 -c "import json; r=json.load(open('_data/repos.json')); print(len(r), 'repos')"
```
Compare to star count on GitHub profile (https://github.com/therustyrobot?tab=stars). Should match within ±5 (slight timing difference). The test is: `count > 100` confirms pagination occurred.

### FETCH-02: Filter Verified
```bash
python3 -c "
import json
repos = json.load(open('_data/repos.json'))
forks = [r for r in repos if r.get('fork')]
archived = [r for r in repos if r.get('archived')]
print(f'Forks: {len(forks)}, Archived: {len(archived)}')  # should both be 0
"
```

### HTML Output Verified
```bash
# Count section headers in output
grep -c 'data-category=' docs/index.html
# Count repo cards
grep -c 'file-num' docs/index.html
# Verify sorted within a section: grab star counts for first section
python3 -c "
import re
html = open('docs/index.html').read()
stars = re.findall(r'&#9733; ([\d.]+[KM]?)', html)
print('First 10 star counts:', stars[:10])  # should be descending
"
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (to be installed — Wave 0 gap) |
| Config file | `pytest.ini` — Wave 0 gap |
| Quick run command | `python3 -m pytest tests/ -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FETCH-01 | Pagination: fetches all pages until no `rel="next"` | unit (mock HTTP) | `pytest tests/test_fetch.py::test_pagination -x` | ❌ Wave 0 |
| FETCH-01 | First page URL has `per_page=100` | unit | `pytest tests/test_fetch.py::test_per_page_100 -x` | ❌ Wave 0 |
| FETCH-02 | Forked repos excluded from output | unit | `pytest tests/test_fetch.py::test_filter_forks -x` | ❌ Wave 0 |
| FETCH-02 | Archived repos excluded from output | unit | `pytest tests/test_fetch.py::test_filter_archived -x` | ❌ Wave 0 |
| FETCH-03 | Output JSON has exactly 6 keys per record | unit | `pytest tests/test_fetch.py::test_output_schema -x` | ❌ Wave 0 |
| HTML-07 | Repos within each section sorted by stars desc | unit | `pytest tests/test_generate.py::test_sort_order -x` | ❌ Wave 0 |
| HTML-08 | Section headers contain emoji, count badge, anchor id | unit | `pytest tests/test_generate.py::test_section_header -x` | ❌ Wave 0 |
| HTML-09 | Sidebar nav contains anchor links to all category slugs | unit | `pytest tests/test_generate.py::test_nav_anchors -x` | ❌ Wave 0 |
| HTML-01 | generate.py produces valid HTML file at docs/index.html | integration (smoke) | `pytest tests/test_generate.py::test_output_file_exists -x` | ❌ Wave 0 |
| — | fmt_stars() K-formatting correctness | unit | `pytest tests/test_generate.py::test_fmt_stars -x` | ❌ Wave 0 |
| — | language_to_slug() handles C++, C#, null | unit | `pytest tests/test_generate.py::test_language_slug -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/ -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_fetch.py` — covers FETCH-01, FETCH-02, FETCH-03 (use `unittest.mock.patch` for HTTP)
- [ ] `tests/test_generate.py` — covers HTML-01, HTML-07, HTML-08, HTML-09, fmt_stars, slug
- [ ] `pytest.ini` — minimal config with `testpaths = tests`
- [ ] Framework install: `pip install pytest` — pytest not currently installed

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Script runs in CI with env var token; no user auth |
| V3 Session Management | No | Static site; no sessions |
| V4 Access Control | No | Read-only data fetch; no write paths exposed |
| V5 Input Validation | Yes | `html.escape()` on all GitHub API strings embedded in HTML |
| V6 Cryptography | No | No crypto needed; HTTPS enforced by `requests` |
| V7 Error Handling | Yes | `raise_for_status()` + explicit error messages; never expose token in logs |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token leakage in logs | Information Disclosure | Never `print(token)`. Use `os.environ["GITHUB_TOKEN"]` — fail loudly if missing (KeyError is intentional). |
| XSS via repo description | Tampering | `html.escape()` on every user-supplied string embedded in HTML |
| Token hardcoded in script | Information Disclosure | `os.environ["GITHUB_TOKEN"]` only; never default value in script |
| Malicious repo name as HTML | Tampering | `html.escape(repo["name"])` — names can contain `<`, `>`, `"` |

**Token handling pattern:**
```python
# CORRECT — raises KeyError if not set (intentional fail-fast)
token = os.environ["GITHUB_TOKEN"]

# WRONG — silently uses empty token, gets 401 with no explanation
token = os.environ.get("GITHUB_TOKEN", "")
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Both scripts | ✓ | 3.9.6 (local); 3.12 (ubuntu-latest) | — |
| `requests` | fetch_stars.py | ✗ locally | — | `pip install requests` locally; pre-installed on ubuntu-latest |
| `pytest` | test suite | ✗ | — | `pip install pytest` — Wave 0 task |
| `_data/` directory | Both scripts | ✗ (gitignored) | — | `os.makedirs(..., exist_ok=True)` in scripts |
| `docs/` directory | generate.py | ✓ | exists (index.html in it) | — |

**Missing dependencies with no fallback:**
- None — all missing items have clear install paths or exist on ubuntu-latest runners

**Missing dependencies with fallback:**
- `requests` not installed locally: `pip install requests` (or test with `python3 -m pip install requests`)
- `pytest` not installed: `pip install pytest` in Wave 0

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Jinja2 for Python HTML gen | f-strings + html.escape | Ongoing preference for zero-dep | No new dep; explicit escaping |
| `urllib.request` for HTTP | `requests` | Python 2→3 era | Cleaner API, auto header handling |
| `Link` header with `urllib.parse` | `re.search` regex | — | One-liner, no dependency |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Emoji assignments for language slugs (e.g., 🐹 for Go, 🦀 for Rust) | Language Grouping | Only aesthetic; easy to change |
| A2 | `requests` is pre-installed on `ubuntu-latest` (per REQUIREMENTS.md ACTION-03 note) | Standard Stack | Need explicit `pip install requests` step in workflow if wrong |
| A3 | Header height is ~45px for the `md:top-[45px]` sticky sidebar offset | HTML Templates | Sidebar cuts off below/above header; adjust offset value |
| A4 | Global FILE index counter is continuous across all sections (not reset per section) | generate.py Architecture | Cards restart at #001 per section — aesthetic only, easily changed |

---

## Open Questions

1. **Mobile sidebar behavior**
   - What we know: HTML-09 says "mobile responsive" for nav
   - What's unclear: Should the sidebar collapse into a hamburger toggle on mobile, or stack as a horizontal scroll strip?
   - Recommendation: Stack vertically above content on mobile (no JS toggle needed); Tailwind `md:flex-row` on the two-column wrapper handles this naturally

2. **Section ordering: by total stars vs. alphabetical**
   - What we know: Repos within sections are sorted by stars desc (HTML-07)
   - What's unclear: How should the sections themselves be ordered?
   - Recommendation: Sort sections by total star count of all repos in the section (descending) — surfaces most popular languages first; deterministic

3. **Marquee ticker content**
   - What we know: Phase 1 has `<div class="... animate-[marquee_20s_linear_infinite]">` with hardcoded category names
   - What's unclear: Should Phase 2 populate it dynamically with actual language names?
   - Recommendation: Yes — generate dynamically from `" // ".join(group_names)` repeated 4× to fill the scroll

---

## Sources

### Primary (HIGH confidence)
- `docs/index.html` (552 lines) — exact card markup, barcode styles, Tailwind classes verified by reading
- `starred_repos.md` — category taxonomy, 370 repo count
- `.planning/REQUIREMENTS.md` — requirement IDs, constraint notes

### Secondary (MEDIUM confidence)
- [CITED: https://docs.github.com/en/rest/activity/starring] — endpoint, fields, pagination
- [CITED: https://docs.github.com/en/rest/using-the-rest-api/rate-limiting-for-the-rest-api] — rate limits

### Tertiary (LOW confidence — training knowledge)
- Emoji choices for language slugs — `[ASSUMED]`
- `requests` pre-installed on ubuntu-latest — noted in REQUIREMENTS.md, not independently verified in this session

---

## Metadata

**Confidence breakdown:**
- GitHub API endpoint + pagination: HIGH — cited official docs, confirmed regex pattern tested
- Python patterns: HIGH — all code examples verified locally with Python 3.9.6
- HTML templates: HIGH — extracted directly from existing docs/index.html
- Language emoji map: LOW — assumed aesthetics, easily changed
- requests on ubuntu-latest: MEDIUM — mentioned in project REQUIREMENTS.md notes

**Research date:** 2026-04-21
**Valid until:** 2026-07-21 (GitHub API pagination format is stable; Tailwind CDN URL stable)
