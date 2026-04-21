# Codebase Structure

**Analysis Date:** 2026-04-21

## Directory Layout

```
ai-tools-ref/
├── README.md               # One-line repository description
├── starred_repos.md        # Full 370-repo curated reference catalog (665 lines)
├── .planning/
│   └── codebase/           # GSD agent codebase map documents
└── .crush/                 # Crush AI agent runtime artifacts (gitignored)
    ├── crush.db            # SQLite session state (~786 KB)
    ├── init                # Sentinel file for agent initialization
    └── logs/
        └── crush.log       # Agent session activity log
```

## Directory Purposes

**Root (`/`):**
- Purpose: Repository landing; contains all committed content
- Contains: `README.md`, `starred_repos.md`
- Key files: `starred_repos.md` — the entire value of the repository

**`.planning/codebase/`:**
- Purpose: Agent-generated codebase analysis documents
- Contains: Markdown files written by GSD mapping commands (`/gsd-map-codebase`)
- Key files: `ARCHITECTURE.md`, `STRUCTURE.md`, and other maps as created

**`.crush/`:**
- Purpose: Local-only Crush AI agent harness state
- Contains: SQLite database, log file, init sentinel
- Generated: Yes (by Crush agent at runtime)
- Committed: No (`.crush/.gitignore` contains `*`, excluding all contents)

## Key File Locations

**Entry Points:**
- `README.md`: Repository description — "Organizing my saved tools references"
- `starred_repos.md`: Primary content document; Table of Contents at lines 5–36

**Content Sections in `starred_repos.md`:**
- `## AI & ML` — 9 subsections covering Claude skills, agent frameworks, MCP servers, LLM UIs, RAG, AI productivity, AI infra, coding agents, generalist agents
- `## Self-Hosting & Homelab` — 8 subsections: dashboards, auth, monitoring, media/arr, deployment, notes, networking, Proxmox
- `## Dev Tools & CLI` — 6 subsections: terminal/shell, docs/sites, automation, arr/media, ESP32, other dev tools
- `## DevOps & Infra` — Single-level (no subsections)
- `## Security` — Single-level
- `## Web & Frontend` — Single-level
- `## Data & Analytics` — Single-level
- `## Productivity & Notes` — Single-level
- `## Media & Entertainment` — Single-level
- `## Networking` — Single-level
- `## Mobile & Desktop` — Single-level
- `## Awesome Lists` — Single-level
- `## ESP32 & Hardware` — Single-level
- `## Other` — Catch-all for unclassified repos

**Planning / Meta:**
- `.planning/codebase/ARCHITECTURE.md`: Architecture analysis
- `.planning/codebase/STRUCTURE.md`: This file

## Naming Conventions

**Files:**
- Lowercase with underscores for content files: `starred_repos.md`
- Uppercase for planning/meta documents: `README.md`, `ARCHITECTURE.md`, `STRUCTURE.md`

**Sections (in `starred_repos.md`):**
- `##` heading: Top-level domain (Title Case with `&` for compound domains)
- `###` heading: Subsection within a domain (Title Case)
- Table columns: `Name`, `★`, `Lang`, `Description` — consistent across all tables

**Table Entry Format:**
```markdown
| [Display Name](https://github.com/owner/repo) | star_count | Language | Short description |
```
- Missing descriptions use `—` (em dash)
- Star counts expressed as integers with `K` suffix for thousands (e.g., `162K`)

## Where to Add New Code

**New Repository Entry:**
- Locate the appropriate `##` section and `###` subsection in `starred_repos.md`
- Add a new table row following the `| [Name](URL) | ★ | Lang | Description |` format
- Update the count in the document header: `*N repos · organized DATE*`

**New Section:**
- Add `##` heading at appropriate position in `starred_repos.md`
- Add corresponding entry in the Table of Contents (lines 5–36) with an anchor link

**New Subsection within Existing Section:**
- Add `###` heading under the parent `##` section
- Add corresponding nested entry in the Table of Contents
- Add a `| Name | ★ | Lang | Description |` header row and `|---|---|---|---|` separator row before entries

**New Planning Document:**
- Write to `.planning/codebase/` using uppercase filename (e.g., `STACK.md`, `CONCERNS.md`)

## Special Directories

**`.crush/`:**
- Purpose: Runtime state for Crush AI coding agent sessions
- Generated: Yes — created and managed by Crush agent automatically
- Committed: No — entirely gitignored via `.crush/.gitignore: *`
- Notable: `crush.db` is a SQLite file (~786 KB) holding session/conversation history

**`.planning/`:**
- Purpose: Structured planning artifacts for GSD agent workflow (`/gsd-map-codebase`, `/gsd-plan-phase`, `/gsd-execute-phase`)
- Generated: Yes — written by GSD agent commands
- Committed: Yes (no gitignore exclusion detected)

---

*Structure analysis: 2026-04-21*
