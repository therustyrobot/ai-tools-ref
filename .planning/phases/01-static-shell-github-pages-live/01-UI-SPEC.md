---
phase: 1
slug: static-shell-github-pages-live
status: draft
shadcn_initialized: false
preset: none
created: 2026-04-21
---

# Phase 1 — UI Design Contract: Static Shell + GitHub Pages Live

> Visual and interaction contract for Phase 1. This phase produces `docs/index.html` — a fully styled, statically hardcoded Stitch-themed gallery page proving the aesthetic and layout before any pipeline code exists.
>
> **Primary reference:** `stitch_example/code.html` — every visual decision traces back to this file unless explicitly noted.

---

## Design System

| Property | Value | Source |
|----------|-------|--------|
| Tool | none (vanilla HTML + Tailwind CDN) | STACK.md, REQUIREMENTS.md HTML-02 |
| Preset | not applicable | — |
| Component library | none | STACK.md |
| Icon library | Material Icons CDN (`fonts.googleapis.com/icon?family=Material+Icons`) | stitch_example/code.html |
| Mono font | JetBrains Mono 400/700 from Google Fonts CDN | stitch_example/code.html |
| Display font | Inter 700 from Google Fonts CDN | stitch_example/code.html |
| CSS framework | Tailwind CDN `https://cdn.tailwindcss.com?plugins=forms,typography` | stitch_example/code.html |

### Tailwind Config Block (exact — inline `<script>` after CDN `<script>` tag)

```js
tailwind.config = {
  darkMode: "media",          // HTML-04: prefers-color-scheme only, no JS toggle in v1
  theme: {
    extend: {
      colors: {
        primary:             "#FF5F1F",  // Safety Orange
        "background-light":  "#F4F1EA",  // Off-white / Bone
        "background-dark":   "#0D0D0D",  // Deep black
        "navy":              "#0A0A23",  // Near-black for light mode text/borders
      },
      fontFamily: {
        mono:    ["'JetBrains Mono'", "monospace"],
        display: ["'Inter'",          "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0px",               // Brutalist — NO rounded corners anywhere
        sm:      "0px",
        md:      "0px",
        lg:      "0px",
        full:    "0px",
      },
    },
  },
};
```

> **Note on `darkMode`:** The stitch reference uses `darkMode: "class"` with a JS toggle. Phase 1 requirement HTML-04 explicitly specifies `prefers-color-scheme` CSS media query with **no** JS toggle. Use `darkMode: "media"` here. The JS toggle (`TOGGLE_MODE` button) from stitch is omitted in v1.

---

## Page Structure

```
┌─────────────────────────────────────────────────────┐
│ SCANLINE OVERLAY (fixed, full viewport, z-50)        │
├─────────────────────────────────────────────────────┤
│ STATUS STRIP (sticky top, z-40, full width)          │
│ SERIAL NO: STARS-[YYYYMMDD] // TOTAL_REPOS: NNN //   │
│ UPDATED: YYYY-MM-DD HH:MM UTC // STATUS: ● ACTIVE   │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│  CATEGORY    │  REPO CONTENT                        │
│  INDEX       │  (scrollable)                        │
│  SIDEBAR     │                                      │
│  (240px)     │  [Section: AI & ML]                  │
│              │    [Subcategory header]               │
│  01_AI & ML  │      [Repo card]                     │
│  02_SELF-    │      [Repo card]                     │
│    HOSTING   │      ...                             │
│  03_DEV-     │                                      │
│    TOOLS     │  [Section: Self-Hosting]             │
│  ...         │    ...                               │
│              │                                      │
├──────────────┴──────────────────────────────────────┤
│ FOOTER: BUILD_V_1.0 // SYSTEM_STATUS: OK            │
└─────────────────────────────────────────────────────┘

Mobile (< md breakpoint): sidebar stacks above content, full-width
```

---

## Spacing Scale

All values are multiples of 4. Tailwind utility class equivalents are shown.

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| xs | 4px | `p-1`, `gap-1` | Icon-to-text gaps, badge inner padding |
| sm | 8px | `p-2`, `gap-2` | Compact element spacing, status strip py |
| md | 16px | `p-4`, `gap-4` | Default card padding, nav item px |
| lg | 24px | `p-6`, `gap-6` | Section header padding |
| xl | 32px | `p-8`, `gap-8` | Card section padding, sidebar py |
| 2xl | 48px | `p-12` | Major section top padding |
| 3xl | 64px | `p-16` | Page-level outer padding (desktop) |

