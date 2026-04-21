# Phase 1: Static Shell + GitHub Pages Live — Research

**Researched:** 2026-04-21
**Domain:** Static HTML authoring · GitHub Pages hosting · Tailwind CDN · Brutalist CSS
**Confidence:** HIGH — all implementation details derive from verified in-repo sources (stitch_example, UI-SPEC, REQUIREMENTS) and official GitHub Pages documentation patterns. No framework APIs to track.

---

## Summary

Phase 1 is a pure authoring phase: write one file (`docs/index.html`), configure GitHub Pages to serve it, add `_data/` to `.gitignore`. Zero Python, zero pipeline, zero automation — just proving the aesthetic and hosting work before any pipeline code exists.

All visual decisions are already locked in `01-UI-SPEC.md`, which traces every choice back to `stitch_example/code.html` or an explicit REQUIREMENTS override. The research job here is to extract the exact implementation-ready details a planner needs: the verbatim Tailwind config, the precise GitHub Pages setup sequence, the hardcoded sample data set, the K-formatting algorithm, the language color map, the HTML skeleton, and the git operations required.

**One critical delta from the stitch reference:** `stitch_example/code.html` uses `darkMode: "class"` with a JS toggle button. Phase 1 requirement HTML-04 overrides this to `darkMode: "media"` — system preference only, no JS toggle. The planner must not copy the stitch `TOGGLE_MODE` button pattern.

**Primary recommendation:** Write `docs/index.html` in one pass using the exact skeleton from UI-SPEC.md, hardcode the 12 sample repos with pre-computed K-formatted strings, enable GitHub Pages via `gh` CLI or repo Settings UI, verify with `curl -I`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Visual rendering (Stitch theme, dark mode, scanline) | Browser / Client | — | Pure CSS + Tailwind CDN; no server processing |
| Page structure & content | Static file (`docs/index.html`) | — | Single committed artifact, no runtime generation in Phase 1 |
| Font loading | CDN (Google Fonts) | — | External CDN; no build step |
| CSS framework | CDN (Tailwind CDN) | — | Inline config, browser-evaluated; no purge step needed at this scale |
| Hosting | CDN / Static (GitHub Pages) | — | Pages serves `docs/` root directly from `main` branch |
| Dark mode | Browser / Client | — | `prefers-color-scheme` CSS media query; zero JS |
| Category navigation | Browser / Client | — | CSS `scroll-smooth` + HTML anchor links; zero JS in Phase 1 |
| `.gitignore` configuration | Repo config | — | One-line addition; no runtime impact |

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SETUP-01 | ⚠️ Prerequisite note — repo must be on the account that owns the starred repos | Documented constraint; Phase 1 is purely local authoring and is unblocked regardless of account |
| SETUP-02 | GitHub Pages enabled to serve from `docs/` on `main` branch | Exact setup sequence documented below; `gh` CLI command provided |
| SETUP-03 | `_data/` added to `.gitignore` | Currently `.gitignore` only contains `.DS_Store`; need one-line addition |
| SETUP-04 | Initial `docs/index.html` committed so Pages has a valid entry point | `docs/` directory does not yet exist; Phase 1 creates it |
| HTML-02 | Tailwind CDN + inline config + Google Fonts CDN; no build step | Exact config block extracted from UI-SPEC.md; verified against stitch_example |
| HTML-03 | Stitch brutalist aesthetic: Safety Orange, deep black, sharp corners, scanline | All tokens verified in stitch_example; scanline CSS extracted verbatim |
| HTML-04 | Dark mode via `prefers-color-scheme`; no JS toggle | **Delta from stitch_example**: use `darkMode: "media"` not `"class"`; omit TOGGLE_MODE button |
| HTML-05 | Status strip: serial no, repo count, last-updated timestamp, status indicator | Full markup pattern documented in UI-SPEC.md; hardcoded values for Phase 1 specified |
| HTML-06 | Repo cards: name link, K-formatted stars, language dot, description | K-format algorithm + language color map + card markup all extracted below |
</phase_requirements>

---

## Standard Stack

### Core (Phase 1 — zero install required)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Tailwind CSS CDN | 3.x (`cdn.tailwindcss.com?plugins=forms,typography`) | Utility-first CSS | Zero build step; matches stitch_example exactly; inline `tailwind.config` supports all custom tokens |
| Google Fonts CDN | — | JetBrains Mono 400/700 + Inter 700 + Material Icons | Already used in stitch_example; no font files to manage |
| Vanilla HTML5 | — | Page structure | No framework; single file committed directly to Pages |

### No Dependencies to Install

