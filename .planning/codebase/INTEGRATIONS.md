# External Integrations

**Analysis Date:** 2026-04-21

## Overview

This is a **static documentation repository** with no application runtime. There are no API calls,
no database connections, and no auth flows in the repository's own code. The integrations listed
below are entirely in the local AI-agent tooling (crush) used to author content.

---

## APIs & External Services

**AI Coding Agent (crush):**
- Service: Charmbracelet `crush` — terminal UI AI agent
  - Source: `github.com/charmbracelet/crush` (Go binary)
  - Auth: Configured at system level (not in this repo)
  - Logs: `.crush/logs/crush.log`

**MCP (Model Context Protocol) Servers:**
- `packmind` — attempted connection at `http://localhost:8081/mcp`
  - Status: **Not running** — connection refused at analysis time (error in `.crush/logs/crush.log`)
  - Type: Local HTTP MCP server (port 8081)
  - Configured in: crush's system-level MCP config (not in this repo)

---

## Data Storage

**Databases:**
- `crush` session database
  - Type: SQLite 3.x
  - File: `.crush/crush.db` (786 KB, gitignored)
  - Tables: `sessions`, `messages`, `files`, `read_files`, `goose_db_version`
  - Purpose: Stores AI agent conversation sessions, file snapshots, and cost/token metadata
  - Client: Built into `crush` binary — not accessed by this repo's code

**File Storage:**
- Local filesystem only — all content is flat Markdown files tracked in Git

**Caching:**
- None

---

## Authentication & Identity

**Auth Provider:**
- None — no user authentication in this repository
- crush AI provider credentials are stored at the OS user config level
  (`~/.config/crush/` — outside this repo)

---

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- crush structured JSON logs: `.crush/logs/crush.log` (gitignored)
  - Format: JSON with `time`, `level`, `source`, `msg` fields
  - Scope: AI agent session activity only

---

## CI/CD & Deployment

**Hosting:**
- Not applicable — no deployed application
- Repository hosted on GitHub (implied by starred_repos content referencing GitHub URLs)

**CI Pipeline:**
- None — no `.github/workflows/` detected

---

## Environment Configuration

**Required env vars:**
- None required by this repository

**Secrets location:**
- crush AI provider credentials stored at system level (`~/.config/crush/` — outside repo)
- `.crush/` directory is entirely gitignored (`*`)

---

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

---

## Skills Discovery (crush)

The `crush` agent attempts to load skills from the following paths at startup (all missing in this
repo — see `.crush/logs/crush.log`):

- `~/.config/crush/skills`
- `~/.config/agents/skills`
- `.agents/skills` (repo-local)
- `.crush/skills` (repo-local)
- `.claude/skills` (repo-local)
- `.cursor/skills` (repo-local)

None are present. To add agent skills, create any of the above directories with skill definitions.

---

*Integration audit: 2026-04-21*
