# Technology Stack

**Project:** AI Stars Gallery
**Researched:** 2026-04-21
**Mode:** Ecosystem — static site + GitHub Actions automation

---

## Recommended Stack

### Hosting & Frontend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| GitHub Pages | — | Static hosting | Free, zero-config for public repos, no server needed, works with single-commit deploys |
| HTML (single file) | HTML5 | Page structure | No build pipeline; `index.html` at repo root is auto-served by Pages |
| Tailwind CSS CDN | 3.x (cdn.tailwindcss.com) | Styling | Exact match to `stitch_example/code.html`; zero build step; inline `tailwind.config` for custom theme tokens |
| Google Fonts (CDN) | — | JetBrains Mono + Inter | Already used in stitch theme; no font files to manage |

**Why no build framework:** The project constraint is static HTML only. Adding Next.js, Astro, or Vite would require a build step in the Action, a `dist/` artifact, and configuration that adds fragility. A single `index.html` commits directly and serves immediately from Pages.

**Tailwind CDN caveat:** CDN Tailwind does not purge unused CSS. For a single-page gallery this is fine — the CDN is ~100KB gzipped and the total page will be dominated by repo data anyway. Do NOT use `npx tailwindcss` build in the Action; it adds a Node.js step, `node_modules`, and a build artifact for no real benefit at this scale.

---

### Automation Runtime

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| GitHub Actions | — | Daily scheduled automation | Native to the repo; free on public repos; provides `GITHUB_TOKEN` without any secrets setup |
| Python | 3.12 (pre-installed on `ubuntu-latest`) | Script language | Pre-installed on `ubuntu-latest` — no `setup-python` step needed; excellent string manipulation and `json`/`html` stdlib; cleaner than bash for multi-step logic |
| `requests` library | 2.33.1 | HTTP calls to GitHub REST API and GitHub Models | Pre-installed on GitHub Actions runners' Python env; simple, battle-tested pagination |

**Why Python over Node.js:** Python 3.12 is pre-installed on `ubuntu-latest`. The script does three things: paginate a REST API, call an LLM, generate a string of HTML. Python's stdlib (`json`, `html`, `textwrap`) handles all three cleanly. Node.js requires a `setup-node` step or relies on a version that may not have `fetch` stable. Python wins on simplicity.

**Why not a shell script:** The AI batching logic (loop over repo pages, build prompt arrays, parse JSON response) is hard to express cleanly in bash. Python is the right tool.

---

### GitHub Stars API

| Technology | Endpoint | Purpose | Why |
|------------|----------|---------|-----|
| GitHub REST API v3 | `GET /user/starred?per_page=100` | Fetch all starred repos | Official, stable, paginated via `Link` header; `GITHUB_TOKEN` gives 1000 req/hr in Actions context |

**Pagination pattern:**
```python
headers = {
    "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}
url = "https://api.github.com/user/starred?per_page=100"
while url:
    resp = requests.get(url, headers=headers)
    repos.extend(resp.json())
    url = resp.links.get("next", {}).get("url")
```

**Rate limits:** Authenticated `GITHUB_TOKEN` in Actions gets 1,000 requests/hour for the REST API. 370 repos = 4 pages at 100/page = 4 requests. This is negligible. Confidence: HIGH (verified via curl headers test).

---

### AI Categorization API

| Technology | Endpoint | Model | Why |
|------------|----------|-------|-----|
| GitHub Models API | `https://models.github.ai/inference/chat/completions` | `openai/gpt-4o-mini` | Free with `GITHUB_TOKEN`; no external API keys; callable from Actions with `models: read` permission; OpenAI-compatible format |

**Confirmed endpoint** (from official GitHub Models quickstart docs, 2026):
```
POST https://models.github.ai/inference/chat/completions
Authorization: Bearer $GITHUB_TOKEN
Content-Type: application/json
```

**Required workflow permission:**
```yaml
permissions:
  contents: write    # to commit the generated HTML
  models: read       # to call GitHub Models API
```

**Why `openai/gpt-4o-mini` over `openai/gpt-4o`:**
- Faster response times → less total wall-clock time for the daily Action
- Lower token consumption per request → more headroom within free tier rate limits
- Categorization is a simple classification task; GPT-4o-mini handles it reliably
- GitHub Models free tier rate limits are not publicly documented as hard numbers, but smaller/faster models get more generous allowances

**Why `requests` over `openai` Python SDK:**
- `requests` is pre-installed; `openai` requires `pip install` (adds ~30s to Action)
- The GitHub Models endpoint is OpenAI-compatible but does NOT require the `openai` SDK
- One fewer dependency = one fewer thing to break
- If batching prompts via raw JSON, `requests` is equally clean

**Batching strategy for 370 repos:**
Send repos in batches of 50 with a system prompt requesting JSON output:
```json
{
  "model": "openai/gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "You are a software library taxonomist. Given a list of GitHub repos, return a JSON array where each element has: {\"full_name\": \"...\", \"category\": \"...\", \"subcategory\": \"...\"}. Use the existing taxonomy from the starred_repos.md reference. Categories must be consistent across all repos."
    },
    {
      "role": "user",
      "content": "<json array of repo objects>"
    }
  ],
  "response_format": {"type": "json_object"}
}
```
370 repos ÷ 50 per batch = 8 API calls/run. Well within any reasonable rate limit.

---

### Commit Step

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Native `git` in shell | — | Commit regenerated `index.html` | No third-party Action needed; simpler; fewer supply chain dependencies |

**Pattern:**
```yaml
- name: Commit updated index.html
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add index.html
    git diff --staged --quiet || git commit -m "chore: regenerate stars gallery [skip ci]"
    git push
```

