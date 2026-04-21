# Architecture

**Analysis Date:** 2026-04-21

## Pattern Overview

**Overall:** Single-file Reference Catalog

**Key Characteristics:**
- Static, content-only repository with no application code, build system, or runtime dependencies
- All reference content lives in a single Markdown document (`starred_repos.md`)
- Two-level categorical hierarchy: top-level domain sections → subsections → tabular repo entries
- No data flow, server, or API — pure documentation artifact consumed by humans and AI agents

## Layers

**Content Layer:**
- Purpose: Curated reference catalog of 370 GitHub-starred repositories
- Location: `starred_repos.md`
- Contains: Markdown tables with columns `Name`, `★` (star count), `Lang` (primary language), `Description`
- Depends on: Nothing
- Used by: Human readers, AI agents performing research or discovery

**Navigation Layer:**
- Purpose: Table of contents enabling quick access to any section
- Location: `starred_repos.md` lines 5–36 (ToC block)
- Contains: Anchor-linked list mirroring the two-level section hierarchy
- Depends on: Markdown heading anchors in the content below
- Used by: Readers navigating the document directly

**Planning Layer:**
- Purpose: Agent-generated planning artifacts (codebase maps, phase plans)
- Location: `.planning/codebase/`
- Contains: Markdown documents produced by GSD agent commands
- Depends on: Nothing (outputs only)
- Used by: `/gsd-plan-phase`, `/gsd-execute-phase` agent commands

**Agent Harness Layer:**
- Purpose: Crush AI agent session state and logs
- Location: `.crush/` (fully gitignored via `.crush/.gitignore: *`)
- Contains: `crush.db` (SQLite session state), `logs/crush.log`, `init` sentinel file
- Depends on: Crush agent runtime (external tool)
- Used by: Crush AI coding agent during active sessions

## Data Flow

**Content Consumption (human):**

1. Reader opens `starred_repos.md`
2. Uses Table of Contents anchors to jump to relevant section
3. Browses tabular entries in subsection of interest
4. Follows GitHub URL links to individual repositories

**Content Consumption (agent):**

1. Agent reads `starred_repos.md` via file tool
2. Filters by section heading or keyword matching
3. Extracts repo name, URL, language, and description
4. Uses data for research, recommendations, or further exploration

**State Management:**
- No application state; document is static Markdown
- Crush session state persisted to `.crush/crush.db` (local only, not committed)

## Key Abstractions

**Repository Entry:**
- Purpose: Represents a single starred GitHub repository
- Examples: Rows within any table in `starred_repos.md`
- Pattern: `| [Name](URL) | ★count | Lang | Description |`

**Section Hierarchy:**
- Purpose: Organizes repos into discoverable domains and sub-domains
- Examples: `## AI & ML` → `### Claude Code & Skills`, `### Agent Frameworks & Harnesses`
- Pattern: `##` top-level domain, `###` subsection (24 subsections across 14 top-level sections)

**Table of Contents:**
- Purpose: Navigational index for the entire catalog
- Examples: `starred_repos.md` lines 5–36
- Pattern: Two-level nested unordered list with GitHub-flavored Markdown anchor links

## Entry Points

**Primary Document:**
- Location: `starred_repos.md`
- Triggers: Direct file read by human or agent
- Responsibilities: Delivers full catalog — 370 repos, 14 top-level sections, 24 subsections

**Repository Root:**
- Location: `README.md`
- Triggers: GitHub web view, clone landing
- Responsibilities: One-line description — "Organizing my saved tools references"

## Error Handling

**Strategy:** Not applicable — static content repository, no runtime errors possible

**Patterns:**
- Broken external links (GitHub URLs) are silent; no link-checking infrastructure exists
- Missing descriptions in table rows use `—` as a placeholder value

## Cross-Cutting Concerns

**Logging:** Crush agent activity logged to `.crush/logs/crush.log` (local only, gitignored)
**Validation:** None — no linting, CI, or link-checking configured
**Authentication:** Not applicable

---

*Architecture analysis: 2026-04-21*
