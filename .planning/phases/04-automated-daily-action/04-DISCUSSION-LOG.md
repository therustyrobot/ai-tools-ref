# Phase 4: Automated Daily Action - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-24
**Phase:** 04-automated-daily-action
**Areas discussed:** requests dependency, failure alerting, Python version pin

---

## requests dependency

| Option | Description | Selected |
|--------|-------------|----------|
| Trust pre-installed | ubuntu-latest ships requests; no extra step, faster workflow | |
| Add pip install requests | Explicit safety net; ~5s overhead but never breaks on runner updates | ✓ |

**Follow-up — what to install:**

| Option | Description | Selected |
|--------|-------------|----------|
| requests only | Only missing dep; keep workflow lean | ✓ |
| requests + PyGithub | Only if planning to use PyGithub (currently not used) | |
| Full requirements.txt | Pin all deps explicitly with pip install -r requirements.txt | |

**Follow-up — pip command style:**

| Option | Description | Selected |
|--------|-------------|----------|
| pip install requests | Direct, minimal | ✓ |
| pip install --upgrade requests | Ensures latest version | |
| pip install requests==2.31.0 | Pin exact version for reproducibility | |

**Follow-up — step structure:**

| Option | Description | Selected |
|--------|-------------|----------|
| Separate step named 'Install dependencies' | Clear intent, visible in Action logs | ✓ |
| Inline with the first python script run | e.g. `pip install requests && python scripts/fetch_stars.py` | |
| In a requirements.txt file | pip install -r requirements.txt | |

**User's choice:** Separate "Install dependencies" step, `pip install requests` only, plain (no pin, no --upgrade).
**Notes:** Explicit safety net preferred over trusting runner image state; lean (requests only, not a requirements.txt).

---

## Failure alerting

| Option | Description | Selected |
|--------|-------------|----------|
| GitHub default email | GitHub already sends failure emails to repo owner; zero extra config | ✓ |
| No notifications | Silent fail, check manually or trust gallery to go stale | |
| Create a GitHub Issue on failure | Opens a visible issue in the repo when the Action fails | |

**Follow-up — step failure behavior:**

| Option | Description | Selected |
|--------|-------------|----------|
| Let the whole job fail | Clear failure signal, GitHub email fires, easy to diagnose | ✓ |
| continue-on-error per step | Log failures but let workflow finish; gallery may be partially updated | |
| Conditional failure | Fail hard if fetch/categorize fails, but allow generate with stale data | |

**Follow-up — retry:**

| Option | Description | Selected |
|--------|-------------|----------|
| No retry | Tomorrow's run will retry; no retry masks real issues | ✓ |
| Retry the whole job once | Actions supports retry via third-party action or manual re-run | |
| Retry individual steps | Shell retry loops around each python script call | |

**User's choice:** Default GitHub email, whole-job fail, no retry.
**Notes:** Simplest failure model — fail loud, fix tomorrow. Matches the low-stakes daily cron nature of the workflow.

---

## Python version pin

| Option | Description | Selected |
|--------|-------------|----------|
| Rely on runner default Python | ubuntu-latest ships Python 3.12; no setup-python step, faster startup | ✓ |
| Pin with setup-python@v4 python-version: '3.12' | Explicit version, reproducible across runner image updates | |
| Pin with setup-python@v4 python-version: '3.x' | Latest 3.x, explicit but flexible | |

**User's choice:** Rely on runner default (no setup-python step).
**Notes:** Lean workflow; no extra action to maintain. Acceptable risk — runner image updates are infrequent and announced.

---

## Agent's Discretion

- `git config` identity — standard `github-actions[bot]` user/email format
- Step naming and ordering — follow REQUIREMENTS.md ACTION-03 exactly
- No-change guard placement — after `git add docs/index.html`, before push
- GITHUB_ACTOR log — early in the job per ACTION-04
- Workflow name — `Update Gallery`

## Deferred Ideas

- Custom failure notification (Issues, Slack) — GitHub email sufficient for now
- Pinned Python version — revisit if runner updates cause breakage
- `requirements.txt` with pinned `requests==x.y.z` — V2 hardening if needed
- Retry logic — tomorrow's run handles transient failures