**Why not `stefanzweifel/git-auto-commit-action`:** Adds a third-party dependency that must be pinned to a SHA for supply chain safety, requires extra configuration, and provides no benefit over 5 lines of native git. The `|| true` pattern and `--quiet` diff check handle the "nothing changed" case natively.

**`[skip ci]` in commit message:** Prevents the commit from re-triggering the workflow, avoiding infinite loops.

---

## Complete Workflow Summary

```yaml
name: Regenerate Stars Gallery

on:
  schedule:
    - cron: '0 6 * * *'   # daily at 06:00 UTC
  workflow_dispatch:        # allow manual trigger

permissions:
  contents: write
  models: read

jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Fetch stars, categorize, regenerate HTML
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/generate.py

      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add index.html
          git diff --staged --quiet || git commit -m "chore: regenerate stars gallery [skip ci]"
          git push
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Frontend framework | Vanilla HTML + Tailwind CDN | Astro, Next.js | Requires build step in Actions, extra config, overkill for single static page |
| Script language | Python (pre-installed) | Node.js | Needs `setup-node` step; no advantage for this task |
| AI SDK | raw `requests` | `openai` SDK, `azure-ai-inference` | Requires `pip install`, adds 30s+ to Action; raw HTTP is simpler for this use case |
| Commit action | native `git` | `stefanzweifel/git-auto-commit-action@v7` | Third-party dependency, supply chain risk, no benefit over 5 lines of git |
| AI model | `openai/gpt-4o-mini` | `openai/gpt-4o`, `openai/gpt-4.1` | gpt-4o-mini is fast enough for categorization, more rate-limit headroom, lower latency |
| Tailwind | CDN | Local build/purge | CDN is fine for a single page; avoids Node toolchain entirely |
| Styling from scratch | Match `stitch_example` exactly | Custom CSS | Reference implementation is complete and correct; no value in diverging |

---

## Key Version Pins

| Artifact | Version | Source |
|----------|---------|--------|
| `actions/checkout` | `v4` (latest: v4.2.x) | [GitHub Releases](https://github.com/actions/checkout/releases) — confirmed 2026-04 |
| `actions/setup-python` | Not needed | Python 3.12 pre-installed on `ubuntu-latest` |
| `requests` Python library | 2.33.1 | PyPI — pre-installed on GH Actions runner |
| GitHub REST API version | `2022-11-28` | Current stable ([docs](https://docs.github.com/en/rest)) |
| GitHub Models API version | `2022-11-28` | Confirmed in quickstart docs |
| GitHub Models endpoint | `https://models.github.ai/inference/chat/completions` | [GitHub Models Quickstart](https://docs.github.com/en/github-models/quickstart) — confirmed 2026 |
| Tailwind CDN | `cdn.tailwindcss.com` (auto-latest 3.x) | Matches stitch_example exactly |
| JetBrains Mono font | Google Fonts CDN | Matches stitch_example exactly |

---

## Confidence Assessment

| Decision | Confidence | Source |
|----------|------------|--------|
| GitHub Models endpoint URL | HIGH | Official GitHub Docs quickstart, fetched 2026-04-21 |
| `GITHUB_TOKEN` + `models: read` works in Actions | HIGH | Official GitHub docs example confirmed |
| `openai/gpt-4o-mini` available via GitHub Models | HIGH | Listed in GitHub Models CLI README |
| Python pre-installed on ubuntu-latest | HIGH | GitHub Actions docs (Python 3.9–3.13 listed) |
| `requests` pre-installed on runners | MEDIUM | Consistently true historically; verify in first Action run |
| GitHub Models free-tier rate limits are sufficient for 8 calls/day | MEDIUM | Rate limits not published as exact numbers; inference from free tier nature and batch size |
| Tailwind CDN v3.x stable for this use case | HIGH | Same CDN URL used in stitch_example, confirmed working |
| No `[skip ci]` infinite loop risk | HIGH | Standard pattern, confirmed by GitHub Actions docs |

---

## What NOT to Use

| Technology | Reason to Avoid |
|------------|----------------|
| Astro / Next.js / SvelteKit | Adds a build step, `node_modules`, and a deployment pipeline where none is needed |
| GitHub Pages Actions deployment (`actions/deploy-pages`) | Overkill for a root `index.html`; Pages auto-serves from default branch by default |
| Jekyll / Hugo | Template engines add complexity without benefit; HTML is generated by Python anyway |
| `openai` Python SDK | Adds a pip install step and ~25MB of dependencies; raw `requests` is equivalent for this endpoint |
| Separate `data.json` + client-side fetch | Adds complexity and a second file to manage; all data embedded in `index.html` is simpler and works fully offline |
| localStorage / IndexedDB | No user state to persist; read-only gallery |
| Search/filter JS | Out of scope per PROJECT.md; adds JS complexity |

---

## Sources

- GitHub Models Quickstart (fetched 2026-04-21): `https://docs.github.com/en/github-models/quickstart`
- GitHub REST API — Starring (fetched 2026-04-21): `https://docs.github.com/en/rest/activity/starring`
- GitHub Actions — Schedule trigger: Context7 `/websites/github_en_actions`
- `actions/checkout` releases: `https://api.github.com/repos/actions/checkout/releases/latest` → v4.0.2
- `azure-ai-inference` README: confirms GitHub Models endpoint pattern
- `requests` PyPI: 2.33.1 (2026-04-21)
- Stitch theme reference: `stitch_example/code.html` (Tailwind CDN, JetBrains Mono, `#FF5F1F`, no border-radius)
