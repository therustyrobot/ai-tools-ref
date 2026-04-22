"""Unit tests for scripts/fetch_stars.py — no real HTTP calls."""
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Bootstrap: import fetch_stars as a module (may not be in sys.path yet)
# ---------------------------------------------------------------------------
import importlib.util, pathlib

_ROOT = pathlib.Path(__file__).parent.parent
_MOD_PATH = _ROOT / "scripts" / "fetch_stars.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("fetch_stars", _MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Inject a fake 'requests' so the import doesn't fail if requests isn't installed
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.ModuleType("requests")
    spec.loader.exec_module(mod)
    return mod


fetch_stars = _load_module()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_repo(full_name="owner/repo", fork=False, archived=False, language="Python", stars=100):
    return {
        "full_name": full_name,
        "name": full_name.split("/")[-1],
        "html_url": f"https://github.com/{full_name}",
        "description": "A test repo",
        "language": language,
        "stargazers_count": stars,
        "fork": fork,
        "archived": archived,
    }


def _mock_response(data, link_next=None):
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    headers = {}
    if link_next:
        headers["Link"] = f'<{link_next}>; rel="next"'
    resp.headers = headers
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFetchAllStars(unittest.TestCase):

    def test_per_page_100(self):
        """First request URL must contain per_page=100."""
        repos = [_make_repo(f"owner/repo{i}") for i in range(5)]
        mock_resp = _mock_response(repos)  # no next link → single page

        with patch("requests.get", return_value=mock_resp) as mock_get:
            fetch_stars.fetch_all_stars("fake-token")

        first_url = mock_get.call_args_list[0][0][0]
        self.assertIn("per_page=100", first_url)

    def test_pagination(self):
        """Two pages of repos must both be collected."""
        page1 = [_make_repo(f"owner/r{i}") for i in range(5)]
        page2 = [_make_repo(f"owner/s{i}") for i in range(5)]

        resp1 = _mock_response(page1, link_next="https://api.github.com/user/starred?page=2&per_page=100")
        resp2 = _mock_response(page2)  # no next link

        with patch("requests.get", side_effect=[resp1, resp2]):
            result = fetch_stars.fetch_all_stars("fake-token")

        self.assertEqual(len(result), 10)


class TestFilterRepos(unittest.TestCase):

    def test_filter_forks(self):
        """Repos with fork=True must be excluded."""
        repos = [
            _make_repo("owner/forked", fork=True),
            _make_repo("owner/clean", fork=False),
        ]
        filtered = fetch_stars.filter_repos(repos)
        names = [r["full_name"] for r in filtered]
        self.assertNotIn("owner/forked", names)
        self.assertIn("owner/clean", names)

    def test_filter_archived(self):
        """Repos with archived=True must be excluded."""
        repos = [
            _make_repo("owner/archived-repo", archived=True),
            _make_repo("owner/active-repo", archived=False),
        ]
        filtered = fetch_stars.filter_repos(repos)
        names = [r["full_name"] for r in filtered]
        self.assertNotIn("owner/archived-repo", names)
        self.assertIn("owner/active-repo", names)

    def test_no_fork_no_archived_kept(self):
        """Repos with fork=False and archived=False must be retained."""
        repos = [_make_repo("owner/keep-me", fork=False, archived=False)]
        filtered = fetch_stars.filter_repos(repos)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["full_name"], "owner/keep-me")


class TestWriteRepos(unittest.TestCase):

    def test_output_schema(self):
        """Each written record must have exactly the 6 required keys."""
        repos = [_make_repo("owner/test-repo")]
        tmp_path = "/tmp/test_repos_schema.json"

        fetch_stars.write_repos(repos, path=tmp_path)

        with open(tmp_path, encoding="utf-8") as f:
            records = json.load(f)

        self.assertEqual(len(records), 1)
        expected_keys = {"full_name", "name", "html_url", "description", "language", "stargazers_count"}
        self.assertEqual(set(records[0].keys()), expected_keys)

        # Clean up
        os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
