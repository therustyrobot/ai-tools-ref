# Project State

**Last updated:** 2026-04-21 after project initialization

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-04-21)

**Core value:** Every starred repo is surfaced in a browsable, visually distinctive page that updates itself daily — zero maintenance after setup.
**Current focus:** Ready for Phase 1 execution

## Current Status

**Milestone:** v1 — Initial Release
**Active phase:** None — ready to begin Phase 1
**Next action:** `/gsd-plan-phase 1`

## Phases

| Phase | Title | Status |
|-------|-------|--------|
| 1 | Static Shell + Pages Live | ⬜ Not started |
| 2 | Live Data Pipeline (no AI) | ⬜ Not started |
| 3 | AI Categorization | ⬜ Not started |
| 4 | Automated Daily Action | ⬜ Not started |

## Key Decisions

- **Python scripts** (pre-installed on ubuntu-latest) for all pipeline scripts
- **GitHub Models** (`https://models.github.ai/inference/chat/completions`) with `GITHUB_TOKEN` — no external API keys
- **Batch 10 repos/AI call** — stays within 150 req/day free tier
- **Seed taxonomy from `starred_repos.md`** — prevents category drift between runs
- **`_data/` in `.gitignore`** — only `docs/index.html` committed
- **`[skip ci]` on auto-commits** — prevents infinite workflow loops
- **Static HTML only** — Tailwind CDN, no build step, no framework

## Prerequisite (Blocking)

⚠️ **Repo must be moved to the GitHub account that owns the starred repos** before the GitHub Action automation in Phase 4 can be enabled. Phase 1–3 can be developed locally regardless.

## Planning Artifacts

- `.planning/PROJECT.md` — project definition
- `.planning/REQUIREMENTS.md` — 28 v1 requirements
- `.planning/ROADMAP.md` — 4-phase execution plan
- `.planning/research/` — stack, features, architecture, pitfalls research
- `.planning/codebase/` — codebase map (7 documents)
- `.planning/config.json` — workflow config (YOLO, balanced, research enabled)
