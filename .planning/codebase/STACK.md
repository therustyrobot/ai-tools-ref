# Technology Stack

**Analysis Date:** 2026-04-21

## Overview

This is a **pure documentation repository** — no application source code, no build system, and no
runtime. All content is authored in Markdown and managed via Git. The only tooling present is the
`crush` AI coding agent used for authoring sessions.

---

## Languages

**Primary:**
- Markdown — all content files (`README.md`, `starred_repos.md`)

**Secondary:**
- None

---

## Runtime

**Environment:**
- Not applicable — no executable code in this repository

**Package Manager:**
- Not applicable
- Lockfile: Not present

---

## Frameworks

**Core:**
- None — repository is static Markdown content only

**Testing:**
- None

**Build/Dev:**
- None — no build pipeline or compilation step

---

## Key Dependencies

**Critical:**
- None — no package dependencies

**Infrastructure:**
- `crush` (Charmbracelet) — AI coding agent used to author and manage repository content
  - Binary: `github.com/charmbracelet/crush` (Go-compiled CLI)
  - Session store: `.crush/crush.db` (SQLite 3.x)
  - Logs: `.crush/logs/crush.log` (JSON structured log)
  - Git-ignored: entire `.crush/` directory (`.crush/.gitignore` contains `*`)

---

## Configuration

**Environment:**
- No environment variables required
- No `.env` files present

**Build:**
- No build config files (no `webpack.config.*`, `tsconfig.json`, `vite.config.*`, etc.)

---

## Platform Requirements

**Development:**
- macOS (Darwin) — confirmed by log timestamps and paths under `/Users/`
- `crush` CLI installed for AI-assisted authoring sessions
- Git for version control

**Production:**
- No deployment target — repository serves as a static reference document
- Content is readable directly on GitHub or any Markdown renderer

---

## Content Structure

**Files:**
- `README.md` — Repository title and one-line description
- `starred_repos.md` — 370 curated GitHub starred repositories organized into categories
  (55,331 bytes; organized April 21, 2026)
- `.crush/` — AI agent session state (gitignored, local-only)
- `.planning/` — GSD planning documents (this directory)

---

*Stack analysis: 2026-04-21*
