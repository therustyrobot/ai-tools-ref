# Domain Pitfalls — GitHub Stars Gallery with AI Categorization

**Project:** AI Stars Gallery (ai-tools-ref)
**Researched:** 2026-04-21
**Scope:** GitHub Actions pipeline, GitHub Models AI, static HTML generation, GitHub Pages hosting

---

## Critical Pitfalls

Mistakes that cause pipeline failures, garbled output, or rewrites.

---

### Pitfall 1: GitHub Models Daily Request Cap Breaks Full Re-categorization

**What goes wrong:**
The decision to "re-categorize all repos on every run" collides directly with GitHub Models' daily request caps. At 370 repos with a **Low-tier** model (Copilot Free/Pro):
- Limit: 150 requests/day
- If you send 1 repo per request: **370 calls needed vs 150 allowed** → pipeline fails at ~40% completion
- With a **High-tier** model (GPT-4o class): 50 requests/day → fails at ~13% completion

**Why it happens:**
The daily cap resets on a 24-hour clock. A pipeline that doesn't batch will hit the limit mid-run, leaving the HTML in a partially-regenerated state — or worse, not generating it at all.

**Consequences:**
- Incomplete categorization data → broken HTML output
- Silently missing repos in the gallery with no user-facing error
- Pipeline appears to succeed while output is wrong

**Prevention:**
Batch repos into groups per API call. Minimum safe batch sizes (Copilot Free/Pro):
| Model tier | Daily limit | Batch size for 370 repos | Calls needed |
|------------|-------------|--------------------------|--------------|
| Low (e.g. gpt-4o-mini) | 150/day | ≥ 3 repos/call | 124 calls |
| High (e.g. gpt-4o) | 50/day | ≥ 8 repos/call | 47 calls |

**Recommended:** Use a Low-tier model in batches of 10 repos per call → 37 calls total (well under 150 limit). Low-tier has 8000 input tokens per request — a batch of 10 repo descriptions typically uses ~2000–3000 tokens, leaving headroom.

**Detection:** Add an explicit pre-flight check: query `/rate_limit` (or GitHub Models equivalent) before starting. If remaining < repos/batch_size, abort with a clear error.

**Phase:** Phase 1 (AI categorization step) — design batching before writing any AI call code.

---

### Pitfall 2: Taxonomy Drift — Categories Change Every Run

**What goes wrong:**
Full re-categorization on every run means the LLM generates a fresh taxonomy each time with no memory of previous runs. Even with the same repos, the model may:
- Merge "Machine Learning" and "Deep Learning" into "AI/ML" one day, then split them the next
- Rename "Developer Tools" → "DevTooling" → "Dev Toolbox" across runs
- Put a repo in "Infrastructure" one day and "Cloud" the next

**Why it happens:**
LLMs are statistically non-deterministic. Even `temperature=0` doesn't fully eliminate variation at the taxonomy level (category naming, grouping decisions). With batching, different batches may generate inconsistent category names.

**Consequences:**
- The category navigation rearranges itself daily — confusing for the user
- Repos appear to move categories without any actual change to the star list
- If user bookmarks `#machine-learning`, that anchor may not exist the next day

**Prevention:**
1. **Seed the prompt with the existing taxonomy.** On every run, read the previous `categories.json` (or embedded JSON in the HTML) and include it in the system prompt: *"Use these existing categories unless a repo clearly doesn't fit any of them."*
2. **Separate taxonomy discovery from repo assignment.** Step 1: Generate categories (one API call with all repo names/descriptions). Step 2: Assign each batch of repos to the fixed category list from Step 1.
3. **Store the canonical category list** in a committed `categories.json` file. The pipeline updates it only when the star list changes substantially (e.g. 10+ new repos).

**Reference:** `starred_repos.md` in this repo (370 repos already organized) is the perfect seed taxonomy for the first run.

**Phase:** Phase 1 (AI prompt design) — bake in taxonomy seeding before the first pipeline run.

---

### Pitfall 3: No-Change Commits Pollute Git History and Trigger Unnecessary Deploys

**What goes wrong:**
The Action runs daily. If no new repos were starred and categories haven't changed, it regenerates the identical HTML file and commits it anyway. This creates:
- Daily noise commits ("Regenerate gallery - 2026-04-22")
- Triggers a new GitHub Pages deployment for nothing
- Unnecessary git object accumulation

