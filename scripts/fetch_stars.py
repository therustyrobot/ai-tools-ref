#!/usr/bin/env python3
"""fetch_stars.py — fetch all starred repos from GitHub API and write _data/repos.json"""
import os
import re
import json
import requests

FIELDS = ["full_name", "name", "html_url", "description", "language", "stargazers_count"]


def get_next_url(response):
    """Parse the Link header and return the 'next' URL, or None if last page."""
    link = response.headers.get("Link", "")
    match = re.search(r'<([^>]+)>;\s*rel="next"', link)
    return match.group(1) if match else None


def fetch_all_stars(token):
    """Fetch every starred repo for the authenticated user, following pagination."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = "https://api.github.com/user/starred?per_page=100"
    all_repos = []
    while url:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()  # MUST be called before .json()
        page = resp.json()
        all_repos.extend(page)
        print(f"  fetched page: {len(page)} repos (total so far: {len(all_repos)})")
        url = get_next_url(resp)
    return all_repos


def filter_repos(repos):
    """Remove forked and archived repos."""
    return [r for r in repos if not r.get("fork") and not r.get("archived")]


def write_repos(repos, path="_data/repos.json"):
    """Project to FIELDS and write JSON array to path, creating directories as needed."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    records = [{k: r.get(k) for k in FIELDS} for r in repos]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(records)} repos to {path}")


if __name__ == "__main__":
    token = os.environ["GITHUB_TOKEN"]  # KeyError = fail-fast; never default to ""
    print("Fetching stars for authenticated user...")
    raw = fetch_all_stars(token)
    print(f"Total fetched: {len(raw)} (before filters)")
    filtered = filter_repos(raw)
    print(f"After filtering forks/archived: {len(filtered)}")
    write_repos(filtered)
