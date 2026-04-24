# Phase 4 Research — Automated Daily Action

*Researched: 2026-04-24*
*Scope: GitHub Actions YAML patterns for scheduled Python pipeline with git commit-or-skip*

---

## 1. Triggers — `schedule` + `workflow_dispatch`

```yaml
on:
  schedule:
    - cron: '0 6 * * *'   # Daily at 06:00 UTC
  workflow_dispatch:       # Manual trigger from Actions UI / API
```

- `schedule` uses UTC cron; GitHub may delay runs by up to 15 minutes under heavy load — acceptable for a daily gallery.
- `workflow_dispatch` with no `inputs:` block is perfectly valid; gives a single "Run workflow" button in the Actions UI.

## 2. Permissions Block

```yaml
permissions:
  contents: write   # Required: commit docs/index.html and push
  models: read      # Required: call GitHub Models API from categorize.py
```

- Must be declared at **workflow level** (or job level) — if omitted, `GITHUB_TOKEN` defaults to `contents: read` and the push will fail with 403.
- `models: read` is the GitHub Models permission. Without it, the Bearer auth call to `models.github.ai` returns 401 silently — script exits non-zero and job fails with a confusing error.

## 3. Job Runner — `ubuntu-latest`

```yaml
jobs:
  update-gallery:
    runs-on: ubuntu-latest
```

- `ubuntu-latest` = Ubuntu 22.04 (currently). Ships Python 3.10 and Python 3.12 (selectable via `python3`). Default `python3` binary = 3.10 on 22.04; `python3.12` is available.
- **Key decision (D-07):** No `setup-python` step — but scripts must be invoked with `python3` (not `python`) to get the pre-installed Python. Using bare `python` may resolve to nothing or Python 2 on some runner versions.
- `requests` is **NOT** reliably pre-installed on ubuntu-latest runner images (it's in venv contexts but not always system-wide). REQUIREMENTS.md note says "verify on first run" — CONTEXT.md D-01 resolves this by adding an explicit `pip install requests` step.

## 4. GITHUB_TOKEN Environment Variable

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- Declaring at **job level** (not per-step) means all steps inherit it automatically — cleaner than repeating on each `python` step.
- `${{ secrets.GITHUB_TOKEN }}` is the automatic built-in Actions token — no manual secret configuration needed.
- The scripts read it via `os.environ["GITHUB_TOKEN"]` — this pattern is confirmed in `scripts/fetch_stars.py` and `scripts/categorize.py`.

## 5. Step Order (REQUIREMENTS.md ACTION-03 canonical)

```
1. actions/checkout@v4             (checkout repo)
2. pip install requests             (install deps — D-01)
3. python scripts/fetch_stars.py   (fetch → _data/repos.json)
4. python scripts/categorize.py    (categorize → _data/categories.json)
5. python scripts/generate.py      (generate → docs/index.html)
6. git commit-if-changed            (commit+push or skip)
```

## 6. GITHUB_ACTOR Log (ACTION-04)

```yaml
- name: Verify account
  run: echo "Running as $GITHUB_ACTOR"
```

- `GITHUB_ACTOR` is an automatic environment variable provided by Actions — no declaration needed.
- Emit early (first step or combined with checkout step) so account mismatch is immediately visible in the step log.

## 7. Git Identity + Native Commit (DEPLOY-01)

```yaml
- name: Commit changes
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git add docs/index.html
    git diff --staged --quiet && echo "No changes" && exit 0
    git commit -m "chore: regenerate stars gallery [skip ci]"
    git push
```

- `41898282` is the numeric user ID for `github-actions[bot]` — standard for Actions bot commits.
- `git add docs/index.html` only — never `git add -A` (would stage `_data/` which is gitignored but is good hygiene anyway).
- `exit 0` after the no-change guard is critical — without it the step exits with code 1 from `git diff`, marking the job failed.

## 8. No-Change Guard Pattern (DEPLOY-02)

```bash
git add docs/index.html
git diff --staged --quiet && echo "No changes to commit" && exit 0
git commit -m "chore: regenerate stars gallery [skip ci]"
git push
```

- `git diff --staged --quiet` exits 0 if staged area is empty (no diff), exits 1 if there are staged changes.
- Using `&&` short-circuits correctly: if exit 0 (no changes), echoes message and exits the step cleanly.
- If stars changed → `git diff` exits 1 → `&&` chain does NOT execute → falls through to commit+push.

## 9. `[skip ci]` Convention (DEPLOY-03)

- GitHub Actions skips triggering workflows when `[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`, or `[actions skip]` appears anywhere in the commit message.
- `"chore: regenerate stars gallery [skip ci]"` satisfies both DEPLOY-03 and conventional commit format.

## 10. Structural YAML Template

```yaml
name: Update Gallery

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

permissions:
  contents: write
  models: read

jobs:
  update-gallery:
    runs-on: ubuntu-latest
    env:
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    steps:
      - name: Verify account
        run: echo "Running as $GITHUB_ACTOR"

      - name: Checkout
        uses: actions/checkout@v4

      - name: Install dependencies
        run: pip install requests

      - name: Fetch starred repos
        run: python scripts/fetch_stars.py

      - name: Categorize repos
        run: python scripts/categorize.py

      - name: Generate HTML
        run: python scripts/generate.py

      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add docs/index.html
          git diff --staged --quiet && echo "No changes to commit" && exit 0
          git commit -m "chore: regenerate stars gallery [skip ci]"
          git push
```

## 11. Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| `python` vs `python3` binary | Use `python3` or confirm `ubuntu-latest` `python` symlink — scripts use `#!/usr/bin/env python3` shebang; invoked as `python scripts/...` in workflow — add explicit check or use `python3` |
| `requests` not on system Python | D-01: explicit `pip install requests` step before any script runs |
| `models: read` missing → silent 401 | Declared in `permissions` block |
| Auto-commit triggers new run | `[skip ci]` in commit message |
| `_data/` files committed | `git add docs/index.html` only; `_data/` is gitignored |
| Wrong account stars fetched | ACTION-04: `GITHUB_ACTOR` log line exposes mismatch immediately |

## 12. Open Question: `python` vs `python3`

On `ubuntu-latest` (Ubuntu 22.04), `python` is typically a symlink to `python3`. However, to be safe, workflows should invoke scripts with `python3` explicitly. The scripts have `#!/usr/bin/env python3` shebangs but when invoked as `python scripts/...` the shebang is ignored. **Recommendation: use `python3 scripts/fetch_stars.py` etc. in the workflow steps.**

