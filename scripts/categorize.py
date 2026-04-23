#!/usr/bin/env python3
"""categorize.py — batch-categorize repos via GitHub Models API, writes _data/categories.json"""
import os
import re
import json
import requests

GITHUB_MODELS_URL = "https://models.github.ai/inference/chat/completions"
MODEL = "openai/gpt-4o-mini"
BATCH_SIZE = 10

SYSTEM_PROMPT = """You are a GitHub repository taxonomist. Classify each repository into one of the following top-level categories and subcategories. Use the existing taxonomy below. Prefer existing names over inventing new ones. Only use "Other" if no other category fits.

TAXONOMY:
- AI & ML
  - Claude Code & Skills
  - Agent Frameworks & Harnesses
  - MCP Servers & Tools
  - LLM UIs & Chat Interfaces
  - RAG & Knowledge
  - AI Productivity Tools
  - AI Infrastructure & APIs
  - Coding Agents & IDEs
  - Generalist Agents
- Self-Hosting & Homelab
  - Dashboards & Homepages
  - Password & Auth
  - Monitoring & Alerts
  - Media & Arr Stack
  - Deployment & PaaS
  - Notes & Knowledge
  - Networking & Remote Access
  - Proxmox & Containers
  - Tools & Utilities
- Dev Tools & CLI
  - Terminal & Shell
  - Documentation & Sites
  - Automation & Scraping
  - Arr & Media Tools
  - ESP32 & Embedded
  - Other Dev Tools
- DevOps & Infra
- Security
- Web & Frontend
- Data & Analytics
- Productivity & Notes
- Media & Entertainment
- Networking
- Mobile & Desktop
- Awesome Lists
- ESP32 & Hardware
- Other

Return a JSON object where each key is the repo full_name (owner/repo) and each value is:
{"category": "<top-level category name>", "subcategory": "<subcategory name>"}

If a top-level category has no subcategories, use the category name as the subcategory too.
Return ONLY valid JSON with no preamble, explanation, or markdown formatting."""


def category_to_slug(name):
    """Convert category/subcategory display name to stable URL-safe slug."""
    if not name:
        return "other"
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def build_session(token):
    """Create a requests.Session with Bearer auth headers pre-set."""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    return session


def call_model(session, messages):
    """POST to GitHub Models API, return raw content string."""
    payload = {
        "model": MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    resp = session.post(GITHUB_MODELS_URL, json=payload)
    resp.raise_for_status()  # MUST be called before .json() — project-wide invariant
    return resp.json()["choices"][0]["message"]["content"]


def strip_fences(raw):
    """Remove markdown code fences wrapping JSON."""
    return re.sub(r'```json\s*|\s*```', '', raw).strip()


def build_messages(batch):
    """Build the messages array for a batch of repos."""
    lines = []
    for repo in batch:
        desc = repo.get("description") or "No description"
        lang = repo.get("language") or "Unknown"
        stars = repo.get("stargazers_count") or 0
        lines.append(f'- {repo["full_name"]}: [{lang}, {stars} stars] {desc}')
    user_content = "Classify these repositories:\n" + "\n".join(lines)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def parse_with_retry(session, messages, batch_names):
    """Call model and parse JSON; retry once on JSONDecodeError; fall back to Other."""
    raw = call_model(session, messages)
    try:
        return json.loads(strip_fences(raw))
    except json.JSONDecodeError:
        print(f"[WARN] JSON parse failed. Raw response (first 300 chars): {raw[:300]}")
        retry_messages = messages + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Return only valid JSON, no preamble or markdown fences."},
        ]
        raw2 = call_model(session, retry_messages)
        try:
            return json.loads(strip_fences(raw2))
        except json.JSONDecodeError:
            print(f"[ERROR] JSON parse failed on retry. Assigning batch to Other. Raw: {raw2[:300]}")
            return {name: {"category": "Other", "subcategory": "Other"} for name in batch_names}


def categorize_all(repos, session):
    """Batch repos into groups of BATCH_SIZE, call model for each, return merged cat_map."""
    cat_map = {}
    for i in range(0, len(repos), BATCH_SIZE):
        batch = repos[i:i + BATCH_SIZE]
        batch_names = [r["full_name"] for r in batch]
        print(f"  Categorizing batch {i // BATCH_SIZE + 1}: {batch_names}")
        messages = build_messages(batch)
        result = parse_with_retry(session, messages, batch_names)
        for full_name, info in result.items():
            cat_map[full_name] = {
                "category":    info.get("category", "Other"),
                "subcategory": info.get("subcategory", "Other"),
                "slug":        category_to_slug(info.get("category", "Other")),
            }
        # Repos omitted from model response (valid JSON but incomplete) fall back to Other
        for name in batch_names:
            if name not in cat_map:
                print(f"[WARN] Repo {name!r} missing from model response — assigning to Other")
                cat_map[name] = {"category": "Other", "subcategory": "Other", "slug": "other"}
    return cat_map


def write_categories(cat_map, path="_data/categories.json"):
    """Write categories map to JSON file, creating directories as needed."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cat_map, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(cat_map)} entries to {path}")


if __name__ == "__main__":
    token = os.environ["GITHUB_TOKEN"]  # KeyError = fail-fast; never default to ""
    print("Loading repos...")
    with open("_data/repos.json", encoding="utf-8") as f:
        repos = json.load(f)
    print(f"Loaded {len(repos)} repos. Starting categorization in batches of {BATCH_SIZE}...")
    session = build_session(token)
    cat_map = categorize_all(repos, session)
    write_categories(cat_map)
    print(f"Done. {len(cat_map)} repos categorized.")
