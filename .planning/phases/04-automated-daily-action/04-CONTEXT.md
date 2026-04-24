# Phase 4: Automated Daily Action - Context

**Gathered:** 2026-04-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Create `.github/workflows/update-gallery.yml` — a GitHub Actions workflow that runs the full pipeline (fetch → install deps → categorize → generate → commit-if-changed) on a daily schedule and on manual `workflow_dispatch`. The workflow cannot trigger itself recursively.

This phase does NOT add new scripts, change categorization logic, or modify the HTML output. It only wires the existing scripts into an automated Action.

</domain>

<decisions>
## Implementation Decisions

### Dependency Installation

- **D-01:** Add a **separate "Install dependencies" step** that runs `pip install requests` before the Python scripts execute. This is a dedicated step (not inlined with a script call) so it appears clearly in the Action log.
- **D-02:** Install `requests` only — all other imports (`os`, `json`, `urllib`, `html`, `datetime`, etc.) are Python stdlib. No `requirements.txt` file; no other PyPI packages needed.
- **D-03:** Use plain `pip install requests` — no version pin, no `--upgrade`. Minimal and explicit.

### Failure Handling

- **D-04:** **Let the whole job fail** if any step fails. No `continue-on-error` on individual steps. A clear failure is preferable to a partially-updated gallery.
- **D-05:** **No automatic retry** — if the daily run fails (transient network error, API limit), the next day's scheduled run will retry. Retries inside the workflow would mask real issues.
- **D-06:** **GitHub default email notification** is sufficient for failure alerting. No custom Issue-creation or Slack notification. The repo owner receives GitHub's standard failure email automatically.

### Python Version

- **D-07:** **Rely on the runner's pre-installed Python** — no `setup-python@v4` step. `ubuntu-latest` ships Python 3.12, which the scripts already target. Skipping setup-python reduces startup time and avoids an extra action version to maintain.

### the Agent's Discretion

- **`git config` identity:** Use the standard `github-actions[bot]` pattern: `user.name = github-actions[bot]`, `user.email = 41898282+github-actions[bot]@users.noreply.github.com`.
- **Step naming and ordering:** Follow REQUIREMENTS.md ACTION-03 exactly — checkout → install deps → fetch → categorize → generate → git commit-if-changed.
- **No-change guard placement:** Run `git diff --staged --quiet` after `git add docs/index.html` as per DEPLOY-02; skip push entirely if exit 0.
- **GITHUB_ACTOR log:** Emit `echo "Running as: $GITHUB_ACTOR"` early in the job (or in the first step's `run:` block) to satisfy ACTION-04.
- **Workflow name:** `Update Gallery` — clear and descriptive in the Actions UI.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements (primary source of truth for this phase)
- `.planning/REQUIREMENTS.md` §ACTION — ACTION-01 through ACTION-04: schedule, permissions, step order, GITHUB_ACTOR log
- `.planning/REQUIREMENTS.md` §DEPLOY — DEPLOY-01 through DEPLOY-03: native git commands, no-change guard, `[skip ci]` commit message

### Existing Scripts (the workflow invokes these)
- `scripts/fetch_stars.py` — reads `GITHUB_TOKEN` from env, writes `_data/repos.json`
- `scripts/categorize.py` — reads `GITHUB_TOKEN` from env, reads `_data/repos.json`, writes `_data/categories.json`
- `scripts/generate.py` — reads `_data/repos.json` + `_data/categories.json`, writes `docs/index.html`

### Reference Materials
- `.planning/PROJECT.md` — core constraints (static HTML, `_data/` gitignored, daily automation goal)
- `.planning/phases/03-ai-categorization/03-CONTEXT.md` — prior phase decisions (Bearer auth, batch 10, slug derivation) that inform how scripts behave in the Action

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/fetch_stars.py`, `scripts/categorize.py`, `scripts/generate.py` — all three scripts are complete and tested (45 tests passing). The workflow only needs to invoke them in sequence.
- No existing `.github/workflows/` directory — this is a greenfield workflow file.

### Established Patterns
- Scripts read `GITHUB_TOKEN` from `os.environ["GITHUB_TOKEN"]` — the workflow must pass it via `env:` on each python step (or job-level env).
- `_data/` is in `.gitignore` — intermediate files never committed.
- `docs/index.html` is the only output file to commit.

### Integration Points
- The workflow is the top-level orchestrator: `actions/checkout@v4` → pip → python scripts → git.
- `${{ secrets.GITHUB_TOKEN }}` is the built-in Actions token — no manual secret configuration needed.

</code_context>

<specifics>
## Specific Ideas

- Separate "Install dependencies" step (not inlined) so it's visible as a distinct line in the Action run log.
- No `setup-python` step — lean, fast, no extra action to maintain.
- `workflow_dispatch` trigger alongside `schedule` allows manual first-run testing and ad-hoc regeneration.
- Commit message: `"chore: regenerate stars gallery [skip ci]"` — per DEPLOY-03, prevents recursive trigger.

</specifics>

<deferred>
## Deferred Ideas

- Retry on transient failure — no retry in v1; tomorrow's run handles it (see V2 ideas in REQUIREMENTS.md).
- Custom failure notification (GitHub Issues, Slack) — GitHub email is sufficient for now.
- Pinned Python version — revisit if runner image updates ever cause breakage.
- `pip install -r requirements.txt` with a pinned `requests==x.y.z` — V2 hardening if needed.

</deferred>

---

*Phase: 04-automated-daily-action*
*Context gathered: 2026-04-24*
