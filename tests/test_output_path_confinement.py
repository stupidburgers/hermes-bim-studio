"""Regression tests for confined output paths (catalog review PR #149221).

Covers: absolute paths, '..' traversal, wrong/missing suffix, path separators,
silent overwrite without overwrite:true, and a legitimate bare-filename write
succeeding. Exercises both the low-level guard and the model-facing handlers.
Each test uses its own throwaway HERMES_HOME, so no writes reach the real home.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from plugin import handle_bim_render_view, handle_bim_takeoff
from plugin.bim_engine import _guard_output_path, _OUTPUT_SUBDIR

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IFC_PATH = os.path.join(ROOT, "samples", "sample_house.ifc")


class TestOutputPathConfinement(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self._old_home = os.environ.get("HERMES_HOME")
        os.environ["HERMES_HOME"] = self.tmp.name
        self.addCleanup(self._restore_home)

    def _restore_home(self):
        if self._old_home is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = self._old_home

    @property
    def root(self):
        return os.path.abspath(os.path.join(self.tmp.name, _OUTPUT_SUBDIR))

    # ---- low-level guard: the four injection classes are rejected ----------
    def test_guard_rejects_absolute_paths(self):
        for name in ("/tmp/evil.html", "/etc/passwd",
                     "C:\\Windows\\evil.html", "C:evil.html",
                     os.path.expanduser("~/.bashrc")):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    _guard_output_path(name, ".html")

    def test_guard_rejects_dotdot_traversal(self):
        for name in ("../evil.html", "..\\evil.html", "sub/../../evil.html", "..html"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    _guard_output_path(name, ".html")

    def test_guard_rejects_wrong_or_missing_suffix(self):
        for name in ("evil.txt", "evil", "evil.html.txt", "report.xlsx"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    _guard_output_path(name, ".html")

    def test_guard_rejects_path_separators(self):
        for name in ("sub/evil.html", "sub\\evil.html", "a/b\\c.html"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    _guard_output_path(name, ".html")

    def test_guard_accepts_legitimate_bare_name_and_confines(self):
        path = _guard_output_path("report.html", ".html")
        self.assertTrue(os.path.isabs(path))
        self.assertEqual(os.path.commonpath([path, self.root]), self.root)
        self.assertTrue(path.endswith("report.html"))
        self.assertTrue(os.path.isdir(self.root))

    # ---- overwrite semantics ------------------------------------------------
    def test_no_silent_overwrite_without_flag(self):
        first = _guard_output_path("same.html", ".html")
        with open(first, "w", encoding="utf-8") as fh:
            fh.write("ORIGINAL")
        second = _guard_output_path("same.html", ".html")  # overwrite omitted
        self.assertNotEqual(first, second)               # timestamped variant
        with open(first, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "ORIGINAL")      # original preserved

    def test_overwrite_true_replaces_same_path(self):
        first = _guard_output_path("over.html", ".html", overwrite=False)
        with open(first, "w", encoding="utf-8") as fh:
            fh.write("OLD")
        again = _guard_output_path("over.html", ".html", overwrite=True)
        self.assertEqual(first, again)                    # explicit opt-in reuses path

    def test_guard_refuses_symlink_target(self):
        os.makedirs(self.root, exist_ok=True)
        outside = os.path.join(self.tmp.name, "outside.html")
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write("SAFE")
        link = os.path.join(self.root, "link.html")
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this platform/account")
        with self.assertRaises(ValueError):
            _guard_output_path("link.html", ".html")

    # ---- end-to-end through the model-facing handlers -----------------------
    def test_handler_blocks_absolute_path_attack(self):
        target = os.path.join(self.tmp.name, "pwned.html")
        resp = handle_bim_render_view({
            "ifc_path": IFC_PATH, "output_html": target, "max_elements": 5,
        })
        self.assertTrue(resp.startswith("Error"), resp)
        self.assertFalse(os.path.exists(target))

    def test_handler_blocks_traversal_attack(self):
        escape = os.path.join(os.path.dirname(self.root), "escape.html")
        resp = handle_bim_render_view({
            "ifc_path": IFC_PATH, "output_html": "../escape.html", "max_elements": 5,
        })
        self.assertTrue(resp.startswith("Error"), resp)
        self.assertFalse(os.path.exists(escape))

    def test_handler_blocks_wrong_suffix(self):
        resp = handle_bim_takeoff({"ifc_path": IFC_PATH, "output_xlsx": "evil.txt"})
        self.assertTrue(resp.startswith("Error"), resp)

    def test_handler_blocks_path_separator(self):
        resp = handle_bim_takeoff({"ifc_path": IFC_PATH, "output_xlsx": "sub/evil.xlsx"})
        self.assertTrue(resp.startswith("Error"), resp)

    def test_handler_legitimate_bare_name_succeeds_and_returns_final_path(self):
        resp = handle_bim_render_view({
            "ifc_path": IFC_PATH, "output_html": "safe.html", "max_elements": 5,
        })
        self.assertFalse(resp.startswith("Error"), resp)
        data = json.loads(resp)
        final = data["output_html"]
        self.assertEqual(os.path.commonpath([final, self.root]), self.root)
        self.assertTrue(os.path.isfile(final))
        self.assertIn("::preview{", data["preview_directive"])


if __name__ == "__main__":
    unittest.main()
