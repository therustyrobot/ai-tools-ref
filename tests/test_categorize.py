"""Unit tests for scripts/categorize.py — pure logic, no GitHub API calls.

This file starts as a minimal RED stub (Task 1 TDD gate) and is expanded
to the full 6-class suite in Task 2.
"""
import importlib.util
import pathlib
import sys
import types
import unittest

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


class TestCategoryToSlugStub(unittest.TestCase):
    """Minimal RED gate: verify module loads and core invariants hold."""

    def test_batch_size_is_10(self):
        self.assertEqual(cat.BATCH_SIZE, 10)

    def test_ai_ml_slug(self):
        self.assertEqual(cat.category_to_slug("AI & ML"), "ai-ml")

    def test_empty_returns_other(self):
        self.assertEqual(cat.category_to_slug(""), "other")


if __name__ == "__main__":
    unittest.main()
