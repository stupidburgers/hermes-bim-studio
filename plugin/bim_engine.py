import os
import sys
import json
import math
import time
import hashlib
import html as html_lib
from datetime import datetime
from typing import Any, Dict, List, Optional

import ifcopenshell
import ifcopenshell.geom as geom
import ifcopenshell.util.element as ifc_element_util
import ifcopenshell.util.unit as ifc_unit_util
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

MAX_RENDER_ELEMENTS = 150

# --- Confined output paths (catalog review PR #149221, teknium1) ------------
# Every generated file is confined to this subdirectory of the active Hermes
# home. Model-supplied output names are treated as BARE FILE NAMES only; they
# can never escape this directory. This mirrors the documented plugin data dir
# `<HERMES_HOME>/plugin-data/<name>/` (see plugin_data_dir()).
_OUTPUT_SUBDIR = os.path.join("plugin-data", "hermes-bim-studio")


def _resolve_hermes_home() -> str:
    """Return the absolute active HERMES_HOME used for confined output files.

    Resolution order:
      1. The documented ``HERMES_HOME`` environment variable (Configuration
         docs resolve ``Path(os.environ["HERMES_HOME"])``). Hermes sets this
         per-process to the active profile home, and it keeps standalone runs
         (tests, `hermes plugins doctor`) deterministic.
      2. ``get_hermes_home()`` from ``hermes_constants`` -- the exact helper the
         catalog reviewer named. It is a real, import-safe, stdlib-only symbol
         in Hermes core (hermes_constants.py), but it is a CORE INTERNAL, not a
         documented plugin-SDK import. It is therefore used only behind a
         guarded lazy import, never a hard import, so this module stays
         importable when Hermes is not installed.
      3. The documented default home, ``~/.hermes``.
    """
    env_home = os.environ.get("HERMES_HOME")
    if env_home:
        return os.path.abspath(os.path.expanduser(env_home))
    try:
        from hermes_constants import get_hermes_home  # core internal; guarded
        return os.path.abspath(os.path.expanduser(str(get_hermes_home())))
    except Exception:
        pass
    return os.path.abspath(os.path.expanduser("~/.hermes"))


def _guard_output_path(name: Optional[str], suffix: str, overwrite: bool = False) -> str:
    """Validate a model-supplied output name and resolve it to a confined path.

    ``name`` is treated as a BARE FILE NAME only. Absolute paths, drive letters,
    path separators and ``..`` are rejected before anything is written. The
    required ``.html``/``.xlsx`` suffix is enforced. The final path is always
    under ``<HERMES_HOME>/plugin-data/hermes-bim-studio/``. Existing files are
    never silently replaced: without ``overwrite=True`` a timestamped variant
    is used instead. Returns the final absolute path.
    """
    if not name:
        name = "bim_viewer_3d.html" if suffix == ".html" else "bim_takeoff_5d.xlsx"
    if not isinstance(name, str):
        raise ValueError("output name must be a string")
    if name in ("", ".", ".."):
        raise ValueError("output name must be a bare file name")
    if "/" in name or "\\" in name or os.sep in name or (os.altsep and os.altsep in name):
        raise ValueError("output name must be a bare file name: path separators are not allowed")
    if ".." in name:
        raise ValueError("output name must be a bare file name: '..' is not allowed")
    if os.path.isabs(name) or (len(name) >= 2 and name[0].isalpha() and name[1] == ":"):
        raise ValueError("output name must be a bare file name: absolute paths / drive letters are not allowed")
    if any(ord(ch) < 32 for ch in name) or "\x00" in name:
        raise ValueError("output name contains control characters")
    if not name.lower().endswith(suffix):
        raise ValueError(f"output name must end with {suffix!r}")

    root = os.path.abspath(os.path.join(_resolve_hermes_home(), _OUTPUT_SUBDIR))
    final = os.path.abspath(os.path.join(root, name))
    # Defense in depth: even after validation the resolved path stays inside root.
    if os.path.commonpath([final, root]) != root:
        raise ValueError("resolved output path escapes the plugin data directory")
    os.makedirs(root, exist_ok=True)
    if os.path.islink(final):
        raise ValueError("refusing to write to a symbolic link")
    if os.path.exists(final) and not overwrite:
        stem, ext = os.path.splitext(name)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        candidate = os.path.join(root, f"{stem}-{stamp}{ext}")
        n = 1
        while os.path.exists(candidate) or os.path.islink(candidate):
            candidate = os.path.join(root, f"{stem}-{stamp}-{n}{ext}")
            n += 1
        final = candidate
    return final

