"""Unit tests for scripts/generate.py — pure logic, no GitHub API calls."""
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import shutil
import unittest

# ---------------------------------------------------------------------------
# Bootstrap: load generate.py from file path (avoids __main__ side-effects)
# ---------------------------------------------------------------------------
_ROOT = pathlib.Path(__file__).parent.parent
_MOD_PATH = _ROOT / "scripts" / "generate.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate", _MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Prevent __main__ block from running during import
    original_name = getattr(spec, "name", None)
    spec.loader.exec_module(mod)
    return mod


gen = _load_module()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
FIXTURE_PATH = _ROOT / "tests" / "fixtures" / "sample_repos.json"


def _make_repo(full_name="owner/repo", language="Python", stars=100, description="desc"):
    return {
        "full_name": full_name,
        "name": full_name.split("/")[-1],
        "html_url": f"https://github.com/{full_name}",
        "description": description,
        "language": language,
        "stargazers_count": stars,
    }


# ---------------------------------------------------------------------------
# Tests: Formatting
# ---------------------------------------------------------------------------
class TestFmtStars(unittest.TestCase):

    def test_fmt_stars(self):
        cases = [
            (999, "999"),
            (1000, "1K"),
            (1200, "1.2K"),
            (42000, "42K"),
            (1_500_000, "1.5M"),
        ]
        for n, expected in cases:
            with self.subTest(n=n):
                self.assertEqual(gen.fmt_stars(n), expected)


# ---------------------------------------------------------------------------
# Tests: Language slug
# ---------------------------------------------------------------------------
class TestLanguageToSlug(unittest.TestCase):

    def test_language_to_slug(self):
        cases = [
            ("Python", "python"),
            ("C++", "cpp"),
            ("C#", "csharp"),
            ("Jupyter Notebook", "jupyter"),
            (None, "other"),
        ]
        for lang, expected in cases:
            with self.subTest(lang=lang):
                self.assertEqual(gen.language_to_slug(lang), expected)


# ---------------------------------------------------------------------------
# Tests: Grouping
# ---------------------------------------------------------------------------
class TestGroupByLanguage(unittest.TestCase):

    def test_group_by_language_sort_order(self):
        """Repos within a group must be sorted highest stars first."""
        repos = [
            _make_repo("a/r1", stars=100),
            _make_repo("a/r2", stars=500),
            _make_repo("a/r3", stars=200),
        ]
        groups = gen.group_by_language(repos)
        python_repos = groups["Python"]
        star_counts = [r["stargazers_count"] for r in python_repos]
        self.assertEqual(star_counts, sorted(star_counts, reverse=True))

    def test_group_ordering_by_total_stars(self):
        """Group with higher total star count must appear first."""
        repos = [
            _make_repo("a/big1", language="Go", stars=50000),
            _make_repo("a/big2", language="Go", stars=40000),
            _make_repo("a/small1", language="Rust", stars=1000),
        ]
        groups = gen.group_by_language(repos)
        group_names = list(groups.keys())
        self.assertEqual(group_names[0], "Go")


# ---------------------------------------------------------------------------
# Tests: Rendering
# ---------------------------------------------------------------------------
class TestRenderNav(unittest.TestCase):

    def test_render_nav_contains_slug(self):
        """render_nav must produce anchor links with correct slugs."""
        groups = {"Python": [_make_repo("a/repo", language="Python", stars=100)]}
        nav_html = gen.render_nav(groups)
        self.assertIn('href="#python"', nav_html)


class TestRenderSection(unittest.TestCase):

    def test_render_section_header(self):
        """Section HTML must include emoji, TOTAL_ENTRIES count, and id= slug."""
        repos = [_make_repo("a/r1", stars=100), _make_repo("a/r2", stars=200)]
        groups = {"Python": repos}
        sections_html = gen.render_sections(groups)
        self.assertIn('id="python"', sections_html)
        self.assertIn("TOTAL_ENTRIES: 2", sections_html)
        # Python emoji from LANG_META
        self.assertIn("🐍", sections_html)


class TestHtmlEscape(unittest.TestCase):

    def test_html_escape_in_card(self):
        """Dangerous chars in description must be HTML-escaped in output."""
        repos = [_make_repo("a/r1", description="A & B <test>", stars=100)]
        groups = {"Python": repos}
        sections_html = gen.render_sections(groups)
        self.assertIn("&amp;", sections_html)
        self.assertIn("&lt;", sections_html)
        # Raw characters must NOT appear unescaped
        self.assertNotIn(" & B", sections_html)


# ---------------------------------------------------------------------------
# Tests: Integration (writes docs/index.html)
# ---------------------------------------------------------------------------
class TestOutputFileCreated(unittest.TestCase):

    def setUp(self):
        self.orig_dir = os.getcwd()
        self.tmp_dir = tempfile.mkdtemp()
        # Create _data/ dir with fixture
        os.makedirs(os.path.join(self.tmp_dir, "_data"))
        shutil.copy(FIXTURE_PATH, os.path.join(self.tmp_dir, "_data", "repos.json"))
        os.makedirs(os.path.join(self.tmp_dir, "docs"), exist_ok=True)
        os.chdir(self.tmp_dir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_output_file_created(self):
        """Running generate logic must produce a non-empty docs/index.html."""
        repos = gen.load_repos(os.path.join(self.tmp_dir, "_data", "repos.json"))
        cat_map = gen.load_categories(os.path.join(self.tmp_dir, "_data", "categories.json"))
        groups = gen.group_by_categories(repos, cat_map) if cat_map else gen.group_by_language(repos)
        nav_html = gen.render_nav(groups)
        sections_html = gen.render_sections(groups)
        import datetime
        page = gen.render_page(nav_html, sections_html, len(repos), datetime.datetime.utcnow())
        out_path = os.path.join(self.tmp_dir, "docs", "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)

        self.assertTrue(os.path.exists(out_path))
        with open(out_path, encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 1000)
        self.assertIn("data-category=", content)
        self.assertIn("file-num", content)


if __name__ == "__main__":
    unittest.main()
