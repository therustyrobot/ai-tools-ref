#!/usr/bin/env python3
"""generate.py — reads _data/repos.json (+ optional _data/categories.json),
groups by language (or category), and writes docs/index.html."""
import datetime
import html
import json
import os
import re
from collections import defaultdict

# ---------------------------------------------------------------------------
# Language metadata
# ---------------------------------------------------------------------------

LANG_SLUG_OVERRIDES = {
    "C++": "cpp",
    "C#": "csharp",
    "Objective-C": "objective-c",
    "Objective-C++": "objective-cpp",
    "Jupyter Notebook": "jupyter",
    "Dockerfile": "dockerfile",
}

LANG_META = {
    # slug: (display_name, emoji, color)
    "python":     ("Python",           "🐍", "#3572A5"),
    "typescript": ("TypeScript",       "🔷", "#2b7489"),
    "javascript": ("JavaScript",       "🟨", "#f1e05a"),
    "go":         ("Go",               "🐹", "#00ADD8"),
    "rust":       ("Rust",             "🦀", "#DEA584"),
    "shell":      ("Shell",            "🐚", "#89e051"),
    "c":          ("C",                "⚙️",  "#555555"),
    "cpp":        ("C++",              "⚡", "#f34b7d"),
    "java":       ("Java",             "☕", "#b07219"),
    "ruby":       ("Ruby",             "💎", "#701516"),
    "swift":      ("Swift",            "🦅", "#ffac45"),
    "kotlin":     ("Kotlin",           "🎯", "#A97BFF"),
    "vue":        ("Vue",              "💚", "#41b883"),
    "svelte":     ("Svelte",           "🔥", "#ff3e00"),
    "zig":        ("Zig",              "⚡", "#ec915c"),
    "html":       ("HTML",             "🌐", "#e34c26"),
    "css":        ("CSS",              "🎨", "#563d7c"),
    "csharp":     ("C#",               "🔷", "#178600"),
    "jupyter":    ("Jupyter Notebook", "📓", "#DA5B0B"),
    "dockerfile": ("Dockerfile",       "🐳", "#384d54"),
    "nix":        ("Nix",              "❄️",  "#7e7eff"),
    "lua":        ("Lua",              "🌙", "#000080"),
    "php":        ("PHP",              "🐘", "#4F5D95"),
    "other":      ("Other",            "📦", "#888888"),
}

CATEGORY_META = {
    # slug: (display_name, material_icon_name)  — 2-tuple, NOT 3-tuple like LANG_META
    "ai-ml":                ("AI & ML",                "smart_toy"),
    "self-hosting-homelab": ("Self-Hosting & Homelab", "dns"),
    "dev-tools-cli":        ("Dev Tools & CLI",        "terminal"),
    "devops-infra":         ("DevOps & Infra",         "cloud"),
    "security":             ("Security",               "lock"),
    "web-frontend":         ("Web & Frontend",         "web"),
    "data-analytics":       ("Data & Analytics",       "bar_chart"),
    "productivity-notes":   ("Productivity & Notes",   "edit_note"),
    "media-entertainment":  ("Media & Entertainment",  "movie"),
    "networking":           ("Networking",             "router"),
    "mobile-desktop":       ("Mobile & Desktop",       "devices"),
    "awesome-lists":        ("Awesome Lists",          "star"),
    "esp32-hardware":       ("ESP32 & Hardware",       "developer_board"),
    "other":                ("Other",                  "category"),
}

