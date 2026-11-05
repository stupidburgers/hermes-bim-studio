import os
import sys
import json
import unittest

# Add plugin directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugin import handle_bim_inspect, handle_bim_takeoff, handle_bim_render_view

IFC_SAMPLE_PATH = os.path.expanduser("~/projects/quantity-takeoff/residential-3br-128m2.ifc")
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
        self.assertEqual(data["schema"], "IFC2X3")
        self.assertEqual(data["inventory"]["walls"], 109)
        self.assertEqual(data["inventory"]["slabs"], 88)
        self.assertTrue(len(data["sha256"]) == 64)
        print("✓ test_01_bim_inspect passed")

    def test_02_bim_takeoff(self):
        xlsx_path = os.path.join(TEST_OUTPUT_DIR, "test_takeoff.xlsx")
        raw_res = handle_bim_takeoff({
            "ifc_path": IFC_SAMPLE_PATH,
            "output_xlsx": xlsx_path
        })
        self.assertFalse(raw_res.startswith("Error"), f"Takeoff failed: {raw_res}")
        data = json.loads(raw_res)
        self.assertGreater(data["grand_total_usd"], 0)
        self.assertTrue(os.path.exists(xlsx_path))
        self.assertGreater(os.path.getsize(xlsx_path), 5000)
        print(f"✓ test_02_bim_takeoff passed (Total: ${data['grand_total_usd']:,.2f}, File size: {os.path.getsize(xlsx_path)} bytes)")

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
        self.assertGreater(data["rendered_meshes"], 50)
        self.assertIn("::preview{", data["preview_directive"])
        print(f"✓ test_03_bim_render_view passed ({data['rendered_meshes']} meshes rendered, HTML size: {os.path.getsize(html_path)} bytes)")

if __name__ == '__main__':
    unittest.main()