def compute_sha256(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

_GEOM_SETTINGS = None

def _geom_settings():
    """Shared world-coordinate tessellation settings (lazy singleton)."""
    global _GEOM_SETTINGS
    if _GEOM_SETTINGS is None:
        s = geom.settings()
        s.set(s.USE_WORLD_COORDS, True)
        _GEOM_SETTINGS = s
    return _GEOM_SETTINGS

def _tessellate(elem):
    """Triangulate one IFC element -> (verts, faces) in world coordinates."""
    shape = geom.create_shape(_geom_settings(), elem)
    return shape.geometry.verts, shape.geometry.faces

def _mesh_measurements(verts, faces) -> tuple:
    """Exact volume (signed tetrahedron sum) and exact envelope surface area
    of a closed triangulated mesh. Deterministic: same mesh -> same numbers."""
    volume = 0.0
    area = 0.0
    for i in range(0, len(faces) - 2, 3):
        i0, i1, i2 = faces[i] * 3, faces[i + 1] * 3, faces[i + 2] * 3
        x0, y0, z0 = verts[i0], verts[i0 + 1], verts[i0 + 2]
        x1, y1, z1 = verts[i1], verts[i1 + 1], verts[i1 + 2]
        x2, y2, z2 = verts[i2], verts[i2 + 1], verts[i2 + 2]
        volume += (x0 * (y1 * z2 - z1 * y2)
                   - y0 * (x1 * z2 - z1 * x2)
                   + z0 * (x1 * y2 - y1 * x2)) / 6.0
        ax, ay, az = x1 - x0, y1 - y0, z1 - z0
        bx, by, bz = x2 - x0, y2 - y0, z2 - z0
        cx, cy, cz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
        area += 0.5 * (cx * cx + cy * cy + cz * cz) ** 0.5
    return abs(volume), area

def _measure_elements(elements) -> tuple:
    """Tessellate a list of IFC elements.
    Returns (measured, failures): measured = [(elem, volume_m3, envelope_area_m2)]."""
    measured = []
    failures = 0
    for elem in elements:
        try:
            verts, faces = _tessellate(elem)
            if not verts or not faces:
                failures += 1
                continue
            vol, area = _mesh_measurements(verts, faces)
            measured.append((elem, vol, area))
        except Exception:
            failures += 1
    return measured, failures

def _load_vendor_js() -> tuple:
    """Load the vendored Three.js runtime so generated viewers are fully
    self-contained (no CDN, works offline and inside sandboxed previews)."""
    vendor_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
    three_path = os.path.join(vendor_dir, "three.min.js")
    orbit_path = os.path.join(vendor_dir, "OrbitControls.js")
    if not (os.path.exists(three_path) and os.path.exists(orbit_path)):
        raise FileNotFoundError(
            f"Vendored Three.js runtime missing under {vendor_dir} — plugin install is incomplete."
        )
    with open(three_path, encoding="utf-8") as fh:
        three_js = fh.read()
    with open(orbit_path, encoding="utf-8") as fh:
        orbit_js = fh.read()
    return three_js, orbit_js


def _json_for_inline_script(value: Any) -> str:
    """Serialize values safely inside an HTML script element."""
    serialized = json.dumps(value, ensure_ascii=True)
    return (serialized
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026"))


def _excel_literal(value: Any) -> Any:
    """Keep untrusted text from being interpreted as an Excel formula."""
    if isinstance(value, str) and value.lstrip(" \t\r\n")[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value

def inspect_bim_model(ifc_path: str) -> Dict[str, Any]:
    if not os.path.exists(ifc_path):
        raise FileNotFoundError(f"IFC file not found: {ifc_path}")
        
    t0 = time.time()
    sha = compute_sha256(ifc_path)
    f = ifcopenshell.open(ifc_path)
    load_time = round(time.time() - t0, 3)
    
    proj_name = "Unnamed Project"
    projects = f.by_type("IfcProject")
    if projects and projects[0].Name:
        proj_name = projects[0].Name
        
    schema = f.schema
    
    storeys = f.by_type("IfcBuildingStorey")
    spaces = f.by_type("IfcSpace")
    walls = f.by_type("IfcWall")
    slabs = f.by_type("IfcSlab")
    doors = f.by_type("IfcDoor")
    windows = f.by_type("IfcWindow")
    columns = f.by_type("IfcColumn")
    beams = f.by_type("IfcBeam")
    roofs = f.by_type("IfcRoof")
    
    findings = []
    
    # Check 1: Spatial Containment
    uncontained = []
    for elem in walls + slabs + doors + windows + columns + beams:
        has_container = False
        for rel in getattr(elem, "ContainedInStructure", []):
            if rel.is_a("IfcRelContainedInSpatialStructure"):
                has_container = True
                break
        if not has_container:
            uncontained.append(elem.id())
            
    if uncontained:
        findings.append({
            "code": "WARN_UNCONTAINED_SPATIAL",
            "severity": "WARNING",
            "message": f"{len(uncontained)} elements lack explicit spatial container (IfcRelContainedInSpatialStructure)",
            "sample_ids": uncontained[:5]
        })
        
    # Check 2: Element naming
    unnamed = [e.id() for e in (walls + slabs) if not e.Name]
    if unnamed:
        findings.append({
            "code": "INFO_UNNAMED_ELEMENTS",
            "severity": "INFO",
            "message": f"{len(unnamed)} architectural elements lack descriptive names.",
            "sample_ids": unnamed[:5]
        })
        
    return {
        "project_name": proj_name,
        "schema": schema,
        "file_size_bytes": os.path.getsize(ifc_path),
        "sha256": sha,
        "load_time_sec": load_time,
        "inventory": {
            "storeys": len(storeys),
            "spaces": len(spaces),
            "walls": len(walls),
            "slabs": len(slabs),
            "doors": len(doors),
            "windows": len(windows),
            "columns": len(columns),
            "beams": len(beams),
            "roofs": len(roofs)
        },
        "findings": findings
    }

def _read_base_quantity_si(elem, qto_name: str, quantity_name: str, expected_class: str, ifc_file):
    """Read one named IFC base quantity and convert it to SI.

    Returns (value, source, reason). Missing, ambiguous, unsupported, or
    unitless quantities are unavailable; this helper never guesses a value.
    """
    matches = []
    for relation in getattr(elem, "IsDefinedBy", []):
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        qto = relation.RelatingPropertyDefinition
        if not qto.is_a("IfcElementQuantity") or qto.Name != qto_name:
            continue
        matches.extend(q for q in (qto.Quantities or []) if q.Name == quantity_name)

    source = f"{qto_name}.{quantity_name}"
    if not matches:
        return None, source, "quantity not provided"
    if len(matches) != 1:
        return None, source, "quantity is ambiguous"

    quantity = matches[0]
    if not quantity.is_a(expected_class):
        return None, source, f"expected {expected_class}, got {quantity.is_a()}"

    try:
        unit = ifc_unit_util.get_property_unit(quantity, ifc_file)
    except Exception as exc:
        return None, source, f"unit lookup failed: {exc}"
    if unit is None:
        return None, source, "quantity has no explicit or project unit"
    expected_unit_type = {"IfcQuantityArea": "AREAUNIT", "IfcQuantityVolume": "VOLUMEUNIT"}.get(expected_class)
    if expected_unit_type and getattr(unit, "UnitType", None) != expected_unit_type:
        return None, source, f"expected a {expected_unit_type} unit"

    value_attribute = {
        "IfcQuantityLength": "LengthValue",
        "IfcQuantityArea": "AreaValue",
        "IfcQuantityVolume": "VolumeValue",
    }[expected_class]
    value = getattr(quantity, value_attribute, None)
    if value is None:
        return None, source, "quantity value is empty"
    try:
        si_value = float(value) * ifc_unit_util.get_unit_scale(unit)
    except (TypeError, ValueError, RuntimeError) as exc:
        return None, source, f"unit conversion failed: {exc}"
    if not math.isfinite(si_value) or si_value < 0:
        return None, source, "quantity value is not finite and non-negative"

    symbol = ifc_unit_util.get_unit_symbol(unit) or "unknown unit"
    return si_value, source, f"converted from {symbol} to SI"


def _validated_rate(rates, key):
    if not rates or key not in rates or rates[key] is None:
        return None
    rate = float(rates[key])
    if not math.isfinite(rate) or rate < 0:
        raise ValueError(f"Rate {key!r} must be a finite non-negative number")
    return rate


def _line_total(quantity, rates, key):
    rate = _validated_rate(rates, key)
    return round(quantity * rate, 2) if rate is not None else None


def generate_5d_takeoff(
    ifc_path: str,
    rates: Optional[Dict[str, float]] = None,
    output_xlsx: Optional[str] = None,
    overwrite: bool = False
) -> Dict[str, Any]:
    if not os.path.exists(ifc_path):
        raise FileNotFoundError(f"IFC file not found: {ifc_path}")
    # Resolve the (model-supplied) output name to a confined path BEFORE any
    # work or write. A workbook is always written (see the tool schema).
    final_xlsx = _guard_output_path(output_xlsx, ".xlsx", overwrite=overwrite)
        
    info = inspect_bim_model(ifc_path)
    f = ifcopenshell.open(ifc_path)
    
    walls = f.by_type("IfcWall")
    slabs = f.by_type("IfcSlab")
    doors = f.by_type("IfcDoor")
    windows = f.by_type("IfcWindow")

    def measured_line_item(elements, qto_name, quantity_name, quantity_class, description, unit, rate_key):
        if not elements:
            # An empty IFC category has an explicitly known zero quantity, not missing data.
            # Still require and surface the supplied rate so listed-scope pricing is complete.
            rate = _validated_rate(rates, rate_key)
            return {
                "description": description,
                "qty": 0,
                "unit": unit,
                "source": "IFC entity scope (0 matching elements)",
                "measured_elements": 0,
                "total_elements": 0,
                "complete": True,
                "unavailable": [],
                "rate": rate,
                "total": 0.0 if rate is not None else None,
            }
        values = []
        failures = []
        for elem in elements:
            value, source, reason = _read_base_quantity_si(
                elem, qto_name, quantity_name, quantity_class, f
            )
            if value is None:
                failures.append({"element_id": elem.id(), "source": source, "reason": reason})
            else:
                values.append(value)
        if not values:
            return {
                "description": description,
                "qty": None,
                "unit": unit,
                "source": f"{qto_name}.{quantity_name}",
                "measured_elements": 0,
                "total_elements": len(elements),
                "complete": False,
                "unavailable": failures,
                "rate": None,
                "total": None,
            }
        qty = round(sum(values), 6)
        rate = rates.get(rate_key) if rates else None
        if rate is not None and (not math.isfinite(float(rate)) or float(rate) < 0):
            raise ValueError(f"Rate {rate_key!r} must be a finite non-negative number")
        complete = len(values) == len(elements)
        return {
            "description": description,
            "qty": qty,
            "unit": unit,
            "source": f"{qto_name}.{quantity_name}; {failures[0]['reason']}" if failures else f"{qto_name}.{quantity_name}",
            "measured_elements": len(values),
            "total_elements": len(elements),
            "complete": complete,
            "unavailable": failures,
            "rate": float(rate) if rate is not None else None,
            "total": round(qty * float(rate), 2) if rate is not None and complete else None,
        }

    line_items = [
        {
            "wbs": "01.01",
            "description": "Slabs — net volume",
            **measured_line_item(
                slabs, "BaseQuantities", "NetVolume", "IfcQuantityVolume",
                "Slabs — net volume", "m³", "concrete_slab_m3",
            ),
        },
        {
            "wbs": "02.01",
            "description": "Walls — net side area",
            **measured_line_item(
                walls, "BaseQuantities", "NetSideArea", "IfcQuantityArea",
                "Walls — net side area", "m²", "masonry_wall_m2",
            ),
        },
        {
            "wbs": "03.01",
            "description": "Doors",
            "qty": len(doors),
            "unit": "units",
            "source": "IFC entity count (IfcDoor)",
            "measured_elements": len(doors),
            "total_elements": len(doors),
            "complete": True,
            "unavailable": [],
            "rate": _validated_rate(rates, "door_unit"),
            "total": _line_total(len(doors), rates, "door_unit"),
        },
        {
            "wbs": "03.02",
            "description": "Windows",
            "qty": len(windows),
            "unit": "units",
            "source": "IFC entity count (IfcWindow)",
            "measured_elements": len(windows),
            "total_elements": len(windows),
            "complete": True,
            "unavailable": [],
            "rate": _validated_rate(rates, "window_unit"),
            "total": _line_total(len(windows), rates, "window_unit"),
        },
    ]
    pricing_scope = [
        {"description": item["description"], "source": item["source"]}
        for item in line_items
    ]

    # Price only the four explicitly listed categories; this is not a whole-project estimate.
    total_is_complete = all(item["complete"] and item["total"] is not None for item in line_items)
    scope_total = round(sum(item["total"] for item in line_items), 2) if total_is_complete else None
    
    # Build professionally styled Excel workbook
    wb = openpyxl.Workbook()
    
    # Sheet 1: Executive Summary
    ws_summary = wb.active
    ws_summary.title = "Executive Summary"
    ws_summary.views.sheetView[0].showGridLines = True
    
    header_fill = PatternFill(start_color="1A1B26", end_color="1A1B26", fill_type="solid")
    accent_fill = PatternFill(start_color="2AC3DE", end_color="2AC3DE", fill_type="solid")
    card_fill = PatternFill(start_color="24283B", end_color="24283B", fill_type="solid")
    
    title_font = Font(name="Segoe UI", size=16, bold=True, color="FFFFFF")
    subtitle_font = Font(name="Segoe UI", size=11, italic=True, color="A9B1D6")
    card_header_font = Font(name="Segoe UI", size=11, bold=True, color="7AA2F7")
    card_val_font = Font(name="Segoe UI", size=14, bold=True, color="E0AF68")
    card_total_font = Font(name="Segoe UI", size=16, bold=True, color="9ECE6A")
    
    # Title row
    ws_summary.merge_cells("A1:E2")
    t_cell = ws_summary["A1"]
    t_cell.value = _excel_literal(f"Hermes BIM Studio — IFC Quantity Report: {info['project_name']}")
    t_cell.fill = header_fill
    t_cell.font = title_font
    t_cell.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    
    ws_summary["A3"] = "Listed-scope total (4 categories only):"
    ws_summary["A3"].font = card_header_font
    ws_summary["B3"] = f"${scope_total:,.2f}" if scope_total is not None else "Not calculated — enter complete rates"
    ws_summary["B3"].font = card_total_font
    
    ws_summary["A4"] = "IFC Model SHA-256:"
    ws_summary["A4"].font = card_header_font
    ws_summary["B4"] = info["sha256"]
    ws_summary["B4"].font = subtitle_font
    
    # Table Headers
    headers = ["WBS Code", "Item Description", "Quantity", "Unit", "Unit Rate ($, user supplied)", "Subtotal ($)", "Source / Coverage"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws_summary.cell(row=6, column=col_idx, value=h)
        cell.fill = card_fill
        cell.font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 3, 4] else "left")
        
    for r_idx, item in enumerate(line_items, 7):
        ws_summary.cell(row=r_idx, column=1, value=item["wbs"]).alignment = Alignment(horizontal="center")
        ws_summary.cell(row=r_idx, column=2, value=item["description"])
        ws_summary.cell(row=r_idx, column=3, value=item["qty"]).number_format = "#,##0.000000"
        ws_summary.cell(row=r_idx, column=4, value=item["unit"]).alignment = Alignment(horizontal="center")
        rate_cell = ws_summary.cell(row=r_idx, column=5, value=item["rate"])
        rate_cell.number_format = "$#,##0.00"
        total_cell = ws_summary.cell(row=r_idx, column=6, value=item["total"])
        total_cell.number_format = "$#,##0.00"
        coverage = f"{item['measured_elements']}/{item['total_elements']} complete; {item['source']}"
        if item["unavailable"]:
            coverage += f"; {len(item['unavailable'])} unavailable"
        ws_summary.cell(row=r_idx, column=7, value=coverage)
        
    tot_row = len(line_items) + 7
    ws_summary.cell(row=tot_row, column=2, value="LISTED-SCOPE TOTAL — 4 categories only; user-supplied rates").font = Font(name="Segoe UI", size=12, bold=True)
    tot_cell = ws_summary.cell(row=tot_row, column=6, value=scope_total)
    if scope_total is None:
        ws_summary.cell(row=tot_row, column=2, value="LISTED-SCOPE TOTAL NOT CALCULATED — add complete quantities and user-supplied rates")
    tot_cell.font = card_total_font
    tot_cell.number_format = "$#,##0.00"
    
    # Adjust column widths
    for col in ws_summary.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws_summary.column_dimensions[col_letter].width = max(max_len + 4, 14)
        
    # Sheet 2: Audit Trail
    ws_audit = wb.create_sheet(title="Audit & Provenance")
    ws_audit.views.sheetView[0].showGridLines = True
    
    audit_rows = [
        ("File Path", ifc_path),
        ("Source Model SHA-256", info["sha256"]),
        ("IFC Schema", info["schema"]),
        ("Quantity Basis", "BaseQuantities.NetSideArea / NetVolume; door/window entity counts"),
        ("Pricing Scope", "; ".join(f"{item['description']} [{item['source']}]" for item in pricing_scope)),
        ("Pricing", "User-supplied rates only; no default rate assumptions"),
        ("Quantity Coverage", "; ".join(f"{item['description']}: {item['measured_elements']}/{item['total_elements']}" for item in line_items)),
        ("Price Total Status", "complete for the four listed categories only" if scope_total is not None else "not calculated; missing rates or quantities; four listed categories only"),
        ("File Size (Bytes)", str(info["file_size_bytes"])),
        ("Engine Version", "Hermes BIM Studio v0.1.0 (ifcopenshell 0.9.0)"),
        ("Generated At", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())),
        ("Model Findings", str(len(info["findings"])))
    ]
    
    ws_audit.cell(row=1, column=1, value="Audit Record Parameter").font = card_header_font
    ws_audit.cell(row=1, column=2, value="Value").font = card_header_font
    
    for r_idx, (k, v) in enumerate(audit_rows, 2):
        ws_audit.cell(row=r_idx, column=1, value=k).font = Font(name="Segoe UI", bold=True)
        ws_audit.cell(row=r_idx, column=2, value=_excel_literal(v)).font = Font(name="Segoe UI")
        
    ws_audit.column_dimensions["A"].width = 25
    ws_audit.column_dimensions["B"].width = 65

    ws_unavailable = wb.create_sheet(title="Unavailable Measurements")
    unavailable_headers = ["Category", "Element ID", "Quantity Source", "Unavailable Reason"]
    for col_idx, header in enumerate(unavailable_headers, 1):
        cell = ws_unavailable.cell(row=1, column=col_idx, value=header)
        cell.fill = card_fill
        cell.font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    unavailable_row = 2
    for item in line_items:
        for record in item["unavailable"]:
            values = (item["description"], record["element_id"], record["source"], record["reason"])
            for col_idx, value in enumerate(values, 1):
                ws_unavailable.cell(row=unavailable_row, column=col_idx, value=_excel_literal(value))
            unavailable_row += 1
    if unavailable_row == 2:
        ws_unavailable.cell(row=2, column=1, value="No unavailable measurements")
    for column, width in (("A", 30), ("B", 14), ("C", 36), ("D", 60)):
        ws_unavailable.column_dimensions[column].width = width
    
    wb.save(final_xlsx)
    
    return {
        "project_name": info["project_name"],
        "pricing_scope": pricing_scope,
        "priced_scope_total_usd": scope_total,
        "pricing_status": "complete_for_listed_scope" if scope_total is not None else "not_priced_or_incomplete",
        "line_items_count": len(line_items),
        "line_items": line_items,
        "output_xlsx": final_xlsx,
        "source_model_sha256": info["sha256"]
    }

def render_3d_viewer(
    ifc_path: str,
    output_html: Optional[str] = None,
    max_elements: int = 150,
    overwrite: bool = False
) -> Dict[str, Any]:
    if type(max_elements) is not int or not 0 <= max_elements <= MAX_RENDER_ELEMENTS:
        raise ValueError(f"max_elements must be between 0 and {MAX_RENDER_ELEMENTS}")
    if not os.path.exists(ifc_path):
        raise FileNotFoundError(f"IFC file not found: {ifc_path}")
    # Resolve the (model-supplied) output name to a confined path BEFORE any
    # work or write. A viewer HTML file is always written (see the tool schema).
    final_html = _guard_output_path(output_html, ".html", overwrite=overwrite)
        
    info = inspect_bim_model(ifc_path)
    f = ifcopenshell.open(ifc_path)
    
    walls = f.by_type("IfcWall")
    slabs = f.by_type("IfcSlab")
    doors = f.by_type("IfcDoor")
    windows = f.by_type("IfcWindow")
    columns = f.by_type("IfcColumn")
    roofs = f.by_type("IfcRoof")
    
    settings = geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    
    meshes = []
    selected = (
        walls[:60] + slabs[:30] + doors[:20] + windows[:20] + columns[:10] + roofs[:10]
    )[:max_elements]
    
    for elem in selected:
        try:
            shape = geom.create_shape(settings, elem)
            verts = shape.geometry.verts
            faces = shape.geometry.faces
            
            category = elem.is_a()
            color = "#78909c"
            opacity = 1.0
            if category == "IfcWall":
                color = "#cfd8dc"
            elif category == "IfcSlab":
                color = "#90a4ae"
            elif category == "IfcDoor":
                color = "#8d6e63"
            elif category == "IfcWindow":
                color = "#4fc3f7"
                opacity = 0.65
            elif category == "IfcRoof":
                color = "#b0bec5"
            elif category == "IfcColumn":
                color = "#546e7a"
                
            meshes.append({
                "id": elem.id(),
                "name": elem.Name or f"{category}_{elem.id()}",
                "type": category,
                "color": color,
                "opacity": opacity,
                "vertices": [round(v, 3) for v in verts],
                "faces": list(faces)
            })
        except Exception:
            continue
            
    three_js, orbit_js = _load_vendor_js()
    project_name_html = html_lib.escape(str(info["project_name"]), quote=True)
    meshes_data_json = _json_for_inline_script(meshes)
    html_template = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
<title>Hermes BIM Studio — 3D Viewer</title>
<style>
  body {{ margin: 0; overflow: hidden; background: #13141f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #c0caf5; }}
  #viewport {{ width: 100vw; height: 100vh; display: block; }}
  #overlay {{ position: absolute; top: 16px; left: 16px; background: rgba(26, 27, 38, 0.92); border: 1px solid #414868; border-radius: 8px; padding: 14px 18px; max-width: 320px; backdrop-filter: blur(10px); box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
  h2 {{ margin: 0 0 8px 0; font-size: 15px; color: #7aa2f7; display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
  .brand {{ white-space: nowrap; }}
  .badge {{ flex-shrink: 0; background: #2ac3de; color: #13141f; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; white-space: nowrap; }}
  .stat {{ display: flex; justify-content: space-between; font-size: 12px; margin: 4px 0; }}
  .stat-label {{ color: #7982a9; }}
  .stat-val {{ font-weight: 600; color: #e0af68; }}
  #info-panel {{ position: absolute; top: 16px; right: 16px; background: rgba(26, 27, 38, 0.9); border: 1px solid #414868; border-radius: 8px; padding: 12px 16px; display: none; font-size: 12px; max-width: 260px; }}
  #info-panel h3 {{ margin: 0 0 6px 0; font-size: 13px; color: #9ece6a; }}
  #hint {{ position: absolute; bottom: 16px; left: 16px; font-size: 11px; color: #565f89; background: rgba(26, 27, 38, 0.6); padding: 6px 10px; border-radius: 4px; }}
</style>
<script>{three_js}</script>
<script>{orbit_js}</script>
</head>
<body>
<div id=\"overlay\">
  <h2><span class=\"brand\">Hermes BIM Studio</span><span class=\"badge\">IFC 3D</span></h2>
  <div class=\"stat\"><span class=\"stat-label\">Project:</span> <span class=\"stat-val\">{project_name_html}</span></div>
  <div class=\"stat"><span class=\"stat-label\">Walls / Slabs:</span> <span class=\"stat-val\">{len(walls)} / {len(slabs)}</span></div>
  <div class=\"stat"><span class=\"stat-label\">Doors / Windows:</span> <span class=\"stat-val\">{len(doors)} / {len(windows)}</span></div>
  <div class=\"stat"><span class=\"stat-label\">Rendered Meshes:</span> <span class=\"stat-val\">{len(meshes)}</span></div>
</div>

<div id=\"info-panel\">
  <h3 id=\"elem-title\">Element Info</h3>
  <div class=\"stat"><span class=\"stat-label\">Type:</span> <span id=\"elem-type\" class=\"stat-val\"></span></div>
  <div class=\"stat"><span class=\"stat-label\">ID:</span> <span id=\"elem-id\" class=\"stat-val\"></span></div>
</div>

<div id=\"hint\">Rotate: Left Drag | Pan: Right Drag | Inspect: Left Click Element</div>
<div id=\"viewport\"></div>

<script>
  const meshesData = {meshes_data_json};
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x13141f);
  
  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
  camera.position.set(24, 18, 28);
  
  const renderer = new THREE.WebGLRenderer({{ antialias: true }});
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  document.getElementById('viewport').appendChild(renderer.domElement);
  
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
  scene.add(ambientLight);
  
  const sunLight = new THREE.DirectionalLight(0xffffff, 0.85);
  sunLight.position.set(30, 50, 30);
  scene.add(sunLight);
  
  const fillLight = new THREE.DirectionalLight(0x7aa2f7, 0.35);
  fillLight.position.set(-30, -20, -30);
  scene.add(fillLight);
  
  const grid = new THREE.GridHelper(50, 50, 0x414868, 0x24283b);
  grid.position.y = -0.01;
  scene.add(grid);
  
  const rootGroup = new THREE.Group();
  scene.add(rootGroup);
  const clickable = [];
  
  meshesData.forEach(m => {{
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.BufferAttribute(new Float32Array(m.vertices), 3));
    geom.setIndex(new THREE.BufferAttribute(new Uint32Array(m.faces), 1));
    geom.computeVertexNormals();
    
    const mat = new THREE.MeshStandardMaterial({{
      color: new THREE.Color(m.color),
      roughness: 0.35,
      metalness: 0.1,
      transparent: m.opacity < 1.0,
      opacity: m.opacity,
      side: THREE.DoubleSide
    }});
    
    const mesh = new THREE.Mesh(geom, mat);
    mesh.userData = {{ id: m.id, name: m.name, type: m.type }};
    rootGroup.add(mesh);
    clickable.push(mesh);
  }});
  
  const box = new THREE.Box3().setFromObject(rootGroup);
  const center = box.getCenter(new THREE.Vector3());
  rootGroup.position.sub(center);
  
  // Raycaster for element clicking
  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  let lastSelected = null;
  let origColor = null;
  
  window.addEventListener('click', (e) => {{
    mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    
    raycaster.setFromCamera(mouse, camera);
    const hits = raycaster.intersectObjects(clickable);
    
    if (hits.length > 0) {{
      const obj = hits[0].object;
      if (lastSelected && origColor) {{
        lastSelected.material.color.set(origColor);
      }}
      lastSelected = obj;
      origColor = obj.material.color.getHex();
      obj.material.color.set(0xff9e64); // highlight orange
      
      document.getElementById('info-panel').style.display = 'block';
      document.getElementById('elem-title').innerText = obj.userData.name;
      document.getElementById('elem-type').innerText = obj.userData.type;
      document.getElementById('elem-id').innerText = '#' + obj.userData.id;
    }}
  }});
  
  window.addEventListener('resize', () => {{
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }});
  
  function animate() {{
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }}
  animate();
</script>
</body>
</html>"""
    
    with open(final_html, "w", encoding="utf-8") as out:
        out.write(html_template)
        
    return {
        "output_html": final_html,
        "rendered_meshes": len(meshes),
        "preview_directive": f"::preview{{file=\"{final_html}\"}}"
    }