```
Phase 1 has zero npm packages, zero pip packages, zero node_modules.
All assets are CDN-loaded at browser runtime.
The only "install" step is enabling GitHub Pages in repo settings.
```

---

## Architecture Patterns

### System Architecture Diagram

```
[Browser]
    │
    ├─ GET https://therustyrobot.github.io/ai-tools-ref/
    │         │
    │   [GitHub Pages CDN]
    │         │ serves
    │   [docs/index.html] ──────────────────────────────────────────────────────┐
    │         │ references                                                        │
    │         ├─ fonts.googleapis.com (JetBrains Mono, Inter, Material Icons)    │
    │         ├─ cdn.tailwindcss.com?plugins=forms,typography                    │
    │         └─ (all page content is inline — no other external dependencies)   │
    │                                                                             │
    │   [tailwind.config inline] → evaluates theme tokens → applies dark:        │
    │   [scanline CSS @keyframes] → CSS animation, no JS                         │
    │   [prefers-color-scheme: dark] → triggers dark: Tailwind variants          │
    │   [<html scroll-smooth>] → CSS-driven anchor navigation                   │
    │                                                                             │
    └─── Page displayed to user                                                  │
                                                                                  │
[Git workflow]                                                                    │
    git add docs/index.html                                                       │
    git add .gitignore                                                            │
    git commit → git push → GitHub Pages re-deploys (docs/ root, main branch) ───┘
```

### Recommended Project Structure (Phase 1 output)

```
ai-tools-ref/
├── docs/
│   └── index.html          # ONLY output file — the complete styled page
├── stitch_example/
│   └── code.html           # Reference implementation (read-only)
├── .gitignore              # Must contain _data/ entry
└── .planning/              # Planning artifacts (not served)
```

### Pattern 1: GitHub Pages from `docs/` Directory

**What:** Configure Pages to serve `docs/index.html` directly from the `main` branch `/docs` folder. No Actions deployment action. No `gh-pages` branch.

**Why:** Pages auto-serves a `docs/` root `index.html` with zero configuration beyond the initial Settings toggle. [VERIFIED: REQUIREMENTS.md SETUP-02 note; consistent with GitHub Pages docs pattern]

**Setup sequence:**

```bash
# Step 1: Create docs/ directory with index.html committed
mkdir docs && touch docs/index.html  # (then write the real content)
git add docs/index.html .gitignore
git commit -m "feat: add static shell and gitignore"
git push

# Step 2: Enable Pages via gh CLI
gh api repos/{owner}/{repo}/pages \
  --method POST \
  -f source[branch]=main \
  -f source[path]=/docs

# Alternative: Settings → Pages → Source: "Deploy from a branch"
#              Branch: main, Folder: /docs → Save
```

**Verification:**
```bash
# Pages deployment takes ~1-5 min after first enable
curl -I https://therustyrobot.github.io/ai-tools-ref/
# Expect: HTTP/2 200
```

**Key constraint:** Pages URL is `https://therustyrobot.github.io/ai-tools-ref/` (project page, not user root page) because the repo is named `ai-tools-ref`, not `therustyrobot.github.io`. [ASSUMED — based on repo name `ai-tools-ref` observed via `gh repo view`; confirmed pattern: project pages use `{owner}.github.io/{repo}/`]

---

### Pattern 2: Tailwind CDN Config Block (exact)

**Source:** [VERIFIED: `.planning/phases/01-static-shell-github-pages-live/01-UI-SPEC.md` Design System section]

**Critical delta:** UI-SPEC uses `darkMode: "media"` — NOT `"class"` as in `stitch_example/code.html`. This is an intentional Phase 1 override per HTML-04.

```html
<!-- Tailwind CDN — must include ?plugins=forms,typography -->
<script src="https://cdn.tailwindcss.com?plugins=forms,typography"></script>

<!-- Inline config — immediately after CDN script tag -->
<script>
  tailwind.config = {
    darkMode: "media",             // HTML-04: system prefers-color-scheme ONLY — no JS toggle
    theme: {
      extend: {
        colors: {
          primary:            "#FF5F1F",  // Safety Orange
          "background-light": "#F4F1EA",  // Off-white / Bone
          "background-dark":  "#0D0D0D",  // Deep black
          "navy":             "#0A0A23",  // Near-black for light mode text/borders
        },
        fontFamily: {
          mono:    ["'JetBrains Mono'", "monospace"],
          display: ["'Inter'",          "sans-serif"],
        },
        borderRadius: {
          DEFAULT: "0px",   // Brutalist — NO rounded corners ANYWHERE
          sm:      "0px",
          md:      "0px",
          lg:      "0px",
          full:    "0px",
        },
      },
    },
  };
</script>
```

