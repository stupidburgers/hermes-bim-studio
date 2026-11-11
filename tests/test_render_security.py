import json
import os
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.geom as geom

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
            source.write(modified_path)

            response = json.loads(handle_bim_render_view({
                "ifc_path": modified_path,
                "output_html": "viewer.html",
                "max_elements": 10,
            }))
            self.assertTrue(os.path.exists(response["output_html"]))
            with open(response["output_html"], encoding="utf-8") as viewer_file:
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

    def test_exported_geometry_converts_ifc_z_up_to_y_up(self):
        """IFC world coordinates are Z-up. Exported viewer vertices must be Y-up."""
        settings = geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        ifc = ifcopenshell.open(IFC_PATH)
        wall = next(elem for elem in ifc.by_type("IfcWall") if elem.id() == 21966)
        raw = geom.create_shape(settings, wall).geometry.verts
        raw_y = [raw[i] for i in range(1, len(raw), 3)]
        raw_z = [raw[i] for i in range(2, len(raw), 3)]

        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as hermes_home:
            previous = os.environ.get("HERMES_HOME")
            os.environ["HERMES_HOME"] = hermes_home
            try:
                response = json.loads(handle_bim_render_view({
                    "ifc_path": IFC_PATH,
                    "output_html": "up-axis.html",
                    "max_elements": 120,
                    "overwrite": True,
                }))
            finally:
                if previous is None:
                    os.environ.pop("HERMES_HOME", None)
                else:
                    os.environ["HERMES_HOME"] = previous
            output_path = response["output_html"]
            data_root = os.path.realpath(os.path.join(
                hermes_home, "plugin-data", "hermes-bim-studio"
            ))
            self.assertEqual(os.path.commonpath([os.path.realpath(output_path), data_root]), data_root)
            with open(output_path, encoding="utf-8") as viewer_file:
                html = viewer_file.read()

        self.assertNotIn("https://cdn.", html)
        self.assertIn("camera.up.set(0, 1, 0)", html)
        self.assertIn("screenSpacePanning = false", html)
        self.assertIn("GridHelper", html)
        self.assertNotIn("rootGroup.rotation", html)
        marker = "const meshesData = "
        start = html.index(marker) + len(marker)
        meshes = json.loads(html[start:html.index(";\n", start)])
        exported = next(mesh for mesh in meshes if mesh["id"] == 21966)
        self.assertEqual(exported["name"], "Wand-Ext-ERDG-1")
        self.assertEqual(exported["type"], "IfcWallStandardCase")

        xs = exported["vertices"][0::3]
        ys = exported["vertices"][1::3]
        zs = exported["vertices"][2::3]
        self.assertAlmostEqual(max(ys) - min(ys), max(raw_z) - min(raw_z), places=2)
        self.assertAlmostEqual(max(zs) - min(zs), max(raw_y) - min(raw_y), places=2)
        self.assertAlmostEqual(min(ys), round(min(raw_z), 3), places=3)
        self.assertAlmostEqual(max(ys), round(max(raw_z), 3), places=3)
        self.assertAlmostEqual(min(zs), round(-max(raw_y), 3), places=3)
        self.assertAlmostEqual(max(zs), round(-min(raw_y), 3), places=3)
        self.assertGreater(max(ys) - min(ys), max(xs) - min(xs))

        spans = _axis_spans(meshes)
        self.assertLess(spans[1], spans[0])
        self.assertLess(spans[1], spans[2])
        self.assertGreater(spans[1], 5.0)
        self.assertLess(spans[1], 8.0)


def _axis_spans(meshes):
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    for mesh in meshes:
        verts = mesh["vertices"]
        for index in range(0, len(verts), 3):
            for axis in range(3):
                mins[axis] = min(mins[axis], verts[index + axis])
                maxs[axis] = max(maxs[axis], verts[index + axis])
    return [maxs[axis] - mins[axis] for axis in range(3)]


if __name__ == "__main__":
    unittest.main()
