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
CATEGORIES_FIXTURE_PATH = _ROOT / "tests" / "fixtures" / "sample_categories.json"


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
# Tests: CATEGORY_META
# ---------------------------------------------------------------------------
class TestCategoryMetaLookup(unittest.TestCase):

    def test_all_14_slugs_present(self):
        """All 14 locked slugs from D-08 must exist in CATEGORY_META."""
        expected = [
            "ai-ml", "self-hosting-homelab", "dev-tools-cli", "devops-infra",
            "security", "web-frontend", "data-analytics", "productivity-notes",
            "media-entertainment", "networking", "mobile-desktop",
            "awesome-lists", "esp32-hardware", "other",
        ]
        for slug in expected:
            with self.subTest(slug=slug):
                self.assertIn(slug, gen.CATEGORY_META)

    def test_values_are_2_tuples(self):
        """Each CATEGORY_META value must be a 2-tuple (display_name, icon_name) — NOT 3-tuple."""
        for slug, val in gen.CATEGORY_META.items():
            with self.subTest(slug=slug):
                self.assertEqual(len(val), 2)

    def test_ai_ml_entry(self):
        """ai-ml entry must have correct display name and Material Icon."""
        display_name, icon_name = gen.CATEGORY_META["ai-ml"]
        self.assertEqual(display_name, "AI & ML")
        self.assertEqual(icon_name, "smart_toy")