BARCODE_STYLES = [
    "bg-[repeating-linear-gradient(90deg,#000,#000_1px,transparent_1px,transparent_4px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_1px,transparent_1px,transparent_4px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_2px,transparent_2px,transparent_8px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_2px,transparent_2px,transparent_8px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_1px,transparent_1px,transparent_3px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_1px,transparent_1px,transparent_3px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_3px,transparent_3px,transparent_9px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_3px,transparent_3px,transparent_9px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_1px,transparent_1px,transparent_5px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_1px,transparent_1px,transparent_5px)]",
    "bg-[repeating-linear-gradient(90deg,#000,#000_4px,transparent_4px,transparent_10px)] dark:bg-[repeating-linear-gradient(90deg,#fff,#fff_4px,transparent_4px,transparent_10px)]",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_stars(n):
    """Format a star count as human-readable string: 1200 → '1.2K', 1500000 → '1.5M'."""
    if n is None:
        return "?"
    if n >= 1_000_000:
        v = n / 1_000_000
        return (f"{v:.1f}" if v % 1 else f"{int(v)}") + "M"
    elif n >= 1_000:
        v = n / 1_000
        return (f"{v:.1f}" if v % 1 else f"{int(v)}") + "K"
    return str(n)


def language_to_slug(lang):
    """Convert a GitHub language string to a URL-safe slug."""
    if not lang:
        return "other"
    if lang in LANG_SLUG_OVERRIDES:
        return LANG_SLUG_OVERRIDES[lang]
    return re.sub(r"[^a-z0-9]+", "-", lang.lower()).strip("-")


def lang_badge_html(language):
    """Return a <span> badge for the given language string. Matches Phase 1 pattern exactly."""
    if not language:
        return '<span class="lang-badge border border-current px-2 py-0.5 text-[10px] font-bold opacity-40">&mdash;</span>'
    slug = language_to_slug(language)
    display_name, _, color = LANG_META.get(slug, (language, "📦", "#888888"))
    safe_name = html.escape(display_name)
    return (
        f'<span class="lang-badge border border-current px-2 py-0.5 text-[10px] font-bold '
        f'flex items-center gap-1">'
        f'<span class="w-2 h-2 flex-shrink-0" style="background:{color}"></span>'
        f'{safe_name}</span>'
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_repos(path="_data/repos.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_categories(path="_data/categories.json"):
    """Load optional categories map. Returns empty dict if file absent or malformed."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def group_by_language(repos):
    """Group repos by GitHub-reported language, sorted by total stars descending."""
    groups = defaultdict(list)
    for repo in repos:
        lang = repo.get("language") or "Other"
        groups[lang].append(repo)
    # Sort each group by stars descending (HTML-07)
    for lang in groups:
        groups[lang].sort(key=lambda r: r.get("stargazers_count") or 0, reverse=True)
    # Sort groups by total star count descending
    return dict(
        sorted(groups.items(), key=lambda kv: sum(r.get("stargazers_count") or 0 for r in kv[1]), reverse=True)
    )


def group_by_categories(repos, cat_map):
    """Group repos by the category field in cat_map (full_name → {category: ...})."""
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


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_card(repo, index, global_index):
    """Render a single repo card. global_index is used for barcode style cycling."""
    slug = language_to_slug(repo.get("language"))
    owner, _, name = repo["full_name"].partition("/")
    safe_name = html.escape(name)
    safe_desc = html.escape(repo.get("description") or "No description provided.")
    k_stars = fmt_stars(repo.get("stargazers_count"))
    lang_badge = lang_badge_html(repo.get("language"))
    barcode_style = BARCODE_STYLES[global_index % len(BARCODE_STYLES)]

    return f"""\
    <div class="flex flex-col md:flex-row">
      <a href="{repo['html_url']}" target="_blank" rel="noopener noreferrer"
         class="card-left w-full md:w-1/3 p-8 flex flex-col justify-between border-b-2 md:border-b-0 md:border-r-2 border-navy dark:border-white bg-background-light dark:bg-background-dark">
        <div>
          <div class="file-num text-[10px] font-bold text-primary mb-2">FILE: #{global_index + 1:03d}</div>
          <div class="owner-name text-[10px] uppercase opacity-50 mb-1">{html.escape(owner)}</div>
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
        <a href="{repo['html_url']}" target="_blank" rel="noopener noreferrer"
           class="mt-8 self-start cursor-pointer border-2 border-navy dark:border-white px-4 py-2 text-[10px] font-bold uppercase hover:bg-primary hover:text-white hover:border-primary transition-colors">VIEW ON GITHUB &#8599;</a>
      </div>
      <div class="hidden lg:flex w-16 border-l-2 border-navy dark:border-white flex-col justify-center items-center gap-4 py-8">
        <span class="material-icons rotate-45 text-2xl">arrow_forward</span>
        <div class="[writing-mode:vertical-lr] text-[10px] font-bold uppercase">View Repo</div>
      </div>
    </div>"""


def render_section(cat_name, repos, cat_num, global_offset):
    """Render a full category section including header and all cards."""
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


def render_sections(groups):
    """Render all category sections. Public API used by tests."""
    parts = []
    global_offset = 0
    for cat_num, (cat_name, repos) in enumerate(groups.items(), start=1):
        parts.append(render_section(cat_name, repos, cat_num, global_offset))
        global_offset += len(repos)
    return "\n".join(parts)


def render_subcategory_header(subcat_name, count, subcat_num):
    """Render a Safety Orange subcategory divider with inline repo count (D-02)."""
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


def render_sections_hierarchical(hier_groups):
    """Render all category sections with nested subcategory dividers (D-01).

    Structure per category:
      <section id="{cat_slug}"> category header (gray, Material Icon)
        <div divide-y-2>
          render_subcategory_header() [Safety Orange]
          render_card() * N
          render_subcategory_header() [Safety Orange]
          render_card() * M
        </div>
      </section>
    """
    parts = []
    global_offset = 0
    for cat_num, (cat_name, subcats) in enumerate(hier_groups.items(), start=1):
        slug = language_to_slug(cat_name)
        total_count = sum(len(r) for r in subcats.values())

        # D-06: CATEGORY_META first, then LANG_META, then fallback
        if slug in CATEGORY_META:
            display_name, icon_name = CATEGORY_META[slug]
            icon_html = f'<span class="material-icons text-lg">{icon_name}</span>'
        else:
            display_name, emoji, _ = LANG_META.get(slug, (cat_name, "📦", "#888888"))
            icon_html = f'<span class="text-lg">{emoji}</span>'

        section_lines = [
            f'<section id="{slug}" data-category="{slug}" class="border-b-2 border-navy dark:border-white">',
            f'  <div class="px-8 py-4 border-b-2 border-navy dark:border-white flex justify-between items-center',
            f'              bg-zinc-200 dark:bg-zinc-800 uppercase font-bold text-[10px]">',
            f'    <span class="flex items-center gap-3">',
            f'      {icon_html}',
            f'      <span>{html.escape(display_name.upper())} // CATEGORY_{cat_num:02d}</span>',
            f'    </span>',
            f'    <span class="text-primary">TOTAL_ENTRIES: {total_count}</span>',
            f'  </div>',
            f'  <div class="divide-y-2 divide-navy dark:divide-white">',
        ]

        for subcat_num, (subcat_name, repos) in enumerate(subcats.items(), start=1):
            section_lines.append(render_subcategory_header(subcat_name, len(repos), subcat_num))
            for i, repo in enumerate(repos):
                section_lines.append(render_card(repo, i, global_offset + i))
            global_offset += len(repos)

        section_lines.append('  </div>')
        section_lines.append('</section>')
        parts.append('\n'.join(section_lines))

    return '\n'.join(parts)


def render_nav(groups):
    """Render sidebar navigation items for all groups."""
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


def render_nav_hierarchical(hier_groups):
    """Render sidebar nav for hierarchical groups — top-level categories only (D-03)."""
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
    return '\n'.join(items)


def render_page(nav_html, sections_html, total, generated_at):
    """Render the complete HTML page. Head block is identical to Phase 1."""
    serial_date = generated_at.strftime("%Y%m%d")
    updated_str = generated_at.strftime("%Y-%m-%d %H:%M UTC")

    # Marquee: dynamic category names
    marquee_parts = []
    for line in nav_html.split("\n"):
        if "<span>" in line and "opacity-60" not in line and "href" not in line:
            # extract display name between <span> and </span>
            m = re.search(r"<span>([^<]+)</span>", line)
            if m:
                marquee_parts.append(m.group(1).strip().upper())
    marquee_text = " // ".join(marquee_parts) + " // "
    marquee_content = (marquee_text) * 4

    return f"""<!DOCTYPE html>
<html class="scroll-smooth" lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>STARS GALLERY // THERUSTYROBOT // AI-CATEGORIZED REPOS</title>
<link href="https://fonts.googleapis.com" rel="preconnect"/>
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@900&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com?plugins=forms,typography"></script>
<script>
  tailwind.config = {{
    darkMode: "media",
    theme: {{
      extend: {{
        colors: {{
          primary: "#FF5F1F",
          "background-light": "#F4F1EA",
          "background-dark": "#0D0D0D",
          navy: "#0A0A23",
        }},
        fontFamily: {{
          mono: ["'JetBrains Mono'", "monospace"],
          display: ["'Inter'", "sans-serif"],
        }},
        borderRadius: {{
          DEFAULT: "0px", sm: "0px", md: "0px", lg: "0px", full: "0px",
        }},
      }},
    }},
  }};
</script>
<style>
  .grid-bg{{background-size:40px 40px;background-image:radial-gradient(circle,currentColor 1px,transparent 1px);}}
  @keyframes marquee{{0%{{transform:translateX(0)}}100%{{transform:translateX(-25%)}}}}
  .card-left{{cursor:pointer;transition:background 0.15s,color 0.15s;}}
  .card-left:hover{{background:#FF5F1F !important;color:white !important;}}
  .card-left:hover .file-num{{color:rgba(255,255,255,0.6);}}
  .card-left:hover .owner-name{{opacity:0.65;}}
  .card-left:hover .repo-name{{color:white;}}
  .card-left:hover .lang-badge{{border-color:rgba(255,255,255,0.5);}}
  .card-left:hover .stars-badge{{background:white;color:#FF5F1F;}}
  .card-left:hover .meta-label{{background:white;color:#FF5F1F;}}
  .filter-btn{{cursor:pointer;transition:background 0.12s,color 0.12s;}}
  .filter-btn.is-active,.filter-btn:hover{{background:#FF5F1F;color:white;}}
</style>
</head>
<body class="bg-background-light dark:bg-background-dark text-navy dark:text-white font-mono selection:bg-primary selection:text-white overflow-x-hidden">

<header class="border-b-2 border-navy dark:border-white sticky top-0 bg-background-light dark:bg-background-dark z-40">
  <div class="flex flex-wrap items-center justify-between text-[10px] tracking-tighter uppercase px-4 py-2">
    <div class="flex items-center gap-6">
      <div class="font-bold flex items-center gap-2">
        <span class="bg-navy text-white dark:bg-white dark:text-black px-1">SERIAL NO:</span>
        <span class="text-primary">STARS-{serial_date}</span>
      </div>
      <div class="hidden md:block">TOTAL_REPOS: <span class="text-primary font-bold">{total}</span></div>
      <div class="hidden lg:block">STATUS: <span class="animate-pulse text-green-600">&#9679; SYSTEM_ACTIVE</span></div>
    </div>
    <div class="opacity-70">UPDATED: {updated_str}</div>
  </div>
</header>

<main>

<section class="relative min-h-[70vh] border-b-2 border-navy dark:border-white overflow-hidden">
  <div class="absolute inset-0 grid-bg opacity-10 pointer-events-none"></div>
  <div class="absolute left-0 top-0 bottom-0 w-12 border-r-2 border-navy dark:border-white flex flex-col justify-between py-8 items-center text-[10px] [writing-mode:vertical-lr] uppercase tracking-widest font-bold">
    <span>THERUSTYROBOT // GITHUB STARS // AI-CATEGORIZED</span>
    <span class="text-primary">EST. 2024 // VER: 1.0.0</span>
  </div>
  <div class="ml-12 p-8 md:p-16 flex flex-col justify-center h-full gap-8">
    <div class="bg-primary text-white p-2 md:p-4 inline-block max-w-fit mb-4">
      <div class="border-2 border-white/30 p-1 flex items-center gap-4">
        <span class="material-icons text-4xl">star</span>
        <div>
          <p class="text-2xl font-bold leading-none">STARS CATALOG</p>
          <p class="text-[10px] tracking-widest opacity-80">AI-GENERATED CLASSIFICATION // REF: GH-STARS</p>
        </div>
      </div>
    </div>
    <h1 class="text-[5rem] md:text-[10rem] lg:text-[14rem] font-display font-bold leading-[0.85] tracking-tighter uppercase">
      STARS<span class="text-primary">.</span>
    </h1>
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-8 mt-4">
      <div class="max-w-xl">
        <p class="text-2xl font-bold uppercase leading-none mb-4">AI-CATEGORIZED<br/><span class="text-primary">GITHUB STARS</span></p>
        <p class="text-sm opacity-70 max-w-md">Automatically categorized via GitHub Models. Updated daily. All repos starred by therustyrobot.</p>
      </div>
      <div class="flex flex-col gap-2 items-start md:items-end">
        <div class="flex border-2 border-navy dark:border-white">
          <div class="px-4 py-2 border-r-2 border-navy dark:border-white font-bold text-sm">TOTAL: {total}</div>
          <div class="px-4 py-2 font-bold bg-navy text-white dark:bg-white dark:text-navy uppercase text-sm">Active</div>
        </div>
        <div class="text-[10px] opacity-50 uppercase">Generated: {updated_str}</div>
      </div>
    </div>
  </div>
  <div class="absolute bottom-10 right-10 w-32 h-32 opacity-20 hidden lg:block">
    <div class="absolute top-1/2 left-0 right-0 h-px bg-current"></div>
    <div class="absolute top-0 bottom-0 left-1/2 w-px bg-current"></div>
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 border-2 border-current w-16 h-16"></div>
  </div>
</section>

<div class="flex flex-col md:flex-row min-h-screen">
  <aside class="md:w-64 border-b-2 md:border-b-0 md:border-r-2 border-navy dark:border-white
                md:sticky md:top-[45px] md:self-start md:max-h-[calc(100vh-45px)] md:overflow-y-auto
                bg-background-light dark:bg-background-dark flex-shrink-0">
    <div class="p-4 border-b-2 border-navy dark:border-white">
      <div class="text-[10px] font-bold uppercase tracking-widest mb-3 opacity-60">INDEX // CATEGORIES</div>
      <nav>
        <ul class="space-y-0">
{nav_html}
        </ul>
      </nav>
    </div>
  </aside>
  <div class="flex-1 min-w-0">
{sections_html}
  </div>
</div>

<div class="bg-primary py-3 border-b-2 border-navy dark:border-white overflow-hidden whitespace-nowrap">
  <div class="flex items-center gap-12 text-white font-bold text-2xl animate-[marquee_20s_linear_infinite]">
    <span class="uppercase">{marquee_content}</span>
  </div>
</div>

</main>

<footer class="p-4 border-t-2 border-navy dark:border-white">
  <div class="flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] font-bold uppercase opacity-60">
    <div>STARS_GALLERY // AUTO-GENERATED // DATA FROM GITHUB API</div>
    <div class="flex gap-4"><span>BUILD_V_1.0</span><span>SYSTEM_STATUS: OK</span></div>
  </div>
</footer>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

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
