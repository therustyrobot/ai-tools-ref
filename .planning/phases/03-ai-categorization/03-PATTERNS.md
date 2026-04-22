# Phase 3: AI Categorization - Pattern Map

**Mapped:** 2026-04-22
**Files analyzed:** 4 (2 new, 2 modified)
**Analogs found:** 4 / 4

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `scripts/categorize.py` | script/service | request-response (batch API → file I/O) | `scripts/fetch_stars.py` | role-match (same: env token, requests, `_data/` write, `resp.raise_for_status()`) |
| `tests/test_categorize.py` | test | batch + mock | `tests/test_fetch.py` | exact (same: importlib bootstrap, `types.ModuleType` injection, `MagicMock`, `patch`) |
| `scripts/generate.py` | script/generator | transform (JSON → HTML) | itself (direct modification) | exact |
| `tests/test_generate.py` | test | unit (pure logic) | itself (direct modification) | exact |

---

## Pattern Assignments

---

### `scripts/categorize.py` (NEW — script, request-response + file I/O)

**Analog:** `scripts/fetch_stars.py`

---

#### Imports pattern (fetch_stars.py lines 1–7)

```python
#!/usr/bin/env python3
"""categorize.py — batch-categorize repos via GitHub Models API, writes _data/categories.json"""
import os
import re
import json
import requests
```

> Copy the shebang line, module docstring convention, and import block exactly. `re` is needed for slug derivation and markdown fence stripping. No new pip dependencies.

---

#### Token / fail-fast auth pattern (fetch_stars.py line 52)

```python
if __name__ == "__main__":
    token = os.environ["GITHUB_TOKEN"]  # KeyError = fail-fast; never default to ""
```

> `os.environ["GITHUB_TOKEN"]` with no `.get()` fallback. KeyError is intentional — fail loud in CI if the secret is missing. In `categorize.py`, use `Bearer` format instead of `token`:

```python
# categorize.py specific auth (GitHub Models API uses Bearer, not token)
session.headers.update({
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
})
```

---

#### requests.Session pattern (RESEARCH.md Pattern 1)

```python
GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"
MODEL = "openai/gpt-4o-mini"

def build_session(token):
    """Create a requests.Session with Bearer auth headers pre-set."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    return session

def call_model(session, messages):
    """POST to GitHub Models API, return raw content string."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    resp = session.post(GITHUB_MODELS_URL, json=payload)
    resp.raise_for_status()  # MUST be called before .json() — mirrors fetch_stars.py line 29
    return resp.json()["choices"][0]["message"]["content"]
```

> Note `resp.raise_for_status()` before `.json()` — this is a project-wide invariant established in `fetch_stars.py` line 29. Never call `.json()` before raising on HTTP errors.

---

#### `_data/` file-write pattern (fetch_stars.py lines 42–48)

```python
def write_repos(repos, path="_data/repos.json"):
    """Project to FIELDS and write JSON array to path, creating directories as needed."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    records = [{k: r.get(k) for k in FIELDS} for r in repos]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(records)} repos to {path}")
```

> Copy this exact `write_*` pattern for `write_categories()` in `categorize.py`:
> - `os.makedirs(os.path.dirname(path) ..., exist_ok=True)` before open
> - `open(path, "w", encoding="utf-8")`
> - `json.dump(..., ensure_ascii=False, indent=2)`
> - `print(f"Wrote ...")` progress line

---

#### Slug derivation pattern (generate.py lines 78–84)

```python
def language_to_slug(lang):
    """Convert a GitHub language string to a URL-safe slug."""
    if not lang:
        return "other"
    if lang in LANG_SLUG_OVERRIDES:
        return LANG_SLUG_OVERRIDES[lang]
    return re.sub(r"[^a-z0-9]+", "-", lang.lower()).strip("-")
```

> **Duplicate this as `category_to_slug(name)` in `categorize.py`** — no override dict needed for categories (RESEARCH.md §Pattern 3). The 4-line core `re.sub` formula is identical. Verified: `"AI & ML"` → `"ai-ml"`, `"Self-Hosting & Homelab"` → `"self-hosting-homelab"` (RESEARCH.md line 276–294).