# ---------------------------------------------------------------------------
# Tests: Hierarchical grouping
# ---------------------------------------------------------------------------
class TestGroupByCategoriesHierarchical(unittest.TestCase):

    def test_nesting_structure(self):
        """Result must be {category: {subcategory: [repos]}}."""
        repos = [_make_repo("a/r1", stars=100)]
        cat_map = {"a/r1": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"}}
        result = gen.group_by_categories_hierarchical(repos, cat_map)
        self.assertIn("AI & ML", result)
        self.assertIn("LLMs", result["AI & ML"])
        self.assertEqual(len(result["AI & ML"]["LLMs"]), 1)

    def test_missing_from_cat_map_falls_to_other(self):
        """Repo not in cat_map must land in 'Other' > 'Other'."""
        repos = [_make_repo("a/unknown", stars=50)]
        result = gen.group_by_categories_hierarchical(repos, {})
        self.assertIn("Other", result)
        self.assertIn("Other", result["Other"])

    def test_sort_order_within_subcategory(self):
        """Repos within a subcategory must be sorted highest stars first."""
        repos = [_make_repo("a/r1", stars=10), _make_repo("a/r2", stars=500)]
        cat_map = {
            "a/r1": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"},
            "a/r2": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"},
        }
        result = gen.group_by_categories_hierarchical(repos, cat_map)
        counts = [r["stargazers_count"] for r in result["AI & ML"]["LLMs"]]
        self.assertEqual(counts, sorted(counts, reverse=True))


# ---------------------------------------------------------------------------
# Tests: Subcategory header rendering
# ---------------------------------------------------------------------------
class TestRenderSubcategoryHeader(unittest.TestCase):

    def test_orange_background_class(self):
        """Subcategory header must contain Safety Orange bg class (D-02)."""
        html_out = gen.render_subcategory_header("LLMs", 5, 1)
        self.assertIn("bg-[#FF5F1F]", html_out)

    def test_entry_count_displayed(self):
        """ENTRIES count must appear in subcategory header HTML."""
        html_out = gen.render_subcategory_header("LLMs", 7, 1)
        self.assertIn("ENTRIES: 7", html_out)

    def test_data_subcategory_attribute(self):
        """data-subcategory attribute must be present with correct slug."""
        html_out = gen.render_subcategory_header("LLMs", 3, 1)
        self.assertIn('data-subcategory="llms"', html_out)

    def test_html_escaped_subcat_name(self):
        """Subcategory name with special chars must be HTML-escaped."""
        html_out = gen.render_subcategory_header("A & B", 1, 1)
        self.assertIn("&amp;", html_out)
        self.assertNotIn(" & B", html_out)


# ---------------------------------------------------------------------------
# Tests: Hierarchical nav rendering
# ---------------------------------------------------------------------------
class TestRenderNavHierarchical(unittest.TestCase):

    def test_top_level_anchor_links_only(self):
        """Nav must contain top-level category anchors only — not subcategory anchors (D-03)."""
        hier_groups = {
            "AI & ML": {
                "LLMs": [_make_repo("a/r1", stars=100)],
                "Agents": [_make_repo("a/r2", stars=50)],
            }
        }
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn('href="#ai-ml"', nav_html)
        self.assertNotIn('href="#llms"', nav_html)
        self.assertNotIn('href="#agents"', nav_html)

    def test_count_sums_across_subcategories(self):
        """Count badge must sum repos across all subcategories of a category."""
        hier_groups = {
            "AI & ML": {
                "LLMs": [_make_repo("a/r1"), _make_repo("a/r2")],
                "Agents": [_make_repo("a/r3")],
            }
        }
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn(">3<", nav_html)

    def test_material_icon_for_known_category(self):
        """Known CATEGORY_META slug must render a material-icons span in the nav."""
        hier_groups = {"AI & ML": {"LLMs": [_make_repo()]}}
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn('class="material-icons', nav_html)
        self.assertIn("smart_toy", nav_html)


# ---------------------------------------------------------------------------
# Tests: Hierarchical integration (writes docs/index.html with categories)
# ---------------------------------------------------------------------------
class TestOutputFileHierarchical(unittest.TestCase):

    def setUp(self):
        self.orig_dir = os.getcwd()
        self.tmp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp_dir, "_data"))
        shutil.copy(FIXTURE_PATH, os.path.join(self.tmp_dir, "_data", "repos.json"))
        shutil.copy(CATEGORIES_FIXTURE_PATH,
                    os.path.join(self.tmp_dir, "_data", "categories.json"))
        os.makedirs(os.path.join(self.tmp_dir, "docs"), exist_ok=True)
        os.chdir(self.tmp_dir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_hierarchical_output_file_created(self):
        """Hierarchical pipeline produces non-empty docs/index.html."""
        repos = gen.load_repos(os.path.join(self.tmp_dir, "_data", "repos.json"))
        cat_map = gen.load_categories(os.path.join(self.tmp_dir, "_data", "categories.json"))
        self.assertTrue(cat_map, "categories.json must be non-empty for this test")
        hier_groups = gen.group_by_categories_hierarchical(repos, cat_map)
        nav_html = gen.render_nav_hierarchical(hier_groups)
        sections_html = gen.render_sections_hierarchical(hier_groups)
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
        self.assertIn("bg-[#FF5F1F]", content)   # subcategory header rendered (D-02)
        self.assertIn("data-subcategory=", content)


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


# ---------------------------------------------------------------------------
# Tests: v1.1 Data Attributes (IMPL-02, IMPL-03, IMPL-04)
# ---------------------------------------------------------------------------
class TestDataAttributesOnCards(unittest.TestCase):
    """Verify render_card emits data-name, data-desc, data-category (IMPL-02)."""

    def test_data_name_present(self):
        """Card HTML must contain data-name with full_name value."""
        repo = _make_repo("owner/myrepo", stars=100)
        card_html = gen.render_card(repo, 0, 0, "ai-ml")
        self.assertIn('data-name="owner/myrepo"', card_html)

    def test_data_desc_present(self):
        """Card HTML must contain data-desc with description value."""
        repo = _make_repo("a/b", description="A cool tool", stars=100)
        card_html = gen.render_card(repo, 0, 0, "dev-tools-cli")
        self.assertIn('data-desc="A cool tool"', card_html)

    def test_data_desc_empty_when_no_description(self):
        """Card HTML must have data-desc='' when description is None."""
        repo = _make_repo("a/b", description=None, stars=100)
        card_html = gen.render_card(repo, 0, 0, "other")
        self.assertIn('data-desc=""', card_html)

    def test_data_category_matches_slug(self):
        """Card HTML must contain data-category equal to the passed cat_slug."""
        repo = _make_repo("a/b", stars=100)
        card_html = gen.render_card(repo, 0, 0, "security")
        self.assertIn('data-category="security"', card_html)

    def test_data_category_default_is_other(self):
        """render_card with no cat_slug argument must default to data-category='other'."""
        repo = _make_repo("a/b", stars=100)
        card_html = gen.render_card(repo, 0, 0)
        self.assertIn('data-category="other"', card_html)

    def test_sections_hierarchical_cards_have_data_category(self):
        """Hierarchical sections HTML must contain data-category on every card."""
        repos = [_make_repo("a/r1", stars=100)]
        cat_map = {"a/r1": {"category": "AI & ML", "subcategory": "LLMs", "slug": "ai-ml"}}
        hier = gen.group_by_categories_hierarchical(repos, cat_map)
        html_out = gen.render_sections_hierarchical(hier)
        self.assertIn('data-category="ai-ml"', html_out)


class TestDataFilterOnNavLinks(unittest.TestCase):
    """Verify render_nav_hierarchical emits data-filter and filter-btn class (IMPL-03)."""

    def test_data_filter_on_hierarchical_nav(self):
        """Nav links must have data-filter='{slug}' attribute."""
        hier_groups = {"AI & ML": {"LLMs": [_make_repo()]}}
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn('data-filter="ai-ml"', nav_html)

    def test_filter_btn_class_on_hierarchical_nav(self):
        """Nav links must have 'filter-btn' class."""
        hier_groups = {"AI & ML": {"LLMs": [_make_repo()]}}
        nav_html = gen.render_nav_hierarchical(hier_groups)
        self.assertIn('filter-btn', nav_html)

    def test_data_filter_on_flat_nav(self):
        """render_nav flat mode must also have data-filter attribute."""
        groups = {"Python": [_make_repo()]}
        nav_html = gen.render_nav(groups)
        self.assertIn('data-filter="python"', nav_html)

    def test_filter_btn_class_on_flat_nav(self):
        """render_nav flat mode must also have 'filter-btn' class."""
        groups = {"Python": [_make_repo()]}
        nav_html = gen.render_nav(groups)
        self.assertIn('filter-btn', nav_html)


class TestSearchInputAndScriptTag(unittest.TestCase):
    """Verify render_page emits search input and script tag (IMPL-01, UX-01)."""

    def _render(self):
        import datetime
        return gen.render_page("<li>nav</li>", "<section>x</section>", 1,
                               datetime.datetime.utcnow())

    def test_search_input_present(self):
        """render_page HTML must contain search input with id='search-input'."""
        page = self._render()
        self.assertIn('id="search-input"', page)

    def test_search_input_before_index_categories(self):
        """search-input must appear before 'INDEX // CATEGORIES' in HTML (UX-01)."""
        page = self._render()
        idx_input = page.find('id="search-input"')
        idx_label = page.find('INDEX // CATEGORIES')
        self.assertGreater(idx_input, 0)
        self.assertGreater(idx_label, 0)
        self.assertLess(idx_input, idx_label)

    def test_script_tag_present(self):
        """render_page HTML must contain <script src='search.js'>."""
        page = self._render()
        self.assertIn('<script src="search.js">', page)

    def test_script_tag_before_body_close(self):
        """<script src='search.js'> must appear before </body>."""
        page = self._render()
        idx_script = page.find('<script src="search.js">')
        idx_body = page.find('</body>')
        self.assertGreater(idx_script, 0)
        self.assertGreater(idx_body, 0)
        self.assertLess(idx_script, idx_body)

    def test_clear_button_present(self):
        """render_page HTML must contain the × clear button (UX-03)."""
        page = self._render()
        self.assertIn('id="search-clear"', page)