**Exceptions:**
- Status strip: `px-4 py-2` (16px / 8px) — matches stitch header exactly
- Micro-label gaps: `gap-2` to `gap-6` within the strip flex row
- Touch targets: minimum 44px height for any interactive element (sidebar nav links use `py-2 px-4` = 8px+16px inner; ensure rendered height ≥ 44px via `min-h-[44px]`)
- Border widths: always `border-2` (2px) — never 1px, never 3px

---

## Typography

All text uses `font-mono` (JetBrains Mono) except explicit display headings.

| Role | Size | Tailwind | Weight | Line Height | Font | Usage |
|------|------|----------|--------|-------------|------|-------|
| Micro label | 10px | `text-[10px]` | 700 | 1.2 | mono | Status strip fields, badge prefixes, metadata keys, nav index numbers, section counts, timestamps |
| Body / Description | 14px | `text-sm` | 400 (prose) / 700 (labels) | 1.5 (prose) / 1.3 (labels) | mono | Repo description text (400); repo name links, section header text, nav category names (700) |
| Section heading | 24px | `text-2xl` | 700 | 1.1 | mono | Category/subcategory section header bands |
| Page display | 48px+ | `text-5xl` (desktop) | 700 | 0.9 | display (Inter) | Page title only — "STARS GALLERY" or equivalent |

**Rules:**
- ALL text is `uppercase` except repo description body text and repo names
- Letter spacing on labels/headings: `tracking-tighter` or `tracking-widest` (match stitch pattern)
- Text selection: `selection:bg-primary selection:text-white` on `<body>`
- No italic text anywhere (brutalist aesthetic)

---

## Color

### Dark Mode (Primary — `@media (prefers-color-scheme: dark)`)

