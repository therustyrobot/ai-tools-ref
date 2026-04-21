# AI Stars Gallery

## What This Is

A static web page hosted on GitHub Pages that displays the owner's GitHub starred repos organized into AI-generated categories and subcategories. A daily GitHub Action fetches all stars via the GitHub API, uses GitHub Models (free) to categorize every repo, regenerates the HTML, and commits it — so the page stays current automatically without any manual work.

## Core Value

Every starred repo is surfaced in a browsable, visually distinctive page that updates itself daily — zero maintenance after setup.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

- [ ] Static web page hosted on GitHub Pages displaying all starred repos
- [ ] AI auto-categorization of repos into categories + subcategories using GitHub Models
- [ ] Daily GitHub Action: fetch stars → categorize → regenerate HTML → commit
- [ ] Re-categorize all existing repos on first run (fresh AI-generated taxonomy)
- [ ] Brutalist Stitch aesthetic (JetBrains Mono, Safety Orange #FF5F1F, sharp corners, dark mode)
- [ ] Category navigation embedded in the page layout (not a top header menu)
- [ ] Repo entries show: name (link), star count, language, description

### Out of Scope

- Search/filter bar — category nav is sufficient for now
- Multiple GitHub accounts — single account only
- Comments or social features — read-only reference page
- Backend / database — fully static, no server

## Context

- Existing `starred_repos.md` in this repo has 370 repos already organized into categories — serves as a reference for the AI categorization taxonomy and quality bar.
- `stitch_example/code.html` contains the Stitch theme HTML to match: Tailwind CDN, JetBrains Mono + Inter fonts, Safety Orange primary, off-white light / deep black dark bg, no border radius (brutalist), scanline animation effect.
- AI categorization will use GitHub Models API (free with a GitHub account), callable from GitHub Actions via `GITHUB_TOKEN` — no external API keys needed.
- **Prerequisite:** Repo must be moved to the GitHub account that owns the starred repos before the GitHub Action automation can be enabled. The action fetches stars for the authenticated user.

## Constraints

- **Hosting**: GitHub Pages — static HTML only, no server-side code
- **AI API**: GitHub Models — free tier, accessible via `GITHUB_TOKEN` in Actions
- **Repo account**: Must live on the same GitHub account as the starred repos for the Action to fetch stars seamlessly
- **Style**: Must match Stitch brutalist aesthetic from `stitch_example/code.html`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GitHub Models for AI categorization | Free with GitHub account, no external API keys, works natively in Actions | — Pending |
| Daily scheduled Action | Set-it-and-forget-it, no manual trigger needed | — Pending |
| Full re-categorization on every run | Ensures consistent taxonomy; simpler than diff logic | — Pending |
| Static HTML (no framework) | GitHub Pages compatible, zero build complexity | — Pending |

## Evolution

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions

---
*Last updated: 2026-04-21 after initial project definition*