---

### Pattern 3: Complete HTML Skeleton

**Source:** [VERIFIED: `01-UI-SPEC.md` — HTML Structure Skeleton section]

```html
<!DOCTYPE html>
<html class="scroll-smooth" lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>STARS GALLERY // THERUSTYROBOT // AI-CATEGORIZED REPOS</title>

  <!-- Google Fonts: JetBrains Mono 400/700 + Inter 700 + Material Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@700&display=swap" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet" />

  <!-- Tailwind CDN -->
  <script src="https://cdn.tailwindcss.com?plugins=forms,typography"></script>
  <script>/* tailwind.config — see Pattern 2 above */</script>

  <style>
    /* Scanline — copy verbatim from stitch_example */
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
    /* Optional grid texture for decorative areas */
    .grid-bg {
      background-size: 40px 40px;
      background-image: radial-gradient(circle, currentColor 1px, transparent 1px);
    }
  </style>
</head>
<body class="bg-background-light dark:bg-background-dark text-navy dark:text-white font-mono selection:bg-primary selection:text-white overflow-x-hidden">

  <!-- 1. Scanline overlay — first child, z-50 -->
  <div class="scanline"></div>

  <!-- 2. Status strip — sticky top, z-40 -->
  <header class="sticky top-0 z-40 border-b-2 border-navy dark:border-white bg-background-light dark:bg-background-dark">
    <div class="flex flex-wrap items-center justify-between px-4 py-2 text-[10px] tracking-tighter uppercase font-bold gap-4">
      <!-- Left: SERIAL NO // REPO COUNT // STATUS -->
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-2">
          <span class="bg-navy text-white dark:bg-white dark:text-black px-1">SERIAL NO:</span>
          <span>STARS-20260421</span>
        </div>
        <div>TOTAL_REPOS: <span class="text-primary font-bold">12</span></div>
        <div class="hidden md:block">STATUS: <span class="animate-pulse text-green-600">● SYSTEM_ACTIVE</span></div>
      </div>
      <!-- Right: UPDATED timestamp -->
      <div class="hidden sm:block">UPDATED: <span>2026-04-21 06:00 UTC</span></div>
    </div>
  </header>

  <!-- 3. Body: sidebar + content -->
  <div class="flex flex-col md:flex-row min-h-screen">

    <!-- Category sidebar nav -->
    <nav class="w-full md:w-60 border-b-2 md:border-b-0 md:border-r-2 border-navy dark:border-white flex-shrink-0 md:sticky md:top-[41px] md:self-start md:max-h-[calc(100vh-41px)] md:overflow-y-auto">
      <!-- Heading band -->
      <div class="px-4 py-2 border-b-2 border-navy dark:border-white bg-navy text-white dark:bg-white dark:text-black text-[10px] font-bold uppercase tracking-widest">
        INDEX // CATEGORIES
      </div>
      <!-- Nav items with anchor links (Phase 1: 3 categories) -->
      <!-- See Pattern 6: Category Nav Items -->
    </nav>

    <!-- Repo content sections -->
    <main class="flex-1">
      <!-- Sections with id="slug" — See Pattern 5: Section + Cards -->
    </main>

  </div>

  <!-- 4. Footer -->
  <footer class="border-t-2 border-navy dark:border-white px-4 py-4">
    <div class="flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] font-bold uppercase opacity-60">
      <div>STARS_GALLERY // AUTO-GENERATED // ALL DATA FROM GITHUB API</div>
      <div class="flex gap-4">
        <span>BUILD_V_1.0</span>
        <span>SYSTEM_STATUS: OK</span>
      </div>
    </div>
  </footer>

</body>
</html>
```

---

### Pattern 4: K-Formatting Algorithm

**Source:** [VERIFIED: `01-UI-SPEC.md` — Repo Card spec, Star count format rules]

**Rules (implemented as pre-computed strings in Phase 1 hardcoded HTML):**

```
raw < 1,000            → raw integer string        e.g. 847 → "847"
1,000 ≤ raw < 1,000,000 → 1 decimal + K, strip trailing ".0"
                           e.g. 1200 → "1.2K"
                               12400 → "12.4K"
                               55000 → "55K"  (trailing .0 stripped)
raw ≥ 1,000,000        → 1 decimal + M, strip trailing ".0"
                           e.g. 1_200_000 → "1.2M"
```

**Vanilla JS implementation (useful for Phase 2+ generate.py and any inline use):**

```javascript
function formatStars(n) {
  if (n >= 1_000_000) {
    const v = (n / 1_000_000).toFixed(1).replace(/\.0$/, '');
    return v + 'M';
  }
  if (n >= 1_000) {
    const v = (n / 1_000).toFixed(1).replace(/\.0$/, '');
    return v + 'K';
  }
  return String(n);
}
```

