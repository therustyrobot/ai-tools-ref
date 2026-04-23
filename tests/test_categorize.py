"""Unit tests for scripts/categorize.py — pure logic, no GitHub API calls."""
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

_ROOT = pathlib.Path(__file__).parent.parent
_MOD_PATH = _ROOT / "scripts" / "categorize.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("categorize", _MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    if "requests" not in sys.modules:
        sys.modules["requests"] = types.ModuleType("requests")
    spec.loader.exec_module(mod)
    return mod


cat = _load_module()


def _mock_post_response(content_str):
    """Build a mock requests.Response for a GitHub Models API POST."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "choices": [{"message": {"content": content_str}}]
    }
    return resp


class TestCategoryToSlug(unittest.TestCase):
    def test_known_categories(self):
        cases = [
            ("AI & ML",                "ai-ml"),
            ("Self-Hosting & Homelab", "self-hosting-homelab"),
            ("Dev Tools & CLI",         "dev-tools-cli"),
            ("DevOps & Infra",          "devops-infra"),
            ("Security",                "security"),
            ("Other",                   "other"),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(cat.category_to_slug(name), expected)

    def test_empty_string_returns_other(self):
        self.assertEqual(cat.category_to_slug(""), "other")

    def test_none_returns_other(self):
        self.assertEqual(cat.category_to_slug(None), "other")


class TestStripFences(unittest.TestCase):
    def test_no_fences_unchanged(self):
        self.assertEqual(cat.strip_fences('{"a": 1}'), '{"a": 1}')

    def test_json_fences_stripped(self):
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(cat.strip_fences(raw), '{"a": 1}')

    def test_bare_fences_stripped(self):
        raw = '```\n{"a": 1}\n```'
        self.assertEqual(cat.strip_fences(raw), '{"a": 1}')


class TestCallModel(unittest.TestCase):
    def test_returns_content_string(self):
        session = MagicMock()
        mock_resp = _mock_post_response('{"owner/repo": {"category": "Other"}}')
        session.post.return_value = mock_resp
        result = cat.call_model(session, [{"role": "user", "content": "test"}])
        self.assertIsInstance(result, str)
        self.assertIn("owner/repo", result)

    def test_raise_for_status_called(self):
        session = MagicMock()
        mock_resp = _mock_post_response("{}")
        session.post.return_value = mock_resp
        cat.call_model(session, [])
        mock_resp.raise_for_status.assert_called_once()

    def test_posts_to_correct_url(self):
        session = MagicMock()
        session.post.return_value = _mock_post_response("{}")
        cat.call_model(session, [])
        call_url = session.post.call_args[0][0]
        self.assertIn("models.github.ai", call_url)

    def test_response_format_in_payload(self):
        session = MagicMock()
        session.post.return_value = _mock_post_response("{}")
        cat.call_model(session, [])
        payload = session.post.call_args[1]["json"]
        self.assertEqual(payload["response_format"], {"type": "json_object"})


class TestParseWithRetry(unittest.TestCase):
    def test_success_on_first_attempt(self):
        session = MagicMock()
        content = '{"a/r": {"category": "AI & ML", "subcategory": "LLMs"}}'
        session.post.return_value = _mock_post_response(content)
        result = cat.parse_with_retry(session, [], ["a/r"])
        self.assertIn("a/r", result)
        self.assertEqual(session.post.call_count, 1)

    def test_retry_on_first_json_error(self):
        session = MagicMock()
        bad_resp = _mock_post_response("this is not json")
        good_resp = _mock_post_response('{"a/r": {"category": "Other", "subcategory": "Other"}}')
        session.post.side_effect = [bad_resp, good_resp]
        result = cat.parse_with_retry(session, [], ["a/r"])
        self.assertEqual(session.post.call_count, 2)
        self.assertIn("a/r", result)

    def test_fallback_to_other_on_two_failures(self):
        session = MagicMock()
        bad_resp = _mock_post_response("not json at all")
        session.post.side_effect = [bad_resp, bad_resp]
        result = cat.parse_with_retry(session, [], ["a/r1", "a/r2"])
        self.assertEqual(result["a/r1"]["category"], "Other")
        self.assertEqual(result["a/r2"]["category"], "Other")


class TestCategorizeAll(unittest.TestCase):
    def _make_repos(self, n):
        return [{"full_name": f"owner/repo{i}", "description": "d", "language": "Python", "stargazers_count": i}
                for i in range(n)]

    def test_batch_count_25_repos(self):
        """25 repos must produce exactly 3 API calls (10+10+5)."""
        repos = self._make_repos(25)
        content = json.dumps({r["full_name"]: {"category": "Other", "subcategory": "Other"}
                               for r in repos})
        session = MagicMock()
        session.post.return_value = _mock_post_response(content)
        cat.categorize_all(repos, session)
        self.assertEqual(session.post.call_count, 3)

    def test_slug_derived_from_category_not_model(self):
        """Slug must be derived from category name by Python, not taken from model output."""
        repos = self._make_repos(1)
        # Model returns a wrong slug — Python must override it
        content = '{"owner/repo0": {"category": "AI & ML", "subcategory": "LLMs", "slug": "WRONG"}}'
        session = MagicMock()
        session.post.return_value = _mock_post_response(content)
        result = cat.categorize_all(repos, session)
        self.assertEqual(result["owner/repo0"]["slug"], "ai-ml")

    def test_missing_from_result_gets_other(self):
        """Repo not in model response gets Other/Other."""
        repos = self._make_repos(2)
        # Model only returns one of the two repos
        content = '{"owner/repo0": {"category": "Security", "subcategory": "Security"}}'
        session = MagicMock()
        session.post.return_value = _mock_post_response(content)
        result = cat.categorize_all(repos, session)
        # repo1 missing from model response — must be assigned Other/Other
        self.assertIn("owner/repo0", result)
        self.assertEqual(result["owner/repo0"]["slug"], "security")
        self.assertIn("owner/repo1", result)
        self.assertEqual(result["owner/repo1"]["category"], "Other")
        self.assertEqual(result["owner/repo1"]["slug"], "other")


class TestWriteCategories(unittest.TestCase):
    def test_creates_file_with_correct_content(self):
        cat_map = {"a/r": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"}}
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "_data", "categories.json")
            cat.write_categories(cat_map, path=out_path)
            self.assertTrue(os.path.exists(out_path))
            with open(out_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["a/r"]["slug"], "ai-ml")


if __name__ == "__main__":
    unittest.main()