**Why it happens:**
The pipeline doesn't check whether the output changed before committing.

**Consequences:**
- Git log becomes useless signal (every commit looks the same)
- GitHub Pages deploys burn against the 10 builds/hour limit (for branch-based deployments)
- Repo clones get heavier over time

**Prevention:**
```bash
# Before committing, check if the generated file differs from HEAD
git diff --quiet index.html || git commit -m "Update gallery $(date +%Y-%m-%d)"
```
Only commit if `git diff` shows changes. If no change, exit 0 cleanly.

**Detection:** Warning sign: commit timestamps are exactly 24 hours apart with no star activity.

**Phase:** Phase 2 (GitHub Action workflow) — add the diff-gate before the commit step.

---

### Pitfall 4: GITHUB_TOKEN Commits Don't Trigger Other GitHub Actions Workflows

**What goes wrong:**
If GitHub Pages is configured with a separate deployment workflow (triggered by `push` to `main`), and the stars-update Action commits using `GITHUB_TOKEN`, **that commit will not trigger the push-based deployment workflow**.

**Why it happens:**
GitHub intentionally prevents `GITHUB_TOKEN`-authenticated pushes from triggering workflow `push` events to prevent infinite loops. This is documented behavior, not a bug.

**Consequences:**
- HTML is committed but Pages is never deployed
- The live site silently stays out of date
- No error — the Action reports success

**Prevention (choose one):**
1. **Use `actions/deploy-pages` directly** in the same Action workflow — publish the HTML artifact directly to Pages without a separate workflow. This also bypasses the 10 builds/hour limit entirely.
2. **Use a Personal Access Token (PAT)** stored as `secrets.GH_PAT` instead of `GITHUB_TOKEN` for the commit step — PAT pushes do trigger downstream workflows.
3. **Avoid separate deployment workflow entirely** — have the stars Action deploy Pages itself in one job.

**Recommended:** Option 1. Use `actions/upload-pages-artifact` + `actions/deploy-pages` in the same workflow. No separate deployment workflow needed.

**Phase:** Phase 2 (GitHub Action workflow setup).

---

### Pitfall 5: LLM Response Is Not Valid JSON — Silent Data Loss

**What goes wrong:**
When prompting GitHub Models for categorization with JSON output, the model sometimes:
- Wraps JSON in markdown code fences (` ```json ... ``` `)
- Includes a preamble ("Here are the categories:") before the JSON
- Generates truncated JSON when output token limit is hit
- Returns valid JSON but with unexpected schema (wrong keys, nested differently)

**Why it happens:**
Models are not deterministic JSON serializers. Even with `response_format: { type: "json_object" }` (when supported), edge cases exist.

**Consequences:**
- `JSON.parse()` throws → entire batch's categorization is lost
- Partial output written to HTML if error handling is absent
- Hard-to-debug failures on specific repo batches

**Prevention:**
1. **Use `response_format: { type: "json_object" }` if the chosen model supports it** (GPT-4o, gpt-4o-mini support this via the Azure inference endpoint).
2. **Strip markdown fences** before parsing: `content.replace(/```json\n?|\n?```/g, '')`
3. **Validate the parsed structure** against an expected schema before using it.
4. **On parse failure, retry once** with a clarifying message ("Your previous response was not valid JSON. Return only valid JSON.").
5. **Log the raw response** to the Action's log on failure for debugging.

**Phase:** Phase 1 (AI integration code).

---

## Moderate Pitfalls

---

### Pitfall 6: GitHub API Pagination — Default Returns 30, Not All Repos

**What goes wrong:**
`GET /user/starred` without `per_page` parameter returns **30 repos** by default. If the code doesn't paginate, it silently processes only the first page.

**Why it happens:**
GitHub API defaults: `per_page=30`, `page=1`. Max is `per_page=100`. With 370 repos, you need ≥ 4 API calls.

**Prevention:**
Always set `per_page=100` and loop until the `Link` response header has no `rel="next"`, or until the returned array length is less than `per_page`.

```bash
# Check if there's a next page
link_header=$(curl -I "https://api.github.com/user/starred?per_page=100&page=1" -H "Authorization: token $GITHUB_TOKEN" | grep '^link:')
# Parse rel="next" from link_header
```

**Detection:** Gallery shows exactly 30 (or 100) repos — always a suspiciously round number.