**Phase 1 hardcoded values (pre-computed — no JS needed):**

| Repo | Raw Stars | K-formatted |
|------|-----------|-------------|
| anthropics/claude-code | 12400 | 12.4K |
| microsoft/autogen | 42000 | 42K |
| ollama/ollama | 162000 | 162K |
| caddyserver/caddy | 62000 | 62K |
| sharkdp/bat | 55000 | 55K |
| neovim/neovim | 88000 | 88K |
| BerriAI/litellm | 21000 | 21K |
| continuedev/continue | 24000 | 24K |
| netdata/netdata | 75000 | 75K |
| sindresorhus/awesome | 350000 | 350K |
| golang/go | 125000 | 125K |
| rust-lang/rust | 102000 | 102K |

---

### Pattern 5: Section Header + Repo Card Markup

**Source:** [VERIFIED: `01-UI-SPEC.md` — Section Header and Repo Card specs]

```html
<!-- Section wrapper — id is the category slug -->
<section id="ai-ml">

  <!-- Section header band — matches stitch "TECHNICAL_FILINGS" pattern -->
  <div class="px-4 py-2 border-b-2 border-navy dark:border-white flex justify-between items-center bg-zinc-200 dark:bg-zinc-800 uppercase font-bold text-[10px]">
    <span>🤖 AI &amp; ML // AGENT_FRAMEWORKS</span>
    <span class="text-primary">ENTRIES: 4</span>
  </div>

  <!-- Repo card -->
  <article class="border-b-2 border-navy dark:border-white px-4 py-4 hover:bg-zinc-900/30 dark:hover:bg-zinc-800/30 transition-colors">

    <!-- Row 1: name + star count -->
    <div class="flex items-start justify-between gap-4 mb-1">
      <a href="https://github.com/anthropics/claude-code"
         target="_blank" rel="noopener noreferrer"
         class="text-sm font-bold uppercase hover:text-primary transition-colors leading-tight">
        anthropics/claude-code
      </a>
      <span class="text-[10px] font-bold text-primary whitespace-nowrap flex-shrink-0">★ 12.4K</span>
    </div>

    <!-- Row 2: description (sentence case, no uppercase) -->
    <p class="text-sm opacity-70 mb-2 leading-relaxed">
      Claude Code is an agentic coding tool that lives in your terminal.
    </p>

    <!-- Row 3: language badge with color dot -->
    <div class="flex items-center gap-2">
      <span class="flex items-center gap-1 text-[10px] font-bold uppercase border border-current px-1 py-0.5">
        <span class="w-2 h-2 flex-shrink-0" style="background-color: #2B7489;"></span>
        TypeScript
      </span>
    </div>

  </article>

  <!-- ...more repo cards... -->

</section>
```

---

### Pattern 6: Category Sidebar Nav Items

**Source:** [VERIFIED: `01-UI-SPEC.md` — Category Sidebar Nav spec]

```html
<!-- One nav item per category (Phase 1: 4 categories to match 12 sample repos) -->
<a href="#ai-ml"
   class="flex items-center gap-2 px-4 py-2 min-h-[44px] text-[10px] font-bold uppercase tracking-tight hover:bg-primary hover:text-white transition-colors border-b border-navy/20 dark:border-white/20">
  <span class="text-primary text-[10px]">01</span>
  🤖 AI &amp; ML
  <span class="ml-auto text-[10px] opacity-60">4</span>
</a>

<a href="#self-hosting"
   class="flex items-center gap-2 px-4 py-2 min-h-[44px] text-[10px] font-bold uppercase tracking-tight hover:bg-primary hover:text-white transition-colors border-b border-navy/20 dark:border-white/20">
  <span class="text-primary text-[10px]">02</span>
  🏠 SELF-HOSTING
  <span class="ml-auto text-[10px] opacity-60">2</span>
</a>

<a href="#dev-tools"
   class="flex items-center gap-2 px-4 py-2 min-h-[44px] text-[10px] font-bold uppercase tracking-tight hover:bg-primary hover:text-white transition-colors border-b border-navy/20 dark:border-white/20">
  <span class="text-primary text-[10px]">03</span>
  🛠️ DEV TOOLS &amp; CLI
  <span class="ml-auto text-[10px] opacity-60">2</span>
</a>

<a href="#languages-runtimes"
   class="flex items-center gap-2 px-4 py-2 min-h-[44px] text-[10px] font-bold uppercase tracking-tight hover:bg-primary hover:text-white transition-colors border-b border-navy/20 dark:border-white/20">
  <span class="text-primary text-[10px]">04</span>
  💻 LANGUAGES &amp; RUNTIMES
  <span class="ml-auto text-[10px] opacity-60">2</span>
</a>

<a href="#learning-reference"
   class="flex items-center gap-2 px-4 py-2 min-h-[44px] text-[10px] font-bold uppercase tracking-tight hover:bg-primary hover:text-white transition-colors border-b border-navy/20 dark:border-white/20">
  <span class="text-primary text-[10px]">05</span>
  📚 LEARNING &amp; REFERENCE
  <span class="ml-auto text-[10px] opacity-60">1</span>
</a>

<a href="#devops-infra"
   class="flex items-center gap-2 px-4 py-2 min-h-[44px] text-[10px] font-bold uppercase tracking-tight hover:bg-primary hover:text-white transition-colors border-b border-navy/20 dark:border-white/20">
  <span class="text-primary text-[10px]">06</span>
  ⚙️ DEVOPS &amp; INFRA
  <span class="ml-auto text-[10px] opacity-60">1</span>
</a>
```

