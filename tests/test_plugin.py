import os
import sys
import json
import unittest
import tempfile
import ifcopenshell
import openpyxl

# Add plugin directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugin import handle_bim_inspect, handle_bim_takeoff, handle_bim_render_view

SAMPLE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'samples', 'sample_house.ifc'))
IFC_SAMPLE_PATH = SAMPLE_PATH
TEST_OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'docs', 'evidence'))

class TestHermesBimStudioPlugin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
    def test_01_bim_inspect(self):
        raw_res = handle_bim_inspect({"ifc_path": IFC_SAMPLE_PATH})
        self.assertFalse(raw_res.startswith("Error"), f"Inspect failed: {raw_res}")
        data = json.loads(raw_res)
        self.assertIn("project_name", data)
        self.assertIn(data["schema"], ["IFC4", "IFC2X3"])
        self.assertGreater(data["inventory"]["walls"], 0)
        self.assertGreater(data["inventory"]["slabs"], 0)
        self.assertEqual(len(data["sha256"]), 64)
        print(f"[PASS] test_01_bim_inspect passed with {data['schema']} model ({data['inventory']['walls']} walls, {data['inventory']['slabs']} slabs)")

    def test_02_bim_takeoff(self):
        xlsx_path = os.path.join(TEST_OUTPUT_DIR, "test_takeoff.xlsx")
        raw_res = handle_bim_takeoff({
            "ifc_path": IFC_SAMPLE_PATH,
            "output_xlsx": xlsx_path,
            "rates": {
                "masonry_wall_m2": 1.0,
                "concrete_slab_m3": 2.0,
                "door_unit": 3.0,
                "window_unit": 4.0,
            },
        })
        self.assertFalse(raw_res.startswith("Error"), f"Takeoff failed: {raw_res}")
        data = json.loads(raw_res)
        quantities = {item["wbs"]: item["qty"] for item in data["line_items"]}
        self.assertAlmostEqual(quantities["02.01"], 190.465524, places=6)
        self.assertAlmostEqual(quantities["01.01"], 76.99159, places=5)
        self.assertEqual(len(data["pricing_scope"]), 4)
        self.assertEqual(data["pricing_status"], "complete_for_listed_scope")
        self.assertGreater(data["priced_scope_total_usd"], 0)
        self.assertTrue(os.path.exists(xlsx_path))
        self.assertGreater(os.path.getsize(xlsx_path), 5000)
        workbook = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        summary = workbook["Executive Summary"]
        self.assertIn("4 categories only", summary["A3"].value)
        self.assertIn("LISTED-SCOPE TOTAL", summary["B11"].value)
        self.assertIn("four listed categories only", workbook["Audit & Provenance"]["B9"].value)
        workbook.close()
        print(f"[PASS] test_02_bim_takeoff passed (Listed-scope total: ${data['priced_scope_total_usd']:,.2f}, File size: {os.path.getsize(xlsx_path)} bytes)")

    def test_03_bim_render_view(self):
        html_path = os.path.join(TEST_OUTPUT_DIR, "test_viewer.html")
        raw_res = handle_bim_render_view({
            "ifc_path": IFC_SAMPLE_PATH,
            "output_html": html_path,
            "max_elements": 120
        })
        self.assertFalse(raw_res.startswith("Error"), f"Render view failed: {raw_res}")
        data = json.loads(raw_res)
        self.assertTrue(os.path.exists(html_path))
        with open(html_path, encoding="utf-8") as viewer_file:
            html = viewer_file.read()
        self.assertNotIn("https://cdn.", html)
        self.assertIn("THREE.OrbitControls", html)
        self.assertGreater(data["rendered_meshes"], 10)
        self.assertIn("::preview{", data["preview_directive"])
        print(f"[PASS] test_03_bim_render_view passed ({data['rendered_meshes']} meshes rendered, HTML size: {os.path.getsize(html_path)} bytes)")

if __name__ == '__main__':
    unittest.main()