**Phase:** Phase 2 (API fetch step).

---

### Pitfall 7: Git History Bloat from Daily HTML Commits

**What goes wrong:**
A 300KB HTML file committed daily: 
- Raw object size: ~107 MB/year before compression
- With git delta compression (~90% similarity between daily versions): ~11 MB/year effective
- After 3 years: GitHub warns when repo exceeds 1 GB (hard) or 100 MB (soft)

At 300KB changing by ~1% daily, delta compression is very effective. But if the HTML structure changes significantly (e.g. new Tailwind classes, category reorder), compression ratios drop.

**Prevention:**
1. **Separate the data from the presentation.** Commit `data/stars.json` (the raw categorized data) and `index.html` (generated from it). The JSON will compress much better than HTML.
2. **Use `--depth=1` or `--no-checkout` in `actions/checkout`** during the Action run to avoid cloning full history unnecessarily (speeds up the Action).
3. **Consider `.gitattributes`** with `index.html linguist-generated=true` to mark it as generated (affects GitHub diffs).

**Detection:** `git count-objects -vH` showing repo size growing >10MB/year.

**Phase:** Phase 2 (data architecture decision — store JSON separately before writing HTML generator).

---

### Pitfall 8: Tailwind CDN Creates External Dependency for Styling

**What goes wrong:**
The `stitch_example/code.html` uses Tailwind via CDN (`<script src="https://cdn.tailwindcss.com">`). If the CDN is unreachable (outage, network issue, CDN deprecation), the page renders unstyled.

**Why it happens:**
CDN-based Tailwind is a development convenience. Tailwind's own docs recommend against it for production — it generates the full ~3MB CSS at runtime in the browser.

**Consequences:**
- 3MB runtime JS/CSS generation in the browser (slow initial render)
- Styling fails if CDN is down
- Content Security Policy issues if headers are strict

**Prevention:**
Use the **Tailwind CLI to generate a minified CSS file** as part of the Action run, then embed or commit it alongside `index.html`. With only the classes used in the gallery, output will be ~10–30KB.

```bash
npx tailwindcss -i ./styles.css -o ./dist/styles.css --minify
```