---

### Anti-Patterns to Avoid

- **Copying `darkMode: "class"` from stitch_example:** stitch uses class-based toggle. Phase 1 requires `darkMode: "media"` (system preference). Using `"class"` makes dark mode non-functional with no JS to add the `dark` class to `<html>`.
- **Using `border-radius` via Tailwind defaults:** The `borderRadius: DEFAULT: "0px"` config resets ALL Tailwind border-radius tokens to zero. Never use `rounded-*` utilities — they'll all be 0px anyway, but the intent must be explicit.
- **Using `git add -A` or `git add .`:** Phase 1 only `git add docs/index.html .gitignore`. Never `git add -A` — this is established as a permanent project constraint (DEPLOY-01).
- **Enabling Pages before `docs/index.html` is committed:** GitHub Pages activation requires at least one HTML file in the target folder. Commit the file first, then enable Pages.
- **Using Material Icons without the CDN link:** The `<span class="material-icons">` pattern requires the Google Fonts Material Icons stylesheet. It's in the skeleton — don't omit it.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS utility framework | Custom CSS property system | Tailwind CDN with inline config | stitch_example is already built in Tailwind; diverging creates maintenance burden and visual inconsistency |
| Font loading | Self-hosted font files | Google Fonts CDN `<link>` | No font file management; matches stitch_example exactly |
| Dark mode detection | `localStorage` + JS class toggle | `prefers-color-scheme` via `darkMode: "media"` | HTML-04 explicit; no JS needed; system default respected |
| Smooth scroll | `scrollIntoView()` JS | `<html class="scroll-smooth">` + CSS anchor `href="#slug"` | CSS-native; zero JS; works with `<a href="#id">` anchor links |
| Language color system | Dynamic CSS generation | Hardcoded `style="background-color: #hex"` inline on dot `<span>` | 15 static entries; no runtime computation; Phase 2 will use a Python dict |

---

## Hardcoded Sample Data (Phase 1)

**Source:** [VERIFIED: `01-UI-SPEC.md` — Sample Data section; repos drawn from `starred_repos.md`]

Grouped into 6 category sections to prove nav + layout work across multiple sections:

```
AI & ML (4 repos):
  anthropics/claude-code      TypeScript  ★ 12.4K  "Claude Code is an agentic coding tool that lives in your terminal."
  microsoft/autogen           Python      ★ 42K    "A framework for building multi-agent AI applications."
  BerriAI/litellm             Python      ★ 21K    "LLM API proxy supporting 100+ models with a unified interface."
  continuedev/continue        TypeScript  ★ 24K    "Open-source VS Code / JetBrains coding assistant."

Self-Hosting (2 repos):
  ollama/ollama               Go          ★ 162K   "Run large language models locally."
  netdata/netdata             C           ★ 75K    "Real-time infrastructure monitoring, built for production."

Dev Tools & CLI (2 repos):
  sharkdp/bat                 Rust        ★ 55K    "A cat clone with syntax highlighting and Git integration."
  neovim/neovim               C           ★ 88K    "Vim-fork focused on extensibility and usability."

Languages & Runtimes (2 repos):
  golang/go                   Go          ★ 125K   "The Go programming language."
  rust-lang/rust              Rust        ★ 102K   "Empowering everyone to build reliable and efficient software."

Learning & Reference (1 repo):
  sindresorhus/awesome        —           ★ 350K   "Awesome lists about all kinds of interesting topics."

DevOps & Infra (1 repo):
  caddyserver/caddy           Go          ★ 62K    "Fast and extensible multi-platform HTTP/1-2-3 web server with automatic HTTPS."
```

