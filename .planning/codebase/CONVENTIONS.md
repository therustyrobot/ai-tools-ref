# Coding Conventions

**Analysis Date:** 2026-04-21

## Repository Type

This is a **Markdown-only reference/documentation repository**. There is no application source code, no programming language runtime, and no build toolchain. All conventions are Markdown authoring conventions.

- `README.md` — repository description
- `starred_repos.md` — primary content: curated GitHub stars list (665 lines, 370 repos)

## Document Structure

**Top-level documents:**
- `README.md` — brief one-line description, no sections
- `starred_repos.md` — hierarchical reference document with table of contents, H2 categories, H3 subcategories, and Markdown tables

**Heading hierarchy in `starred_repos.md`:**
- `#` — document title (used once at top)
- `##` — top-level category (e.g., `## AI & ML`, `## DevOps & Infra`)
- `###` — subcategory (e.g., `### Claude Code & Skills`, `### Agent Frameworks & Harnesses`)

## Naming Patterns

**Files:**
- `kebab-case.md` for all Markdown files
- Descriptive lowercase names reflecting content purpose

**Section anchors:**
- GitHub-flavored Markdown auto-anchors: spaces → `-`, special chars removed, lowercase
- Example: `## AI & ML` → `#ai--ml` (ampersand dropped, double dash for space-symbol-space)

## Repo Entry Format

Every repository entry follows a **Markdown table** pattern within each `###` subcategory:

```markdown
| Name | ★ | Lang | Description |
|------|---|------|-------------|
| [Repo Name](https://github.com/owner/repo) | 55K | JS | Short description of the tool |
```

**Column conventions:**
- `Name` — linked display name using `[Text](URL)` syntax
- `★` — star count formatted as abbreviated number (e.g., `162K`, `55K`, `2.1K`, `—` for missing)
- `Lang` — primary language abbreviation (`JS`, `TS`, `Python`, `Shell`, `Go`, `—` for none)
- `Description` — single-sentence description, no period, sentence case

## Table of Contents

**Format:**
```markdown
## Table of Contents

- [Category Name](#anchor)
  - [Subcategory Name](#anchor)
```

- Top-level categories use single dash list items
- Subcategories are indented with two spaces
- Anchors follow GitHub Markdown anchor generation rules

## Separators

- `---` (horizontal rule) used after every `###` subcategory section to visually separate sections
- No separator after `##` headings — separator follows the content block of the last `###` subsection

## Metadata Line

At the top of `starred_repos.md`, a single italicized metadata line:
```markdown
*370 repos · organized April 21, 2026*
```
- Italicized with `*...*`
- Contains repo count and organization date
- Must be updated when content changes

## Language Tags in Tables

Standard abbreviations used:
- `JS` — JavaScript
- `TS` — TypeScript
- `Python` — Python
- `Shell` — Shell/Bash
- `Go` — Go
- `—` — no primary language detected or not applicable

## Formatting Rules

- No trailing whitespace convention (standard for Markdown)
- No inline HTML — pure Markdown only
- Links always use `[Text](URL)` syntax, never bare URLs in tables
- Descriptions kept to a single line — no multi-line table cells
- Star counts are abbreviated human-readable values, not exact numbers

## Additions Pattern

**To add a new repo entry:**
1. Identify the correct `##` category and `###` subcategory
2. Add a new table row following the `| [Name](URL) | ★K | Lang | Description |` pattern
3. Update the `*N repos · organized DATE*` metadata line at the top of `starred_repos.md`

**To add a new subcategory:**
1. Add `### New Subcategory` heading under the appropriate `##` section
2. Add the table header row: `| Name | ★ | Lang | Description |` and separator `|------|---|------|-------------|`
3. Add an entry to the Table of Contents under the parent category
4. Add `---` horizontal rule after the section's last entry

**To add a new top-level category:**
1. Add `## New Category` heading at appropriate position
2. Add at least one `###` subsection with table
3. Add entry in Table of Contents at top level

---

*Convention analysis: 2026-04-21*