**Phase:** Phase 3 (HTML generation — generate static CSS in the Action, don't depend on CDN).

---

### Pitfall 9: GitHub Models Tokens-Per-Request Limits Silently Truncate Batches

**What goes wrong:**
Free tier token limit: **8000 input tokens** per request. If a batch of repos has unusually long descriptions, the input can exceed 8000 tokens, causing:
- A 413/400 error from the API
- Or silent truncation (model sees partial last repo)

**Calculation:**
- Average tokens per repo: ~50–100 (name + description + language + stars)
- A batch of 10: ~500–1000 tokens → safe
- A batch of 50: ~2500–5000 tokens → approaching limit with long descriptions

**Prevention:**
1. Calculate estimated token count before sending: `Math.ceil(batchText.length / 4)` (rough estimate, 4 chars per token).
2. If estimated tokens exceed 6000 (leaving buffer), split the batch.
3. Trim descriptions to max 200 characters before sending to the model — the full description isn't needed for categorization.

**Phase:** Phase 1 (AI batching logic).

---

### Pitfall 10: GitHub Pages Build Delay Makes "Daily Update" Feel Stale

**What goes wrong:**
GitHub Pages deployments take 1–10 minutes after a commit. If you need the update at exactly midnight, the actual page update may not be live until 12:10 AM. 

For a "daily gallery", this is cosmetic — but if users check the page shortly after the scheduled Action runs, they see old content.

**Prevention:**
Add a "Last updated" timestamp directly in the generated HTML:
```html
<p class="text-xs text-gray-500">Last updated: 2026-04-21 02:03 UTC</p>
```
This way, even during the propagation delay, the old page clearly shows when it was last updated.

**Phase:** Phase 3 (HTML template — include last-updated timestamp from day one).

---

### Pitfall 11: Action Runs on Wrong Account (Repo Not Moved Yet)

**What goes wrong:**
PROJECT.md explicitly notes: *"Repo must be moved to the GitHub account that owns the starred repos before the GitHub Action automation can be enabled."*

`GITHUB_TOKEN` in an Action is scoped to the **repo's owner**. If the repo lives on account A but the stars belong to account B, `GET /user/starred` returns account A's stars (or zero stars), not account B's.

**Why it happens:**
`GITHUB_TOKEN` authenticates as the repo owner — it cannot cross account boundaries.

**Consequences:**
- Action appears to succeed but generates a gallery of the wrong person's stars (or an empty gallery)
- Hard to detect without manually comparing output vs expected stars

**Prevention:**
Add an assertion at the start of the Action:
```bash
CURRENT_USER=$(gh api /user --jq .login)
echo "Fetching stars for: $CURRENT_USER"
# Fail loudly if this is not the expected account
```

**Detection:** Generated gallery has 0 repos or obviously wrong repos.

**Phase:** Phase 2 (Action setup) — add account assertion as first step.

---

## Minor Pitfalls

---

### Pitfall 12: Archived / Forked Repos Dilute the Gallery

**What goes wrong:**
GitHub stars include repos the user has forked and archived repos. These appear in the gallery but provide low signal (forks are usually personal throwaway copies, archived repos may be defunct).

**Prevention:**
Filter in the fetch step:
```bash
# Filter out forks and archived repos before passing to AI
jq '[.[] | select(.fork == false and .archived == false)]'
```

**Phase:** Phase 2 (data fetch step).

---

### Pitfall 13: GitHub Actions 6-Hour Job Timeout

**What goes wrong:**
GitHub Actions jobs have a 6-hour maximum timeout. This is only relevant if batching + rate-limiting leads to many `sleep` waits. At 15 RPM (low tier), a 37-call run with no rate limiting takes ~3 minutes. But if the rate limit is hit and the code sleeps to recover, it could extend significantly.

**Prevention:**
Design the pipeline to fail fast on rate limit errors rather than sleep-retry. The daily schedule ensures tomorrow's run will complete what today's didn't (if using incremental categorization). If using full re-categorization, ensure batch sizes are chosen so the run completes in under 150 requests (far from the 6-hour limit).

**Phase:** Phase 2 (error handling in Action).

---

### Pitfall 14: HTML Anchor IDs for Category Navigation Break on Rename

**What goes wrong:**
If category names are generated dynamically (e.g., "Machine Learning"), the anchor IDs (`#machine-learning`) change whenever the category is renamed. Any bookmarks or external links break.

**Prevention:**
Use stable category slugs derived from a canonical list (see Pitfall 2 — taxonomy seeding). If a category is renamed, preserve the old slug as an alias with `<span id="old-slug"></span>`.

**Phase:** Phase 3 (HTML generation — stable slug generation).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| AI prompt design | Taxonomy drift (P2), JSON parse failure (P5) | Seed prompt with existing categories; use json_object response format |
| Batch size calculation | Daily cap exceeded (P1), token limit hit (P9) | Calculate before coding: Low-tier = 10 repos/batch = 37 calls |
| GitHub Action YAML | Wrong account fetching stars (P11), GITHUB_TOKEN deploy trigger (P4) | Add account assertion; use deploy-pages action |
| API pagination | First-page-only bug (P6) | Always use `per_page=100` + Link header loop |
| HTML generation | CDN dependency (P8), anchor stability (P14) | Generate static CSS; use stable category slugs |
| Git commit step | No-change commits (P3), history bloat (P7) | Diff-gate before commit; store `stars.json` alongside HTML |
| Pages configuration | Build delay UX (P10) | Embed last-updated timestamp in HTML |

---

## Sources

- GitHub REST API docs — rate limits, starring endpoints: https://docs.github.com/en/rest/activity/starring (HIGH confidence)
- GitHub Models rate limit table (confirmed from docs page): https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models#rate-limits (HIGH confidence)
  - Low tier: 15 RPM, **150 req/day** (Copilot Free/Pro), 8000 in / 4000 out tokens
  - High tier: 10 RPM, **50 req/day** (Copilot Free/Pro), 8000 in / 4000 out tokens
- GitHub Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits (HIGH confidence)
  - Site max: 1 GB; 10 builds/hour (branch deployments); 100 GB/month bandwidth; deploy timeout: 10 min
  - **10 builds/hour limit does NOT apply to custom Actions workflows using `actions/deploy-pages`**
- GitHub Actions GITHUB_TOKEN push behavior: documented non-triggering of downstream push workflows (HIGH confidence)
- Numeric calculations (batch sizes, file sizes): derived from project data (370 repos, 300KB HTML estimate) — MEDIUM confidence on exact file size