**Total: 12 repos across 6 categories** — satisfies the "at least 10 cards across at least 3 sections" success criterion.

---

## Language Color Map

**Source:** [VERIFIED: `01-UI-SPEC.md` — Language Color Map section]

These are applied as inline `style="background-color: #hex"` on a `w-2 h-2` `<span>` square (NOT a circle — `borderRadius: 0px` enforced globally):

```
Python       #3572A5   blue
TypeScript   #2B7489   dark blue
JavaScript   #F1E05A   yellow
Go           #00ADD8   cyan
Rust         #DEA584   peach
Shell        #89E051   green
C            #555555   gray
C++          #F34B7D   pink
Java         #B07219   amber
Ruby         #CC342D   red
Swift        #FFAC45   light orange
Kotlin       #A97BFF   purple
Vue          #41B883   teal
Svelte       #FF3E00   red-orange
Zig          #EC915C   burnt orange
(null/—)     currentColor opacity-30   white/gray
```

---

## `.gitignore` Changes Required

**Current state:** `.gitignore` contains only `.DS_Store` [VERIFIED: `cat .gitignore` output]

**Required addition per SETUP-03:**

```
_data/
```

**Full `.gitignore` after Phase 1:**
```
.DS_Store
_data/
```

---

## GitHub Pages Setup

**Current state:** `docs/` directory does not exist [VERIFIED: `ls docs/ 2>/dev/null` → "docs/ does not exist"]

**Repo identity:** `therustyrobot/ai-tools-ref` → Pages URL will be `https://therustyrobot.github.io/ai-tools-ref/` [VERIFIED: `gh repo view` output]

**Setup sequence (must be in this order):**

1. Create `docs/index.html` with full Stitch shell
2. Update `.gitignore` to add `_data/`
3. `git add docs/index.html .gitignore`
4. `git commit -m "feat(phase-1): static shell + gitignore"`
5. `git push`
6. Enable Pages: `gh api repos/therustyrobot/ai-tools-ref/pages --method POST -f source[branch]=main -f source[path]=/docs`
   _(or: GitHub.com → Settings → Pages → Source: main / /docs → Save)_
7. Wait 1–5 minutes, then verify: `curl -I https://therustyrobot.github.io/ai-tools-ref/`

**If Pages is already enabled pointing at root `/`:** Must re-configure to `/docs`. The Settings → Pages UI allows changing the folder dropdown without disabling Pages first.

---

## Common Pitfalls

### Pitfall 1: `darkMode: "class"` vs `darkMode: "media"` — Phase 1 Critical Delta
**What goes wrong:** Copying `darkMode: "class"` from `stitch_example/code.html` results in a page where dark mode never activates because there's no JavaScript to add `class="dark"` to `<html>`. The page renders in light mode only.
**Why it happens:** `stitch_example` uses a `TOGGLE_MODE` JS button which adds/removes the `dark` class. Phase 1 omits all JS toggles per HTML-04.
**How to avoid:** Use `darkMode: "media"` in the tailwind.config block. Verify by opening the page with OS set to dark mode — dark background should appear automatically.
**Warning signs:** Page always shows light mode regardless of OS setting.

### Pitfall 2: Pages Not Serving Because `docs/` Was Empty or Not Yet Committed
**What goes wrong:** GitHub Pages activation requires at least one file in the target path. If Pages is enabled before `docs/index.html` is committed and pushed, the Pages deployment queue processes an empty folder and may serve a 404 indefinitely.
**Why it happens:** Push order matters — Pages must be configured after the initial commit.
**How to avoid:** Commit and push `docs/index.html` first, then enable Pages.
**Warning signs:** Pages URL returns 404 more than 10 minutes after enabling.

### Pitfall 3: Raw Star Counts in HTML (Missing K-Formatting)
**What goes wrong:** Pasting `162000` as the star count instead of `162K` makes cards look like raw API data rather than a polished UI.
**Why it happens:** Easy to copy numbers from the sample data table without pre-computing the K-format.
**How to avoid:** Pre-compute all K-formatted strings from the table in Pattern 4. Verify no raw integers above 999 appear in the `★` line of any card.
**Warning signs:** Star counts are 5+ digit numbers, e.g. `★ 88000`.

### Pitfall 4: Language Dots Are Circles Instead of Squares
**What goes wrong:** Tailwind's `rounded-full` would normally create a circle, but this project has `borderRadius: DEFAULT: "0px"` — so dots will be squares even if you try to use `rounded-full`. The visual intent requires a square dot; just use `w-2 h-2` without `rounded-*`.
**Why it happens:** Developers habitually reach for `rounded-full` for language dots.
**How to avoid:** Use `<span class="w-2 h-2 flex-shrink-0" style="background-color: #hex;"></span>` — no `rounded-*` class at all.
**Warning signs:** N/A — the config enforces 0px radius; the pitfall is trying to create a circle dot and being confused why it stays square.

