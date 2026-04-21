# Feature Landscape: GitHub Stars Gallery

**Domain:** Personal GitHub stars showcase / bookmarks gallery (static, auto-updating)
**Researched:** 2026-04-21
**Sources:** PROJECT.md requirements, starred_repos.md (370 repos, 13+ top-level categories, 30+ subcategories), stitch_example/code.html aesthetic reference, GitHub stars gallery conventions

---

## Context

This is a single-owner, read-only, static HTML page hosted on GitHub Pages. It displays ~370 starred repos organized into AI-generated categories, regenerated daily by a GitHub Action. The design aesthetic is Brutalist Stitch: JetBrains Mono, Safety Orange (#FF5F1F), sharp corners, dark mode, scanline animation.

**Key constraints driving feature decisions:**
- Static HTML only — no server, no runtime JS framework
- No search/filter bar — already explicitly out of scope in PROJECT.md
- Category navigation is embedded in layout, not a top-header nav
- All data is pre-baked at build time; no client-side GitHub API calls

---

## Table Stakes

Features users expect on any curated-list page. Missing = page feels broken or unfinished.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Repo cards with name (linked), star count, language, description** | Core function of a stars gallery — matches GitHub's own list view | Low | Already in PROJECT.md Active requirements. Link must open GitHub in new tab. |
| **Hierarchical category navigation** | 370 repos across 13+ categories — without nav users must scroll blindly | Medium | Already in PROJECT.md. Must be embedded in layout (not header). Anchor links to section IDs. Nested sub-categories (e.g., AI & ML → Claude Code & Skills). |
| **Dark mode** | Standard expectation for a dev-audience page; Stitch theme requires it | Low | Already in PROJECT.md. CSS class-based (`dark:` Tailwind) — toggle button or system default. |
| **Responsive layout** | ~50%+ of casual reference checks happen on mobile | Medium | Stitch aesthetic works well with single-column on mobile, sidebar nav collapsing to top accordion. |
| **Total repo count displayed prominently** | Users want to gauge scale immediately ("370 repos") | Low | One number, styled as a stitch "TOTAL_ENTRIES" stamp near the top. Build script injects count at generation time. |
| **Last updated timestamp** | Automated daily generation — users need to know data freshness | Low | Single line: "UPDATED: 2026-04-21 // AUTO-GENERATED". Injected by build script. |
| **Star count K-formatting** | "162K" is human-readable; raw "162000" is not | Low | Format in build script: ≥1000 → round to 1 decimal K/M. |
| **External links open in new tab** | Standard for reference/bookmark pages — don't navigate away | Low | `target="_blank" rel="noopener noreferrer"` on all repo links. |

---

## Differentiators

Features that distinguish this gallery from a plain GitHub stars list or a raw markdown file.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI-generated, daily-updated taxonomy** | The whole page recategorizes itself every day — zero maintenance | High (already scoped) | Core differentiator; already in PROJECT.md. GitHub Models via GITHUB_TOKEN in Actions. |
| **Brutalist Stitch aesthetic** | Visually striking vs generic card grids — memorable, distinctive, on-brand | Medium (already scoped) | Safety Orange, JetBrains Mono, scanline animation, sharp borders, "INTERNAL USE ONLY" stamping, all already specified. |
| **Category repo counts** | "AI & ML (120)" — immediately conveys density per category without clicking in | Low | Computed at build time. Styled as stitch's `TOTAL_ENTRIES: 03` label beside each section header. |
| **Repos sorted by star count (descending) within each category** | Surfaces the most battle-tested tools first — eliminates manual scanning | Low | Sorted in build script; no runtime JS needed. Matches how starred_repos.md already presents data. |
| **Language color dots** | GitHub-style colored circle before language badge makes scanning faster | Low | Static color map for top 15 languages (Python=blue, TypeScript=blue, Go=cyan, Rust=orange, Shell=green, etc.) baked into CSS/HTML. |
| **Sticky sidebar category navigation** | For a 370-repo page, losing your place is the #1 frustration | Medium | CSS `position: sticky` or a fixed side column with overflow-y scroll. No JS required for basic stickiness. Category list scrolls independently from content. |
| **Page status strip (stitch-style header)** | Communicates identity + data freshness in one branded band | Low | "SERIAL NO: STARS-[DATE] // STATUS: ● SYSTEM_ACTIVE // TOTAL_REPOS: 370". Pure HTML/CSS, built from stitch header pattern. |
| **"NEW" badges on recently-added repos** | Highlights what changed since last run — turns a static page into a feed | Medium | Build script compares current repo IDs against previous run's list (stored as a JSON artifact in Actions). Adds `NEW` badge class if first seen within last 7 days. Requires storing previous state. |
| **Category icons / emoji markers** | Visual anchor for quick scanning, especially at small screen widths | Low | Single emoji or Unicode symbol per top-level category (🤖 AI & ML, 🏠 Self-Hosting, 🛠️ Dev Tools, etc.). Defined in build config, not AI-generated. |

---

## Anti-Features

Things to deliberately **not** build, with rationale.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Search / filter bar** | Explicitly out of scope in PROJECT.md. Adds JS complexity, index files, and maintenance burden for marginal gain — category nav covers navigation intent | Use category navigation + browser Ctrl+F for power users |
| **Client-side live GitHub API calls** | Blows through unauthenticated rate limits instantly; leaks access patterns; introduces latency on page load | All data baked into HTML at build time via the GitHub Action |
| **JavaScript SPA framework (React, Vue, Svelte)** | Incompatible with the static HTML + GitHub Pages constraint; adds build pipeline complexity | Vanilla HTML generated by Python build script with Tailwind CDN |
| **Pagination** | Defeats the purpose — a single-page reference lets users Ctrl+F and bookmark anchors | Single long scrollable page; sticky nav handles orientation |
| **Interactive sorting / filtering controls** | Requires JS state management; conflicts with static HTML constraint | Sort by stars at build time (highest first); order is deterministic |
| **Social features (comments, reactions, forks)** | Read-only reference page — adding social creates moderation overhead | None; it's a personal bookmark page |
| **Multiple GitHub accounts** | Architectural complexity for zero stated need | Single account only (the repo owner's stars) |
| **Backend / database** | GitHub Pages is static; no server-side code | Everything pre-baked; GitHub Actions + GitHub API are the "backend" |
| **User authentication / login** | Public read-only page; no private data | None required |
| **Tag cloud / global tag system** | Requires a parallel taxonomy to the AI-generated categories; maintenance burden | AI categories serve this purpose |
| **Infinite scroll** | JS-dependent; breaks browser anchor navigation | Single full-page render; CSS column layout handles density |
| **Repo READMEs inlined / expanded** | Page size would balloon to megabytes; every click goes to GitHub anyway | Link out to GitHub for full details |

---

## Feature Dependencies

```
GitHub API data (name, stars, language, description, homepage)
  └── Repo cards                   (requires: name, stars, language, description)
        └── Star count K-format    (requires: raw star count integer)
        └── Language color dots    (requires: language string)

AI categorization (GitHub Models)
  └── Category structure           (requires: AI output with category/subcategory labels)
        └── Category navigation    (requires: category structure with section IDs)
        └── Category repo counts   (requires: category structure + repo list per category)
        └── Sorted repo lists      (requires: repos grouped by category + star counts)
        └── Category icons/emoji   (requires: stable top-level category names → config map)

Build script (Python, runs in GitHub Action)
  └── Total repo count             (requires: full repo list)
  └── Last updated timestamp       (requires: build timestamp)
  └── Page status strip            (requires: count + timestamp)
  └── K-formatted star counts      (requires: raw integers)
  └── Language color dots          (requires: language → color map)
  └── "NEW" badges                 (requires: previous run's repo ID list as artifact)

CSS / Stitch aesthetic
  └── Dark mode toggle             (requires: Tailwind dark: classes + JS toggle or prefers-color-scheme)
  └── Sticky sidebar nav           (requires: CSS position:sticky on nav column)
  └── Scanline animation           (requires: CSS @keyframes, already in stitch_example)
  └── Responsive layout            (requires: Tailwind responsive breakpoints)
```

---

## MVP Recommendation

The minimum viable page that delivers the core value proposition ("browsable, auto-updating gallery"):

**Must ship in MVP:**
1. Repo cards (name/link, star count K-formatted, language badge, description)
2. Hierarchical category navigation with anchor links
3. Dark mode (system default via `prefers-color-scheme` + manual toggle)
4. Total repo count + last updated timestamp in stitch status strip
5. Repos sorted by star count descending within each category
6. Language color dots (static color map, ~15 languages)
7. Brutalist Stitch aesthetic (scanlines, Safety Orange, JetBrains Mono, sharp borders)
8. Responsive layout (sidebar nav collapses on mobile)
9. Category repo counts beside section headers

**Defer post-MVP:**
- **"NEW" badges** — requires persisting previous-run artifact; adds build complexity. Ship after the daily Action is proven reliable.
- **Sticky sidebar** — CSS-only is achievable but layout gets complex on mobile; defer to polish pass.
- **Category icons/emoji** — purely cosmetic; add in a style pass after content is confirmed working.

---

## Sources

- `PROJECT.md` — authoritative requirements, constraints, out-of-scope decisions (HIGH confidence)
- `starred_repos.md` — 370-repo reference dataset demonstrating actual category taxonomy (HIGH confidence)
- `stitch_example/code.html` — Stitch aesthetic implementation reference (HIGH confidence)
- Domain conventions: GitHub Explore, Awesome lists, personal stars pages (MEDIUM confidence — pattern-matched from common implementations)
