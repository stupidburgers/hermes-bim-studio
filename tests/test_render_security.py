import json
import os
import tempfile
import unittest

import ifcopenshell

from plugin import handle_bim_render_view
from plugin.bim_engine import _excel_literal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IFC_PATH = os.path.join(ROOT, "samples", "sample_house.ifc")
OUTPUT_DIR = os.path.join(ROOT, "docs", "evidence")


class TestViewerEscaping(unittest.TestCase):
    def test_ifc_names_cannot_break_html_or_script_context(self):
        payload = "</script><script>window.__ifc_xss = true</script>"
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            source = ifcopenshell.open(IFC_PATH)
            source.by_type("IfcProject")[0].Name = payload
            source.by_type("IfcWall")[0].Name = payload
            modified_path = os.path.join(temp_dir, "unsafe-name.ifc")
            output_path = os.path.join(temp_dir, "viewer.html")
            source.write(modified_path)

            response = json.loads(handle_bim_render_view({
                "ifc_path": modified_path,
                "output_html": output_path,
                "max_elements": 10,
            }))
            self.assertTrue(os.path.exists(response["output_html"]))
            with open(output_path, encoding="utf-8") as viewer_file:
                html = viewer_file.read()

            self.assertNotIn(payload, html)
            self.assertIn("&lt;/script&gt;&lt;script&gt;window.__ifc_xss = true&lt;/script&gt;", html)
            self.assertIn(r"\u003c/script\u003e\u003cscript\u003ewindow.__ifc_xss = true\u003c/script\u003e", html)

    def test_render_limit_rejects_values_outside_supported_range(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            for limit in (-1, 151):
                with self.subTest(limit=limit):
                    output_path = os.path.join(temp_dir, f"viewer-{limit}.html")
                    response = handle_bim_render_view({
                        "ifc_path": IFC_PATH,
                        "output_html": output_path,
                        "max_elements": limit,
                    })
                    self.assertIn("max_elements must be between 0 and 150", response)
                    self.assertFalse(os.path.exists(output_path))

    def test_excel_formula_like_text_is_neutralized(self):
        self.assertEqual(_excel_literal("=1+1"), "'=1+1")
        self.assertEqual(_excel_literal("  =1+1"), "'  =1+1")
        self.assertEqual(_excel_literal(42), 42)


if __name__ == "__main__":
    unittest.main()