### Pitfall 5: Missing `rel="noopener noreferrer"` on External Links
**What goes wrong:** `target="_blank"` without `rel="noopener noreferrer"` is a security vulnerability (reverse tabnabbing). Also flagged by HTML validators.
**Why it happens:** Developers add `target="_blank"` and forget the security attribute.
**How to avoid:** Every repo link must be: `<a href="..." target="_blank" rel="noopener noreferrer">`. Template this in the repo card pattern.

### Pitfall 6: `git add -A` Accidentally Commits `_data/` If Created Before `.gitignore` Addition
**What goes wrong:** If a `_data/` directory is created manually for testing before `.gitignore` is updated, and then `git add -A` is run, `_data/*.json` files get committed.
**Why it happens:** `_data/` doesn't exist yet in Phase 1, but the gitignore entry must be added proactively.
**How to avoid:** Add `_data/` to `.gitignore` in the same commit as `docs/index.html`. Never use `git add -A` for this project.

---

## Code Examples

### Complete Language Badge (verified pattern)

```html
<!-- Source: 01-UI-SPEC.md Language Color Map + Component Spec -->
<!-- For a repo with language "Go" -->
<span class="flex items-center gap-1 text-[10px] font-bold uppercase border border-current px-1 py-0.5">
  <span class="w-2 h-2 flex-shrink-0" style="background-color: #00ADD8;"></span>
  Go
</span>

<!-- For a repo with no language (null) -->
<span class="flex items-center gap-1 text-[10px] font-bold uppercase border border-current px-1 py-0.5">
  <span class="w-2 h-2 flex-shrink-0 opacity-30"></span>
  —
</span>
```

### Status Strip Left Side

```html
<!-- Source: 01-UI-SPEC.md Status Strip spec -->
<div class="flex items-center gap-6">
  <div class="flex items-center gap-2">
    <span class="bg-navy text-white dark:bg-white dark:text-black px-1">SERIAL NO:</span>
    <span>STARS-20260421</span>
  </div>
  <div class="hidden md:block">TOTAL_REPOS: <span class="text-primary font-bold">12</span></div>
  <div class="hidden lg:block">STATUS: <span class="animate-pulse text-green-600">● SYSTEM_ACTIVE</span></div>
</div>
```

### Scanline + Grid-BG (verbatim from stitch_example)

```css
/* Source: stitch_example/code.html <style> block — copy verbatim */
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
.grid-bg {
  background-size: 40px 40px;
  background-image: radial-gradient(circle, currentColor 1px, transparent 1px);
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `darkMode: "class"` + JS toggle (stitch_example) | `darkMode: "media"` (no JS) | Phase 1 requirement HTML-04 | Dark mode works automatically via OS setting; one fewer JS interaction |
| `borderRadius: DEFAULT: "0px"` only | Add all variants (sm/md/lg/full) to "0px" | UI-SPEC revision | Ensures zero-radius even when Tailwind sub-utilities are used |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pages URL will be `https://therustyrobot.github.io/ai-tools-ref/` (project page, not root) | GitHub Pages Setup | URL may differ if repo is renamed or made a user page repo; low risk, just update the curl verification command |
| A2 | Pages API call via `gh api ... --method POST` will work without prior Pages configuration | GitHub Pages Setup | If Pages has already been enabled (unlikely given no `docs/` dir), the POST will 409; use PATCH instead or just use the Settings UI |
| A3 | Hardcoded star counts in sample data are approximately accurate for Phase 1 demo purposes | Hardcoded Sample Data | Star counts drift; for a static demo this is a display issue only, not a functional one |

---

## Open Questions

1. **GitHub Pages URL path — will `index.html` load at root `/` or require `/index.html`?**
   - What we know: GitHub Pages serves `index.html` as the directory index by default
   - What's unclear: Exact trailing-slash behavior for project pages (some CDN configurations require explicit paths)
   - Recommendation: Test `curl -I https://therustyrobot.github.io/ai-tools-ref/` and `curl -I https://therustyrobot.github.io/ai-tools-ref/index.html` — both should 200