> **Split: ~60% `background-dark` (#0D0D0D) / ~30% navy borders + zinc card surfaces / ~10% primary accent (#FF5F1F).**

| Role | Value | Tailwind Token | Usage |
|------|-------|---------------|-------|
| Page background | `#0D0D0D` | `dark:bg-background-dark` | `<body>` background |
| Card / sidebar bg | `#18181B` | `dark:bg-zinc-900` | Repo cards, sidebar column |
| Section header band | `#27272A` | `dark:bg-zinc-800` | Section label bars ("TECHNICAL_FILINGS" pattern) |
| Primary text | `#FFFFFF` | `dark:text-white` | All body text |
| Secondary text | `rgba(255,255,255,0.6)` | `dark:opacity-60` | Metadata, descriptions |
| Border | `#FFFFFF` | `dark:border-white` | All `border-2` elements |
| Accent | `#FF5F1F` | `text-primary` / `bg-primary` | See "Accent reserved for" below |
| Status pulse | `#16A34A` | `text-green-600` | SYSTEM_ACTIVE pulse dot only |

### Light Mode (Secondary — `@media (prefers-color-scheme: light)`)

| Role | Value | Tailwind Token | Usage |
|------|-------|---------------|-------|
| Page background | `#F4F1EA` | `bg-background-light` | `<body>` background |
| Card / sidebar bg | `#E5E2DA` | `bg-stone-200` approx | Repo cards, sidebar |
| Section header band | `#D4D0C8` | `bg-stone-300` approx | Section bars |
| Primary text | `#0A0A23` | `text-navy` | All body text |
| Secondary text | `rgba(10,10,35,0.6)` | `opacity-60` | Metadata |
| Border | `#0A0A23` | `border-navy` | All `border-2` elements |
| Accent | `#FF5F1F` | same | Same accent rules |

### Accent Reserved For (10% rule — exhaustive list)

`#FF5F1F` Safety Orange is ONLY used on:

1. Repo name link hover state (`hover:text-primary`)
2. Category nav item hover/active state background (`hover:bg-primary hover:text-white`)
3. Status strip "PROJECT ID" value text (`text-primary`)
4. Section count badge text (`text-primary`)
5. Star count `★` glyph and K-formatted number in repo cards
6. Language badge color dot — **only** for languages whose GitHub color maps to an orange family (Rust: `#DEA584`, see language map below)
7. Scanline overlay color: `rgba(255, 95, 31, 0.1)` — per stitch_example CSS
8. Text selection highlight: `selection:bg-primary`
9. Accent warning/spec label blocks (stitch "SPECIFICATION SHEET" banner style)

**Never use `#FF5F1F` for:** general borders, backgrounds, body text, language dots (except Rust family), nav items in default state.

### Scanline CSS (copy verbatim from stitch_example)

```css
.scanline {
  width: 100%;
  height: 2px;
  background: rgba(255, 95, 31, 0.1);
  position: fixed;
  z-index: 50;
  pointer-events: none;
  animation: scan 8s linear infinite;
}
@keyframes scan {
  0%   { top: 0; }
  100% { top: 100%; }
}
```

### Grid Background Texture (optional decorative — use on hero/header only)

```css
.grid-bg {
  background-size: 40px 40px;
  background-image: radial-gradient(circle, currentColor 1px, transparent 1px);
}
/* Apply: class="grid-bg opacity-10 pointer-events-none" */
```

---

## Language Color Map

Static 15-language map. Applied as an inline colored `<span>` dot (`w-2 h-2` square — NOT a circle, `border-radius: 0px` enforced) before the language text badge.

| Language | Dot Color | Hex |
|----------|-----------|-----|
| Python | Blue | `#3572A5` |
| TypeScript | Dark blue | `#2B7489` |
| JavaScript | Yellow | `#F1E05A` |
| Go | Cyan | `#00ADD8` |
| Rust | Peach | `#DEA584` |
| Shell | Green | `#89E051` |
| C | Gray | `#555555` |
| C++ | Pink | `#F34B7D` |
| Java | Amber | `#B07219` |
| Ruby | Red | `#CC342D` |
| Swift | Light orange | `#FFAC45` |
| Kotlin | Purple | `#A97BFF` |
| Vue | Teal | `#41B883` |
| Svelte | Red-orange | `#FF3E00` |
| Zig | Burnt orange | `#EC915C` |
| (unknown / null) | White/gray | `currentColor opacity-30` |

Language badge markup pattern:
```html
<span class="flex items-center gap-1 text-[10px] font-bold uppercase border border-current px-1">
  <span class="w-2 h-2 flex-shrink-0" style="background-color: #3572A5;"></span>
  Python
</span>
```

---

## Component Specifications

### Scanline Overlay

```html
<div class="scanline"></div>
<!-- Placed as first child of <body>, before all other elements -->
```
Fixed, full-width, z-50, pointer-events-none. Defined in `<style>` block per stitch_example.

---

### Status Strip (HTML-05)

**Placement:** Sticky top (`sticky top-0 z-40`), full width, below scanline in z-order.

**Border:** `border-b-2 border-navy dark:border-white`

**Background:** Same as page bg (`bg-background-light dark:bg-background-dark`)

**Layout:** `flex flex-wrap items-center justify-between px-4 py-2 text-[10px] tracking-tighter uppercase font-bold`

**Left side fields:**
1. `SERIAL NO:` label (inverted badge: `bg-navy text-white dark:bg-white dark:text-black px-1`) + value `STARS-[YYYYMMDD]`
2. `REPO COUNT:` + value (Safety Orange, bold) — hardcoded `370` for Phase 1
3. `STATUS:` + `● SYSTEM_ACTIVE` (animate-pulse, text-green-600)

**Right side fields:**
4. `UPDATED:` + timestamp value `YYYY-MM-DD HH:MM UTC` — hardcoded for Phase 1

**Copywriting:** See Copywriting Contract section.

---

### Category Sidebar Nav (HTML-06)

**Character:** Brutalist index — looks like a numbered document filing index, NOT a typical nav menu.

**Layout:** Fixed-width left column (`w-60` = 240px desktop). `border-r-2 border-navy dark:border-white`. On mobile (`< md`): full-width, stacks above content, `border-b-2` replaces `border-r-2`.

**Sidebar heading band:**
```html
<div class="px-4 py-2 border-b-2 border-navy dark:border-white bg-navy text-white dark:bg-white dark:text-black text-[10px] font-bold uppercase tracking-widest">
  INDEX // CATEGORIES
</div>
```

**Category nav item:**
```html
<a href="#ai-ml" class="flex items-center gap-2 px-4 py-2 min-h-[44px] text-[10px] font-bold uppercase tracking-tight hover:bg-primary hover:text-white transition-colors border-b border-navy/20 dark:border-white/20">
  <span class="text-primary text-[10px]">01</span>
  🤖 AI &amp; ML
  <span class="ml-auto text-[10px] opacity-60">120</span>
</a>
```

- Index number: Safety Orange micro text (`text-primary text-[10px]`)
- Emoji marker: one per top-level category (see emoji map below)
- Category name: 10px uppercase bold
- Repo count: right-aligned micro text, 60% opacity
- Active state / hover: `bg-primary text-white` (orange fill)
- Subcategory items (if nested): indented `pl-8`, 10px, no emoji, lighter weight

**Category Emoji Map:**
```
ai-ml              → 🤖
self-hosting       → 🏠
dev-tools          → 🛠️
devops-infra       → ⚙️
databases          → 🗄️
security           → 🔐
web-frontend       → 🌐
mobile             → 📱
data-science       → 📊
languages-runtimes → 💻
productivity       → ⚡
learning-reference → 📚
misc               → 📦
```

---

### Repo Card (HTML-05)

**Container:** `border-b-2 border-navy dark:border-white px-4 py-4` (no rounded corners, no card shadow, just borders)

**Dark mode bg:** transparent (inherits page or section bg)

**Layout:** vertical stack

```html
<article class="border-b-2 border-navy dark:border-white px-4 py-4 hover:bg-zinc-900/30 dark:hover:bg-zinc-800/30 transition-colors">

  <!-- Row 1: Repo name + star count -->
  <div class="flex items-start justify-between gap-4 mb-1">
    <a href="https://github.com/owner/repo"
       target="_blank" rel="noopener noreferrer"
       class="text-sm font-bold uppercase hover:text-primary transition-colors leading-tight">
      owner/repo-name
    </a>
    <span class="text-[10px] font-bold text-primary whitespace-nowrap flex-shrink-0">
      ★ 12.4K
    </span>
  </div>

  <!-- Row 2: Description -->
  <p class="text-sm opacity-70 mb-2 leading-relaxed">
    Short description of what this repo does.
  </p>

  <!-- Row 3: Language badge -->
  <div class="flex items-center gap-2">
    <span class="flex items-center gap-1 text-[10px] font-bold uppercase border border-current px-1 py-0.5">
      <span class="w-2 h-2 flex-shrink-0" style="background-color: #3572A5;"></span>
      Python
    </span>
  </div>

</article>
```

**Star count format rules:**
- `< 1000`: display raw integer (e.g. `847`)
- `≥ 1000 < 1,000,000`: format as `12.4K` (round to 1 decimal, strip trailing `.0`)
- `≥ 1,000,000`: format as `1.2M`
- Always prefixed with `★` glyph
- Color: `text-primary` (Safety Orange)

---

### Section Header (Phase 2 full implementation; Phase 1 hardcode)

```html
<div class="px-4 py-2 border-b-2 border-navy dark:border-white flex justify-between items-center bg-zinc-200 dark:bg-zinc-800 uppercase font-bold text-[10px]">
  <span>🤖 AI &amp; ML // SUBCATEGORY_NAME</span>
  <span class="text-primary">ENTRIES: 12</span>
</div>
```

Section `id` attribute: lowercase-hyphenated slug matching category nav `href`. e.g. `id="ai-ml"`, `id="self-hosting"`.

---

### Page Footer

```html
<footer class="border-t-2 border-navy dark:border-white px-4 py-4">
  <div class="flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] font-bold uppercase opacity-60">
    <div>STARS_GALLERY // AUTO-GENERATED // ALL DATA FROM GITHUB API</div>
    <div class="flex gap-4">
      <span>BUILD_V_1.0</span>
      <span>SYSTEM_STATUS: OK</span>
    </div>
  </div>
</footer>
```

---

## Copywriting Contract

| Element | Copy | Notes |
|---------|------|-------|
| Page `<title>` | `STARS GALLERY // [OWNER] // AI-CATEGORIZED REPOS` | Use actual GitHub username |
| Status: Serial No value | `STARS-YYYYMMDD` | Date injected at generation; hardcoded for Phase 1 e.g. `STARS-20260421` |
| Status: Repo count label | `TOTAL_REPOS:` | Followed by count as Safety Orange value |
| Status: Repo count value | `370` | Hardcoded for Phase 1 |
| Status: Updated label | `UPDATED:` | Followed by timestamp |
| Status: Updated value | `2026-04-21 06:00 UTC` | Hardcoded for Phase 1; UTC always |
| Status: System state | `● SYSTEM_ACTIVE` | Pulsing green dot + uppercase text; never lowercase |
| Sidebar heading | `INDEX // CATEGORIES` | All caps, double-slash separator |
| Section header pattern | `🤖 AI & ML // CLAUDE_CODE` | Emoji + category + double-slash + subcategory |
| Section count label | `ENTRIES: N` | Right-aligned, Safety Orange; e.g. `ENTRIES: 12` |
| Empty category state | `NO ENTRIES // DATA PENDING` | For any hardcoded category with 0 repos |
| Repo link rel | — | Always `target="_blank" rel="noopener noreferrer"` — no copy shown |
| Footer identity | `STARS_GALLERY // AUTO-GENERATED // ALL DATA FROM GITHUB API` | All caps |
| Footer build | `BUILD_V_1.0` | Increment per release |
| Footer status | `SYSTEM_STATUS: OK` | Always OK for a successfully served page |

**Destructive actions:** None in Phase 1 — this is a fully read-only gallery. No forms, no buttons that modify state, no deletion patterns.

**Error states:** This is a static pre-rendered page; runtime errors cannot occur. The only "error" scenario is the page not loading, which is handled by GitHub Pages (returns a GitHub 404 page). No error state copy needed in the HTML itself.

**Tone rules:**
- All labels: UPPERCASE with underscores replacing spaces (`TOTAL_REPOS` not `Total Repos`)
- Double-slash `//` as the separator between label and value in status strip
- No periods, no sentence case for UI labels
- Repo descriptions: sentence case, no trailing period (following `starred_repos.md` convention)

---

## Interaction Contract

This is a read-only static page. All interactions are pure CSS — no JavaScript required in Phase 1.

| Interaction | Trigger | Behavior | Implementation |
|-------------|---------|----------|----------------|
| Repo link click | `<a href>` click | Opens GitHub repo in new tab | `target="_blank" rel="noopener noreferrer"` |
| Category nav link click | `<a href="#slug">` click | Smooth-scrolls to section | `<html class="scroll-smooth">` + CSS anchor |
| Nav item hover | CSS `:hover` | Background → `#FF5F1F`, text → white | `hover:bg-primary hover:text-white transition-colors` |
| Repo card hover | CSS `:hover` | Subtle bg tint | `hover:bg-zinc-900/30 dark:hover:bg-zinc-800/30 transition-colors` |
| Repo name hover | CSS `:hover` | Text → Safety Orange | `hover:text-primary transition-colors` |
| Scanline | CSS animation | 2px orange line sweeps viewport top→bottom every 8s | `.scanline` class, `animation: scan 8s linear infinite` |
| Text selection | CSS `::selection` | Orange bg, white text | `selection:bg-primary selection:text-white` on `<body>` |
| Dark mode | `prefers-color-scheme: dark` | Full dark theme activates | `darkMode: "media"` in tailwind config; `dark:` prefixes |
| Status pulse | CSS animation | Green dot pulses | `animate-pulse text-green-600` on `● SYSTEM_ACTIVE` span |

**No JavaScript interactions in Phase 1.** No toggle buttons, no accordions, no modals, no sorting controls.

---

## Responsive Behavior

| Breakpoint | Tailwind | Behavior |
|------------|----------|----------|
| Mobile default | `< 768px` (< `md`) | Single column. Sidebar stacks above content as full-width horizontal scroll nav OR collapsed index list. Border changes from `border-r-2` to `border-b-2`. |
| Tablet / Desktop | `≥ 768px` (`md:`) | Two-column layout: `w-60` sidebar + `flex-1` content. |
| Large desktop | `≥ 1024px` (`lg:`) | Same two-column layout, content area gains more horizontal padding. |

Mobile nav: display as horizontal scrollable strip OR full-width stacked list — both acceptable for Phase 1. Sidebar items shrink to micro text or just numbered index.

---

## HTML Structure Skeleton

```html
<!DOCTYPE html>
<html class="scroll-smooth" lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>STARS GALLERY // [OWNER] // AI-CATEGORIZED REPOS</title>
  <!-- Google Fonts: JetBrains Mono 400/700 + Inter 700 -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@700&display=swap" rel="stylesheet" />
  <!-- Material Icons -->
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet" />
  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com?plugins=forms,typography"></script>
  <script>/* tailwind.config block — see Design System section above */</script>
  <style>/* scanline + grid-bg — see Scanline CSS above */</style>
</head>
<body class="bg-background-light dark:bg-background-dark text-navy dark:text-white font-mono selection:bg-primary selection:text-white overflow-x-hidden">

  <!-- Scanline overlay -->
  <div class="scanline"></div>

  <!-- Status strip (sticky) -->
  <header class="sticky top-0 z-40 border-b-2 border-navy dark:border-white bg-background-light dark:bg-background-dark">
    <!-- SERIAL NO // REPO COUNT // STATUS // UPDATED -->
  </header>

  <!-- Page body: sidebar + content -->
  <div class="flex flex-col md:flex-row min-h-screen">

    <!-- Category sidebar -->
    <nav class="w-full md:w-60 border-b-2 md:border-b-0 md:border-r-2 border-navy dark:border-white flex-shrink-0">
      <!-- INDEX // CATEGORIES heading band -->
      <!-- Category nav items with anchor links -->
    </nav>

    <!-- Repo content -->
    <main class="flex-1">
      <!-- Category sections with section[id="slug"] -->
      <!-- Subcategory headers + repo card lists -->
    </main>

  </div>

  <!-- Footer -->
  <footer class="border-t-2 border-navy dark:border-white px-4 py-4">
    <!-- BUILD_V_1.0 // SYSTEM_STATUS: OK -->
  </footer>

</body>
</html>
```

---

## Sample Data for Phase 1 Hardcoding

Phase 1 uses hardcoded sample repos (≥ 10 cards required by success criteria). Use these real repos from `starred_repos.md` as representative samples:

| Repo | Stars | Language | Category |
|------|-------|----------|----------|
| `anthropics/claude-code` | 12.4K | TypeScript | AI & ML |
| `microsoft/autogen` | 42K | Python | AI & ML |
| `ollama/ollama` | 162K | Go | Self-Hosting |
| `caddyserver/caddy` | 62K | Go | DevOps & Infra |
| `sharkdp/bat` | 55K | Rust | Dev Tools & CLI |
| `neovim/neovim` | 88K | C | Dev Tools & CLI |
| `BerriAI/litellm` | 21K | Python | AI & ML |
| `continuedev/continue` | 24K | TypeScript | AI & ML |
| `netdata/netdata` | 75K | C | Self-Hosting |
| `sindresorhus/awesome` | 350K | — | Learning & Reference |
| `golang/go` | 125K | Go | Languages & Runtimes |
| `rust-lang/rust` | 102K | Rust | Languages & Runtimes |

Display across at least 3 category sections to prove the nav and layout work.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable — no shadcn |
| Tailwind CDN | framework only | CDN integrity: none (matches stitch_example exactly) |
| Google Fonts CDN | JetBrains Mono + Inter + Material Icons | CDN integrity: none (standard Google Fonts, no JS) |

No third-party component registries. No npm packages. No pip packages for this phase. All assets are CDN-loaded at runtime.

---

## Files Produced by Phase 1

| File | Purpose |
|------|---------|
| `docs/index.html` | Single output — the complete styled page; committed to git |
| `.gitignore` | Must contain `_data/` entry (SETUP-04) |

No other files are created in Phase 1.

---

## Pre-Population Sources

| Decision | Source |
|----------|--------|
| Safety Orange `#FF5F1F` | stitch_example/code.html tailwind.config + REQUIREMENTS HTML-03 |
| Deep black `#0D0D0D` | stitch_example/code.html tailwind.config |
| Off-white `#F4F1EA` | stitch_example/code.html tailwind.config |
| JetBrains Mono + Inter fonts | stitch_example/code.html `<link>` tags |
| `borderRadius: DEFAULT: "0px"` | stitch_example/code.html tailwind.config |
| Scanline CSS (exact) | stitch_example/code.html `<style>` block |
| `darkMode: "media"` (not "class") | REQUIREMENTS HTML-04 explicit override of stitch |
| Status strip pattern | stitch_example/code.html `<header>` band |
| Category nav = sidebar, not top menu | REQUIREMENTS HTML-06 + PROJECT.md explicit |
| K-formatted star counts | REQUIREMENTS HTML-06 + FEATURES.md |
| Language color map (15 languages) | REQUIREMENTS HTML-06 |
| `target="_blank" rel="noopener noreferrer"` | REQUIREMENTS HTML-06 |
| No JS interactions | REQUIREMENTS HTML-04 + PROJECT.md constraints |
| Tailwind CDN (not CLI build) | REQUIREMENTS HTML-02 + STACK.md |
| Material Icons from Google CDN | stitch_example/code.html `<link>` |
| Selection highlight orange | stitch_example/code.html `<body>` class |
| Grid-bg texture pattern | stitch_example/code.html `<style>` block |
| `scroll-smooth` on `<html>` | stitch_example/code.html `class` attribute |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