---

#### JSON parse + retry + fallback pattern (RESEARCH.md Pattern 2)

```python
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

> Log prefix convention: `[WARN]` on first failure, `[ERROR]` on second. Never raise — assign "Other" and continue. This matches the project's "never crash the pipeline" requirement (CONTEXT.md § Discretion).

---

#### Batch-processing loop pattern (RESEARCH.md AI-02)

```python
BATCH_SIZE = 10

def categorize_all(repos, session):
    """Batch repos into groups of BATCH_SIZE, call model for each, return merged cat_map."""
    cat_map = {}
    for i in range(0, len(repos), BATCH_SIZE):
        batch = repos[i:i + BATCH_SIZE]
        batch_names = [r["full_name"] for r in batch]
        print(f"  Batch {i // BATCH_SIZE + 1}: {batch_names}")
        messages = build_messages(batch)
        result = parse_with_retry(session, messages, batch_names)
        # Derive slug from canonical category name (not from model output)
        for full_name, info in result.items():
            cat_map[full_name] = {
                "category":    info.get("category", "Other"),
                "subcategory": info.get("subcategory", "Other"),
                "slug":        category_to_slug(info.get("category", "Other")),
            }
    return cat_map
```

> Slug is derived **in categorize.py** from `info["category"]`, NOT taken from model output — this ensures anchor stability regardless of what string the model generates (CONTEXT.md D-08 rationale).

---

### `tests/test_categorize.py` (NEW — test, mock + batch logic)

**Analog:** `tests/test_fetch.py`

---

#### Module bootstrap pattern (test_fetch.py lines 12–28)

```python
import importlib.util, pathlib
import types
import sys

_ROOT = pathlib.Path(__file__).parent.parent
_MOD_PATH = _ROOT / "scripts" / "categorize.py"