2. **Sticky sidebar positioning — `md:sticky md:top-[41px]`**
   - What we know: The status strip is ~41px tall (10px text + 8px×2 py = 36px content + 2px border); sidebar should stick below it
   - What's unclear: Exact rendered height of the status strip on different viewports (varies with font metrics)
   - Recommendation: Use `md:top-[41px]` as the initial value; adjust by 4px increments after visual verification in browser

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| git | Commit `docs/index.html` | ✓ | 2.50.1 | — |
| gh CLI | Enable Pages via API | ✓ | 2.90.0 | Use GitHub.com Settings UI |
| curl | Verify Pages URL | ✓ | 8.7.1 | Use browser directly |
| GitHub Pages (remote) | Hosting | [must enable] | — | No fallback — this is the deliverable |
| Google Fonts CDN | Font loading | ✓ (internet required) | — | Graceful degradation to system sans/mono |
| Tailwind CDN | Styling | ✓ (internet required) | 3.x | Page renders unstyled without it (no fallback needed for Phase 1) |

**Missing dependencies with no fallback:**
- GitHub Pages must be enabled for success criteria 1 (live URL returns 200). No local equivalent — this is the deliverable.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None — static HTML; no test runner applicable |
| Config file | N/A |
| Quick run command | `curl -s -o /dev/null -w "%{http_code}" https://therustyrobot.github.io/ai-tools-ref/` |
| Full suite command | Manual visual checklist (see below) |

> **Note:** `nyquist_validation: true` is configured, but Phase 1 produces a single static HTML file with no logic to unit test. Validation is done via HTTP checks (automated) and browser visual inspection (manual). No Wave 0 test files needed.

### Phase Requirements → Test Map

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
| HTML-06 | Language badges present | grep | `grep -c 'style="background-color' docs/index.html` (expect ≥10) | ✅ Wave 0: create the file |

### Sampling Rate

- **Per task commit:** `grep "cdn.tailwindcss.com" docs/index.html && grep '"media"' docs/index.html && grep "_data/" .gitignore`
- **Per wave merge:** All grep checks above + `curl -I https://therustyrobot.github.io/ai-tools-ref/`
- **Phase gate:** Live URL returns HTTP 200 AND manual visual checklist passes before `/gsd-verify-work`

### Manual Visual Checklist (Phase Gate)

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

### Wave 0 Gaps

- [ ] `docs/index.html` — the only deliverable; does not exist yet → create in Wave 1
- [ ] `.gitignore` entry `_data/` → add in same commit as index.html

*(No test framework install needed — all validation via `curl`, `grep`, and browser)*

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Static public page; no auth |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Public read-only |
| V5 Input Validation | no | No user input in Phase 1 |
| V6 Cryptography | no | No secrets |
| External links | yes | `rel="noopener noreferrer"` on all `target="_blank"` links — prevents reverse tabnabbing |

**Phase 1 security surface:** Minimal. The only security-relevant item is proper `rel="noopener noreferrer"` on all external repo links (ASVS V1.1 — the principle of zero implicit trust on cross-origin navigations). This is documented in HTML-06 and enforced in every repo card template.

---

## Sources

### Primary (HIGH confidence)
- `stitch_example/code.html` — Visual reference; all theme tokens, CSS patterns, HTML patterns extracted directly
- `.planning/phases/01-static-shell-github-pages-live/01-UI-SPEC.md` — Authoritative design contract for Phase 1; all component specs, color values, spacing, typography, sample data
- `.planning/REQUIREMENTS.md` — Requirement text and notes for SETUP-01–04, HTML-02–06
- `.planning/research/STACK.md` — Tailwind CDN rationale, GitHub Pages setup pattern, Pages configuration approach
- `gh repo view` CLI output — Confirmed repo name `ai-tools-ref`, owner `therustyrobot`
- `cat .gitignore` — Confirmed current contents (`.DS_Store` only)
- `ls docs/` — Confirmed `docs/` directory does not yet exist

### Secondary (MEDIUM confidence)
- `.planning/research/ARCHITECTURE.md` — `docs/` directory rationale, Pages configuration pattern
- `.planning/research/PITFALLS.md` — Pitfalls 3, 8, 10 relevant to Phase 1 (no-change commits, CDN dependency, build delay)
- `.planning/research/FEATURES.md` — Feature dependencies, MVP feature set

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are CDN-loaded per stitch_example; zero decisions to make
- Architecture: HIGH — single file, single Pages configuration, fully specified in UI-SPEC
- Pitfalls: HIGH — delta between stitch_example and Phase 1 requirements is the dominant risk; well-documented
- Sample data: HIGH — drawn from verified `starred_repos.md`; K-formatted values pre-computed

**Research date:** 2026-04-21
**Valid until:** 2026-09-21 (stable — Tailwind CDN URL, Google Fonts URL, GitHub Pages `/docs` configuration are long-lived)
