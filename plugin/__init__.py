"""Hermes BIM Studio — IFC model inspection and listed-scope quantity reporting."""
from __future__ import annotations

import json
from typing import Any, Dict

from .bim_engine import MAX_RENDER_ELEMENTS, inspect_bim_model, generate_5d_takeoff, render_3d_viewer


def handle_bim_inspect(args: Dict[str, Any], **kwargs: Any) -> str:
    ifc_path = args.get("ifc_path", "")
    if not ifc_path:
        return "Error: 'ifc_path' parameter is required."
    try:
        result = inspect_bim_model(ifc_path)
        return json.dumps(result, indent=2)
    except Exception as exc:
        return f"Error inspecting BIM model: {exc}"


def handle_bim_takeoff(args: Dict[str, Any], **kwargs: Any) -> str:
    ifc_path = args.get("ifc_path", "")
    if not ifc_path:
        return "Error: 'ifc_path' parameter is required."
    rates = args.get("rates")
    output_xlsx = args.get("output_xlsx")
    overwrite = bool(args.get("overwrite", False))
    try:
        result = generate_5d_takeoff(ifc_path, rates=rates, output_xlsx=output_xlsx, overwrite=overwrite)
        return json.dumps(result, indent=2)
    except Exception as exc:
        return f"Error generating 5D takeoff: {exc}"


def handle_bim_render_view(args: Dict[str, Any], **kwargs: Any) -> str:
    ifc_path = args.get("ifc_path", "")
    if not ifc_path:
        return "Error: 'ifc_path' parameter is required."
    output_html = args.get("output_html")
    max_elements = args.get("max_elements", MAX_RENDER_ELEMENTS)
    overwrite = bool(args.get("overwrite", False))
    try:
        result = render_3d_viewer(ifc_path, output_html=output_html, max_elements=max_elements, overwrite=overwrite)
        return json.dumps(result, indent=2)
    except Exception as exc:
        return f"Error generating 3D view: {exc}"


BIM_INSPECT_SCHEMA = {
    "name": "bim_inspect",
    "description": (
        "Inspect an IFC (Industry Foundation Classes) Building Information Model. "
        "Extracts project metadata, storeys, spaces, and architectural/structural element counts. "
        "Runs basic model-quality checks for spatial containment and unnamed elements; "
        "these checks are not building-code or regulatory compliance certification."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_path": {
                "type": "string",
                "description": "Path to the .ifc model. Relative paths resolve against the session working directory, not the gateway process directory.",
            },
        },
        "required": ["ifc_path"],
    },
}

BIM_TAKEOFF_SCHEMA = {
    "name": "bim_takeoff",
    "description": (
        "Create an IFC quantity report from IFC BaseQuantities: NetSideArea for walls and "
        "NetVolume for slabs, converted using the IFC quantity/project unit. Reports per-element "
        "coverage and missing quantities rather than guessing. Door/window values are IFC entity "
        "counts. Optional caller-supplied USD rates produce a total for these four listed categories "
        "only when every item has complete quantities and a supplied rate; this is not a whole-project "
        "estimate, professional bid, or quantity-surveying certification."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_path": {
                "type": "string",
                "description": "Path to the .ifc model. Relative paths resolve against the session working directory, not the gateway process directory.",
            },
            "rates": {
                "type": "object",
                "description": "Optional caller-supplied USD unit rates: masonry_wall_m2, concrete_slab_m3, door_unit, window_unit. A total covers only these four listed categories, not the whole project. Missing rates leave the corresponding total blank; no default prices are applied.",
            },
            "output_xlsx": {
                "type": "string",
                "description": "A workbook is ALWAYS written. Give a bare file name ending in .xlsx (no directories, no '..', no absolute paths); it is saved under <HERMES_HOME>/plugin-data/hermes-bim-studio/. If omitted, a default name is used. An existing file is never silently overwritten: a timestamp is added, or set overwrite=true to replace it. The final absolute path is returned.",
            },
            "overwrite": {
                "type": "boolean",
                "description": "Allow replacing an existing file at the chosen name. Default false; without it a timestamped variant is written instead of overwriting.",
            },
        },
        "required": ["ifc_path"],
    },
}

BIM_RENDER_VIEW_SCHEMA = {
    "name": "bim_render_view",
    "description": (
        "Generate a self-contained interactive WebGL 3D view of selected IFC elements "
        "using vendored Three.js assets (no network request). IFC Z-up geometry is "
        "converted once to the viewer's Y-up scene so floors stay horizontal. "
        "Supports orbit around the vertical axis, zoom, and click-to-inspect element identity."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_path": {
                "type": "string",
                "description": "Path to the .ifc model. Relative paths resolve against the session working directory, not the gateway process directory.",
            },
            "output_html": {
                "type": "string",
                "description": "A viewer HTML file is ALWAYS written. Give a bare file name ending in .html (no directories, no '..', no absolute paths); it is saved under <HERMES_HOME>/plugin-data/hermes-bim-studio/. If omitted, a default name is used. An existing file is never silently overwritten: a timestamp is added, or set overwrite=true to replace it. The final absolute path is returned.",
            },
            "overwrite": {
                "type": "boolean",
                "description": "Allow replacing an existing file at the chosen name. Default false; without it a timestamped variant is written instead of overwriting.",
            },
            "max_elements": {
                "type": "integer",
                "description": f"Max number of 3D mesh elements to render (0 to {MAX_RENDER_ELEMENTS}; default: {MAX_RENDER_ELEMENTS}).",
                "minimum": 0,
                "maximum": MAX_RENDER_ELEMENTS,
            },
        },
        "required": ["ifc_path"],
    },
}


def register(ctx) -> None:
    """Register Hermes BIM Studio tools."""
    ctx.register_tool(
        name="bim_inspect",
        toolset="hermes-bim-studio",
        schema=BIM_INSPECT_SCHEMA,
        handler=handle_bim_inspect,
    )
    ctx.register_tool(
        name="bim_takeoff",
        toolset="hermes-bim-studio",
        schema=BIM_TAKEOFF_SCHEMA,
        handler=handle_bim_takeoff,
    )
    ctx.register_tool(
        name="bim_render_view",
        toolset="hermes-bim-studio",
        schema=BIM_RENDER_VIEW_SCHEMA,
        handler=handle_bim_render_view,
    )
