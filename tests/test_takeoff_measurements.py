import json
import os
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.api
import openpyxl

from plugin import handle_bim_takeoff

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IFC_PATH = os.path.join(ROOT, "samples", "sample_house.ifc")
OUTPUT_DIR = os.path.join(ROOT, "docs", "evidence")
RATES = {"masonry_wall_m2": 1, "concrete_slab_m3": 1, "door_unit": 1, "window_unit": 1}


class TestTakeoffMeasurements(unittest.TestCase):
    def test_empty_wall_and_slab_categories_are_complete_zero_quantities(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            source = ifcopenshell.open(IFC_PATH)
            for element in list(source.by_type("IfcWall")) + list(source.by_type("IfcSlab")):
                ifcopenshell.api.run("root.remove_product", source, product=element)
            modified_path = os.path.join(temp_dir, "no-walls-or-slabs.ifc")
            source.write(modified_path)

            raw = handle_bim_takeoff({
                "ifc_path": modified_path,
                "output_xlsx": os.path.join(temp_dir, "takeoff.xlsx"),
                "rates": RATES,
            })
            data = json.loads(raw)
            items = {item["wbs"]: item for item in data["line_items"]}
            for wbs in ("02.01", "01.01"):
                self.assertEqual(items[wbs]["qty"], 0)
                self.assertTrue(items[wbs]["complete"])
                self.assertEqual(items[wbs]["measured_elements"], 0)
                self.assertEqual(items[wbs]["total_elements"], 0)
                self.assertEqual(items[wbs]["total"], 0)
                # Rate must still reflect the supplied/validated rate for audit,
                # even though a zero-quantity category always totals to $0.
                self.assertEqual(items[wbs]["rate"], 1.0)
            self.assertEqual(data["priced_scope_total_usd"], 16.0)

    def test_line_items_are_ordered_by_ascending_wbs_code(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            raw = handle_bim_takeoff({
                "ifc_path": IFC_PATH,
                "output_xlsx": os.path.join(temp_dir, "ordering.xlsx"),
                "rates": RATES,
            })
            data = json.loads(raw)
            wbs_codes = [item["wbs"] for item in data["line_items"]]
            self.assertEqual(wbs_codes, sorted(wbs_codes))
            self.assertEqual(wbs_codes, ["01.01", "02.01", "03.01", "03.02"])

    def test_missing_wall_base_quantity_is_reported_and_not_priced(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            source = ifcopenshell.open(IFC_PATH)
            wall = source.by_type("IfcWall")[0]
            for relation in list(wall.IsDefinedBy):
                definition = getattr(relation, "RelatingPropertyDefinition", None)
                if definition and definition.is_a("IfcElementQuantity") and definition.Name == "BaseQuantities":
                    source.remove(relation)
            modified_path = os.path.join(temp_dir, "missing-wall-qto.ifc")
            source.write(modified_path)

            xlsx_path = os.path.join(temp_dir, "takeoff.xlsx")
            raw = handle_bim_takeoff({
                "ifc_path": modified_path,
                "output_xlsx": xlsx_path,
                "rates": RATES,
            })
            data = json.loads(raw)
            wall_item = next(item for item in data["line_items"] if item["wbs"] == "02.01")
            self.assertEqual((wall_item["measured_elements"], wall_item["total_elements"]), (12, 13))
            self.assertFalse(wall_item["complete"])
            self.assertEqual(len(wall_item["unavailable"]), 1)
            self.assertIsNone(wall_item["total"])
            self.assertIsNone(data["priced_scope_total_usd"])

            workbook = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
            self.assertIn("Unavailable Measurements", workbook.sheetnames)
            rows = list(workbook["Unavailable Measurements"].values)
            unavailable = wall_item["unavailable"][0]
            matches = [row for row in rows[1:] if row[1] == unavailable["element_id"]]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0][0], wall_item["description"])
            self.assertEqual(matches[0][2], unavailable["source"])
            self.assertEqual(matches[0][3], unavailable["reason"])
            workbook.close()

    def test_no_rates_means_no_cost_total(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            raw = handle_bim_takeoff({
                "ifc_path": IFC_PATH,
                "output_xlsx": os.path.join(temp_dir, "unpriced.xlsx"),
            })
            data = json.loads(raw)
            self.assertIsNone(data["priced_scope_total_usd"])
            self.assertEqual(data["pricing_status"], "not_priced_or_incomplete")
            self.assertTrue(all(item["rate"] is None and item["total"] is None for item in data["line_items"]))

    def test_explicit_square_millimetre_quantity_is_converted_to_square_metres(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            source = ifcopenshell.open(IFC_PATH)
            wall = source.by_type("IfcWall")[0]
            quantity = None
            for relation in wall.IsDefinedBy:
                definition = getattr(relation, "RelatingPropertyDefinition", None)
                if definition and definition.is_a("IfcElementQuantity") and definition.Name == "BaseQuantities":
                    quantity = next(q for q in definition.Quantities if q.Name == "NetSideArea")
                    break
            self.assertIsNotNone(quantity)
            quantity.AreaValue *= 1_000_000
            quantity.Unit = source.createIfcSIUnit(None, "AREAUNIT", "MILLI", "SQUARE_METRE")
            modified_path = os.path.join(temp_dir, "square-millimetre-override.ifc")
            source.write(modified_path)

            raw = handle_bim_takeoff({
                "ifc_path": modified_path,
                "output_xlsx": os.path.join(temp_dir, "takeoff.xlsx"),
            })
            data = json.loads(raw)
            wall_item = next(item for item in data["line_items"] if item["wbs"] == "02.01")
            self.assertAlmostEqual(wall_item["qty"], 190.465524, places=6)

    def test_area_unit_on_slab_volume_is_rejected_and_not_priced(self):
        with tempfile.TemporaryDirectory(dir=OUTPUT_DIR) as temp_dir:
            source = ifcopenshell.open(IFC_PATH)
            slab = source.by_type("IfcSlab")[0]
            quantity = None
            for relation in slab.IsDefinedBy:
                definition = getattr(relation, "RelatingPropertyDefinition", None)
                if definition and definition.is_a("IfcElementQuantity") and definition.Name == "BaseQuantities":
                    quantity = next(q for q in definition.Quantities if q.Name == "NetVolume")
                    break
            self.assertIsNotNone(quantity)
            quantity.Unit = source.createIfcSIUnit(None, "AREAUNIT", None, "SQUARE_METRE")
            modified_path = os.path.join(temp_dir, "wrong-volume-unit.ifc")
            source.write(modified_path)

            raw = handle_bim_takeoff({
                "ifc_path": modified_path,
                "output_xlsx": os.path.join(temp_dir, "takeoff.xlsx"),
                "rates": RATES,
            })
            data = json.loads(raw)
            slab_item = next(item for item in data["line_items"] if item["wbs"] == "01.01")
            self.assertEqual((slab_item["measured_elements"], slab_item["total_elements"]), (3, 4))
            self.assertFalse(slab_item["complete"])
            self.assertIn("expected a VOLUMEUNIT unit", slab_item["unavailable"][0]["reason"])
            self.assertIsNone(slab_item["total"])
            self.assertIsNone(data["priced_scope_total_usd"])


if __name__ == "__main__":
    unittest.main()
