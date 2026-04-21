# Testing Patterns

**Analysis Date:** 2026-04-21

## Repository Type

This is a **Markdown-only reference/documentation repository** with no application source code. There are no tests, no test frameworks, no CI pipelines, and no test configuration files.

- No `package.json`, `requirements.txt`, `go.mod`, or any runtime manifest
- No `jest.config.*`, `vitest.config.*`, `pytest.ini`, or equivalent
- No `*.test.*`, `*.spec.*`, or `test/` directory
- No `.github/workflows/` CI configuration

## Testing Approach

**Applicable testing:** Not applicable — this repository contains only Markdown documents.

**What "correctness" means for this repo:**
- Markdown renders correctly in GitHub
- Table of Contents anchors resolve to existing headings
- All linked URLs are valid GitHub repository URLs
- Star counts and language tags are accurate at time of organization

## Manual Validation Checklist

Since there is no automated test suite, content correctness is validated manually:

**Structure checks:**
- Every `###` subcategory has a corresponding Table of Contents entry
- Every Table of Contents entry links to an existing `###` heading
- Every section ends with a `---` separator
- Table header and separator rows are present in every subcategory table

**Data checks:**
- `*N repos · organized DATE*` metadata count matches actual row count in all tables
- All `[Name](URL)` links use `https://github.com/` URLs
- Star counts use abbreviated format (`K` suffix or `—`)
- Language tags use approved abbreviations (`JS`, `TS`, `Python`, `Shell`, `Go`, `—`)

## Automated Validation Opportunities

If automation is desired in future, the following checks could be scripted:

**Link validation:**
```bash
# Extract all URLs from starred_repos.md
grep -oE 'https://github\.com/[^)]+' starred_repos.md | sort -u
# Validate with curl or gh CLI
```

**Row count check:**
```bash
# Count table data rows (exclude header and separator rows)
grep -c "^| \[" starred_repos.md
# Compare against metadata line count
grep "repos · organized" starred_repos.md
```

**Anchor validation:**
```bash
# Extract TOC links
grep -oE '\(#[^)]+\)' starred_repos.md | tr -d '()'
# Extract heading anchors (manual transformation required)
```

## CI/CD

**Current:** None

**Recommended future addition:**
- GitHub Actions workflow to run `markdownlint` on PRs
- Link checker action (e.g., `lychee-action`) to validate GitHub URLs
- Row count assertion to keep metadata line accurate

## Coverage

**Requirements:** None enforced

**Untested risks:**
- Broken Table of Contents links (anchor drift when headings are renamed)
- Dead GitHub repository links (repos may be deleted or renamed)
- Inaccurate star counts (become stale over time)
- Off-by-one repo count in metadata line after additions/removals

---

*Testing analysis: 2026-04-21*