def _load_module():
    spec = importlib.util.spec_from_file_location("categorize", _MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Inject a fake 'requests' so the import doesn't fail if requests isn't installed
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.ModuleType("requests")
    spec.loader.exec_module(mod)
    return mod

categorize = _load_module()
```

> Copy this bootstrap verbatim, changing only `"fetch_stars"` → `"categorize"` and the path. The `types.ModuleType` injection guard is required — `conftest.py` pre-imports real `requests`, but the guard makes the test safe in isolation too.

---

#### Mock response helper pattern (test_fetch.py lines 48–56)

```python
from unittest.mock import MagicMock, patch

def _mock_post_response(content_str):
    """Build a mock requests.Response for a GitHub Models API POST."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "choices": [{"message": {"content": content_str}}]
    }
    return resp
```

> The `resp.raise_for_status.return_value = None` line is the project-wide mock pattern from `test_fetch.py` line 51. The `.json()` return shape must match `resp.json()["choices"][0]["message"]["content"]` — the exact path used in `call_model()`.

---

#### `patch` usage pattern for `requests.post` (test_fetch.py lines 70–75)

```python
# Patching requests.get in test_fetch.py — mirror for requests.post in test_categorize.py
with patch("requests.Session.post", return_value=mock_resp) as mock_post:
    result = categorize.categorize_all(repos, session)
```

> Or patch at the module level if `categorize.py` uses `session.post(...)`:

```python
with patch.object(session, "post", return_value=mock_resp):
    result = categorize.parse_with_retry(session, messages, batch_names)
```

> Follow the `patch("requests.get", ...)` precedent from `test_fetch.py` line 71 — patch at the point of use, not on the return value.

---

#### Test class structure to copy (test_fetch.py lines 64–143)

```python
class TestCallModel(unittest.TestCase):
    """Tests for call_model() — happy path + raise_for_status."""

class TestStripFences(unittest.TestCase):
    """Tests for strip_fences() — no fences, json fences, bare fences."""

class TestParseWithRetry(unittest.TestCase):
    """Tests for parse_with_retry() — success, one retry success, two failures → Other."""

class TestCategorizeAll(unittest.TestCase):
    """Tests for categorize_all() — batch slicing, slug derivation, Other fallback."""

class TestWriteCategories(unittest.TestCase):
    """Integration: write_categories() produces correct JSON file on disk."""
```

> Mirror `test_fetch.py`'s one-class-per-function structure. Each class tests exactly one function. Use `self.subTest()` for parametric cases (like `test_fetch.py` does not, but `test_generate.py` line 59 does — follow `test_generate.py` for parametric cases).

---

### `scripts/generate.py` (MODIFY — add CATEGORY_META + hierarchical functions)

**Analog:** itself — direct modification target. Patterns extracted from existing code.

---

#### CATEGORY_META dict placement (after LANG_META, generate.py lines 24–50)

```python
# Place immediately after LANG_META block (line 50), before BARCODE_STYLES
CATEGORY_META = {
    # slug: (display_name, material_icon_name)
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

> **Structure is `(display_name, material_icon_name)` — 2-tuple, not 3-tuple.** `LANG_META` uses `(display_name, emoji, color)` 3-tuples (generate.py line 26). These are intentionally different; do NOT mix them. Comment the column headers exactly as shown.

---

#### `group_by_categories_hierarchical()` — mirror of `group_by_categories()` (generate.py lines 138–149)

```python
# Existing flat grouper to mirror (generate.py lines 138–149):
def group_by_categories(repos, cat_map):
    groups = defaultdict(list)
    for repo in repos:
        cat_info = cat_map.get(repo["full_name"], {})
        category = cat_info.get("category", "Other")
        groups[category].append(repo)
    for cat in groups:
        groups[cat].sort(key=lambda r: r.get("stargazers_count") or 0, reverse=True)
    return dict(
        sorted(groups.items(), key=lambda kv: sum(r.get("stargazers_count") or 0 for r in kv[1]), reverse=True)
    )

# New hierarchical grouper to add (RESEARCH.md Pattern 4):
def group_by_categories_hierarchical(repos, cat_map):
    """Group repos into nested {category: {subcategory: [repos]}} structure."""
    hier = defaultdict(lambda: defaultdict(list))
    for repo in repos:
        info = cat_map.get(repo["full_name"], {})
        cat = info.get("category", "Other")
        subcat = info.get("subcategory", "Other")
        hier[cat][subcat].append(repo)
    for cat in hier:
        for subcat in hier[cat]:
            hier[cat][subcat].sort(
                key=lambda r: r.get("stargazers_count") or 0, reverse=True
            )
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

> Place in the `# Grouping` section, immediately after `group_by_categories()`. The sorting invariant (stars descending, groups sorted by total stars) is identical to the flat version.

---

#### `render_subcategory_header()` — Safety Orange divider (RESEARCH.md Pattern 5)

```python
# For placement reference — render_section() is at generate.py lines 196-215
def render_subcategory_header(subcat_name, count, subcat_num):
    """Render a Safety Orange subcategory divider with inline repo count."""
    slug = language_to_slug(subcat_name)
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

> `bg-[#FF5F1F]` is the Tailwind JIT arbitrary color for Safety Orange — already used as `bg-primary` in the existing CSS but specified explicitly here so it renders correctly whether or not Tailwind scans this f-string. Compare with `render_section()` header div at generate.py line 204 (`bg-zinc-200`).

---

#### Updated `render_section()` — CATEGORY_META lookup first (RESEARCH.md Pattern 6)

```python
# Current render_section() icon lookup (generate.py line 199):
#   display_name, emoji, _ = LANG_META.get(slug, (cat_name, "📦", "#888888"))
#
# Replace with D-06 three-way lookup:
def render_section(cat_name, repos, cat_num, global_offset):
    slug = language_to_slug(cat_name)

    # D-06: CATEGORY_META → LANG_META → fallback
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

> The `count` variable in the updated `render_section()` must reflect only the **flat** repo count (for backward compatibility with the language path and existing tests). In the hierarchical path, `render_section()` is called with a flat list — the caller aggregates subcategory repos before passing them.

---

#### `render_nav_hierarchical()` — Material Icons nav (RESEARCH.md Pattern 7)

```python
# Existing render_nav() to mirror (generate.py lines 229-248):
def render_nav(groups):
    items = []
    for cat_name, repos in groups.items():
        slug = language_to_slug(cat_name)
        display_name, emoji, _ = LANG_META.get(slug, (cat_name, "📦", "#888888"))
        count = len(repos)
        items.append(f"""\
          <li>
            <a href="#{slug}" class="flex items-center justify-between px-3 py-2 text-[10px] font-bold uppercase
               hover:bg-primary hover:text-white transition-colors border-b border-navy/10 dark:border-white/10
               group">
              <span class="flex items-center gap-2">
                <span class="opacity-60">{emoji}</span>
                <span>{html.escape(display_name)}</span>
              </span>
              <span class="bg-navy text-white dark:bg-white dark:text-navy px-1.5 py-0.5 text-[9px] font-bold
                           group-hover:bg-white group-hover:text-primary">{count}</span>
            </a>
          </li>""")
    return "\n".join(items)

# New render_nav_hierarchical() (RESEARCH.md Pattern 7):
def render_nav_hierarchical(hier_groups):
    """Sidebar nav for hierarchical groups — top-level categories only (D-03)."""
    items = []
    for cat_name, subcats in hier_groups.items():
        slug = language_to_slug(cat_name)
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

> The `<a>` tag CSS classes are **character-for-character identical** to `render_nav()` at generate.py lines 237–246. The only differences are: `{emoji}` → `{icon_html}` (Material Icons span or emoji fallback), and `len(repos)` → `sum(len(repos) for repos in subcats.values())` to count across subcategories.

---

#### Entry point update (generate.py lines 414–424)

```python
# Current entry point (generate.py lines 414-424):
if __name__ == "__main__":
    repos = load_repos()
    cat_map = load_categories()
    groups = group_by_categories(repos, cat_map) if cat_map else group_by_language(repos)
    nav_html = render_nav(groups)
    sections_html = render_sections(groups)
    page = render_page(nav_html, sections_html, len(repos), datetime.datetime.utcnow())
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Generated docs/index.html: {len(repos)} repos, {len(groups)} categories")

# Updated entry point — branch on cat_map presence:
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
    print(f"Generated docs/index.html: {len(repos)} repos")
```

> `render_sections_hierarchical(hier_groups)` is a new function (parallel to `render_sections(groups)`) that iterates over the `{cat: {subcat: [repos]}}` structure, calls `render_section()` for the top-level header, then `render_subcategory_header()` + cards for each subcategory.

---

### `tests/test_generate.py` (MODIFY — add hierarchical test classes)

**Analog:** itself — direct modification target. Copy class/method structure from existing tests.

---

#### Existing test class structure to mirror (test_generate.py lines 49–188)

```python
# Existing pattern — one class per function under test:
class TestFmtStars(unittest.TestCase):         # lines 49-62
class TestLanguageToSlug(unittest.TestCase):   # lines 65-79
class TestGroupByLanguage(unittest.TestCase):  # lines 83-109
class TestRenderNav(unittest.TestCase):        # lines 113-120
class TestRenderSection(unittest.TestCase):    # lines 123-134
class TestHtmlEscape(unittest.TestCase):       # lines 137-146
class TestOutputFileCreated(unittest.TestCase): # lines 151-183 (integration, uses setUp/tearDown)
```

> New test classes follow the same `class Test<FunctionName>(unittest.TestCase)` convention. Append after `TestHtmlEscape`, before `TestOutputFileCreated` (keep integration test last).

---

#### `_make_repo()` helper — reuse verbatim (test_generate.py lines 35–43)

```python
def _make_repo(full_name="owner/repo", language="Python", stars=100, description="desc"):
    return {
        "full_name": full_name,
        "name": full_name.split("/")[-1],
        "html_url": f"https://github.com/{full_name}",
        "description": description,
        "language": language,
        "stargazers_count": stars,
    }
```

> No changes needed — used by all new test classes too. The existing function covers all fields needed.

---

#### New test class patterns to add

```python
# Test class for group_by_categories_hierarchical()
class TestGroupByCategoriesHierarchical(unittest.TestCase):

    def test_nesting_structure(self):
        """Result must be {category: {subcategory: [repos]}}."""
        repos = [_make_repo("a/r1", stars=100)]
        cat_map = {"a/r1": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"}}
        result = gen.group_by_categories_hierarchical(repos, cat_map)
        self.assertIn("AI & ML", result)
        self.assertIn("LLMs", result["AI & ML"])
        self.assertEqual(len(result["AI & ML"]["LLMs"]), 1)

    def test_missing_from_cat_map_falls_to_other(self):
        """Repo not in cat_map must land in 'Other' > 'Other'."""
        repos = [_make_repo("a/unknown", stars=50)]
        result = gen.group_by_categories_hierarchical(repos, {})
        self.assertIn("Other", result)
        self.assertIn("Other", result["Other"])

    def test_sort_order_within_subcategory(self):
        """Repos within a subcategory must be sorted highest stars first."""
        repos = [_make_repo("a/r1", stars=10), _make_repo("a/r2", stars=500)]
        cat_map = {
            "a/r1": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"},
            "a/r2": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"},
        }
        result = gen.group_by_categories_hierarchical(repos, cat_map)
        counts = [r["stargazers_count"] for r in result["AI & ML"]["LLMs"]]
        self.assertEqual(counts, sorted(counts, reverse=True))


# Test class for CATEGORY_META lookup
class TestCategoryMetaLookup(unittest.TestCase):

    def test_category_meta_keys_present(self):
        """All 14 locked slugs must exist in CATEGORY_META."""
        expected = [
            "ai-ml", "self-hosting-homelab", "dev-tools-cli", "devops-infra",
            "security", "web-frontend", "data-analytics", "productivity-notes",
            "media-entertainment", "networking", "mobile-desktop",
            "awesome-lists", "esp32-hardware", "other",
        ]
        for slug in expected:
            with self.subTest(slug=slug):
                self.assertIn(slug, gen.CATEGORY_META)

    def test_category_meta_tuple_length(self):
        """Each CATEGORY_META value must be a 2-tuple (display_name, icon_name)."""
        for slug, val in gen.CATEGORY_META.items():
            with self.subTest(slug=slug):
                self.assertEqual(len(val), 2)


# Test class for render_subcategory_header()
class TestRenderSubcategoryHeader(unittest.TestCase):

    def test_orange_background_class(self):
        """Subcategory header must contain Safety Orange bg class."""
        html_out = gen.render_subcategory_header("LLMs", 5, 1)
        self.assertIn("bg-[#FF5F1F]", html_out)

    def test_entry_count_displayed(self):
        """ENTRIES count must appear in subcategory header HTML."""
        html_out = gen.render_subcategory_header("LLMs", 7, 1)
        self.assertIn("ENTRIES: 7", html_out)

    def test_data_subcategory_attribute(self):
        """data-subcategory attribute must be present with correct slug."""
        html_out = gen.render_subcategory_header("LLMs", 3, 1)
        self.assertIn('data-subcategory="llms"', html_out)


# Test class for render_nav_hierarchical()
class TestRenderNavHierarchical(unittest.TestCase):

    def test_anchor_links_top_level_only(self):
        """Nav must only contain top-level category anchors, not subcategory anchors."""
        hier_groups = {
            "AI & ML": {
                "LLMs": [_make_repo("a/r1", stars=100)],
                "Agents": [_make_repo("a/r2", stars=50)],
            }
        }
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn('href="#ai-ml"', nav_html)
        self.assertNotIn('href="#llms"', nav_html)

    def test_total_count_across_subcategories(self):
        """Count badge must sum across all subcategories."""
        hier_groups = {
            "AI & ML": {
                "LLMs": [_make_repo("a/r1"), _make_repo("a/r2")],
                "Agents": [_make_repo("a/r3")],
            }
        }
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn(">3<", nav_html)

    def test_material_icon_for_known_category(self):
        """Known CATEGORY_META slug must render material-icons span."""
        hier_groups = {"AI & ML": {"LLMs": [_make_repo()]}}
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn('class="material-icons', nav_html)
```

> Use `self.subTest(slug=slug)` for parametric loops — mirrors `TestFmtStars` at test_generate.py line 59. Use `self.assertIn` / `self.assertNotIn` for HTML output assertions — mirrors `TestRenderNav` at line 120 and `TestRenderSection` at lines 131–133.

---

#### Integration test — sample_categories.json fixture (test_generate.py lines 151–183 pattern)

```python
# New integration test (append to TestOutputFileCreated OR create TestOutputFileHierarchical):
class TestOutputFileHierarchical(unittest.TestCase):

    def setUp(self):
        self.orig_dir = os.getcwd()
        self.tmp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp_dir, "_data"))
        # Copy both fixtures
        shutil.copy(FIXTURE_PATH, os.path.join(self.tmp_dir, "_data", "repos.json"))
        shutil.copy(CATEGORIES_FIXTURE_PATH,
                    os.path.join(self.tmp_dir, "_data", "categories.json"))
        os.makedirs(os.path.join(self.tmp_dir, "docs"), exist_ok=True)
        os.chdir(self.tmp_dir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
```

> Add `CATEGORIES_FIXTURE_PATH = _ROOT / "tests" / "fixtures" / "sample_categories.json"` near `FIXTURE_PATH` at the top of the test file (line 32). The fixture must be created at `tests/fixtures/sample_categories.json` with a small sample (3–5 repos) matching `sample_repos.json` `full_name` values.

---

## Shared Patterns

### 1. Token / Env var — fail-fast
**Source:** `scripts/fetch_stars.py` line 52
**Apply to:** `scripts/categorize.py` entry point
```python
token = os.environ["GITHUB_TOKEN"]  # KeyError = fail-fast; never default to ""
```

### 2. `resp.raise_for_status()` before `.json()`
**Source:** `scripts/fetch_stars.py` line 29
**Apply to:** `call_model()` in `scripts/categorize.py`
```python
resp.raise_for_status()  # MUST be called before .json()
```

### 3. `_data/` write with makedirs
**Source:** `scripts/fetch_stars.py` lines 43–44
**Apply to:** `write_categories()` in `scripts/categorize.py`
```python
os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 4. importlib bootstrap + types.ModuleType guard
**Source:** `tests/test_fetch.py` lines 12–28
**Apply to:** `tests/test_categorize.py` bootstrap section
```python
if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")
spec.loader.exec_module(mod)
```

### 5. `MagicMock` response with `raise_for_status`
**Source:** `tests/test_fetch.py` lines 48–56
**Apply to:** All HTTP mock helpers in `tests/test_categorize.py`
```python
resp = MagicMock()
resp.raise_for_status.return_value = None
resp.json.return_value = { ... }
```

### 6. `self.subTest()` for parametric assertions
**Source:** `tests/test_generate.py` lines 59–61
**Apply to:** `TestCategoryMetaLookup` in `tests/test_generate.py`
```python
for slug in expected_slugs:
    with self.subTest(slug=slug):
        self.assertIn(slug, gen.CATEGORY_META)
```

### 7. Material Icons ligature span
**Source:** `scripts/generate.py` line 191 (in `render_card()`)
**Apply to:** `render_subcategory_header()`, `render_nav_hierarchical()`, updated `render_section()` in `scripts/generate.py`
```python
f'<span class="material-icons text-lg">{icon_name}</span>'
# Already loaded via CDN in render_page() <head>: fonts.googleapis.com/icon?family=Material+Icons
```

### 8. `html.escape()` for all user-visible strings
**Source:** `scripts/generate.py` lines 161–163, 199, 208
**Apply to:** `render_subcategory_header()`, `render_nav_hierarchical()` in `scripts/generate.py`
```python
safe_name = html.escape(subcat_name.upper())
# All display_name values passed to f-strings must go through html.escape()
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/fixtures/sample_categories.json` | fixture | static data | No existing categories fixture; planner must define minimal JSON schema matching `{"owner/repo": {"category": "...", "subcategory": "...", "slug": "..."}}` with 3–5 entries keyed to `sample_repos.json` full_names |

---

## Metadata

**Analog search scope:** `scripts/`, `tests/`, `tests/fixtures/`
**Files scanned:** 5 (`fetch_stars.py`, `generate.py`, `test_fetch.py`, `test_generate.py`, `conftest.py`)
**Pattern extraction date:** 2026-04-22
