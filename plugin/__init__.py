"""Hermes BIM Studio — AI-powered Building Information Modeling (BIM) & 5D Cost Takeoff."""
from __future__ import annotations

import json
from typing import Any, Dict

from .bim_engine import inspect_bim_model, generate_5d_takeoff, render_3d_viewer


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
    try:
        result = generate_5d_takeoff(ifc_path, rates=rates, output_xlsx=output_xlsx)
        return json.dumps(result, indent=2)
    except Exception as exc:
        return f"Error generating 5D takeoff: {exc}"


def handle_bim_render_view(args: Dict[str, Any], **kwargs: Any) -> str:
    ifc_path = args.get("ifc_path", "")
    if not ifc_path:
        return "Error: 'ifc_path' parameter is required."
    output_html = args.get("output_html")
    max_elements = int(args.get("max_elements", 150))
    try:
        result = render_3d_viewer(ifc_path, output_html=output_html, max_elements=max_elements)
        return json.dumps(result, indent=2)
    except Exception as exc:
        return f"Error generating 3D view: {exc}"


BIM_INSPECT_SCHEMA = {
    "name": "bim_inspect",
    "description": (
        "Inspect an IFC (Industry Foundation Classes) Building Information Model. "
        "Extracts project metadata, building storeys, spaces, architectural and "
        "structural element counts (walls, slabs, doors, windows, columns, beams, roofs), "
        "and runs deterministic compliance checks (spatial containment, uncontained elements)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_path": {
                "type": "string",
                "description": "Absolute or relative path to the .ifc building model file.",
            },
        },
        "required": ["ifc_path"],
    },
}

BIM_TAKEOFF_SCHEMA = {
    "name": "bim_takeoff",
    "description": (
        "Generate a deterministic 5D Quantity Takeoff (QTO) and construction cost "
        "estimate from an IFC model. Calculates physical quantities (wall areas m², "
        "concrete volumes m³, element counts), applies unit rates, and produces a "
        "professionally styled Excel spreadsheet (.xlsx) with an immutable cryptographic "
        "audit trail."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_path": {
                "type": "string",
                "description": "Path to the .ifc building model file.",
            },
            "rates": {
                "type": "object",
                "description": "Optional custom unit rates (e.g. {'concrete_slab_m3': 450.0, 'masonry_wall_m2': 70.0}).",
            },
            "output_xlsx": {
                "type": "string",
                "description": "Optional path to save the generated .xlsx workbook.",
            },
        },
        "required": ["ifc_path"],
    },
}

BIM_RENDER_VIEW_SCHEMA = {
    "name": "bim_render_view",
    "description": (
        "Generate an interactive 3D WebGL Building Information Model viewer "
        "from an IFC file. Produces a self-contained HTML page using Three.js with "
        "orbit controls, directional lighting, storey isolation, and element click inspection. "
        "Returns the preview directive ::preview{file=\"path.html\"} to display the 3D model "
        "directly in the Hermes Desktop preview pane."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "ifc_path": {
                "type": "string",
                "description": "Path to the .ifc building model file.",
            },
            "output_html": {
                "type": "string",
                "description": "Optional path to save the generated viewer HTML file.",
            },
            "max_elements": {
                "type": "integer",
                "description": "Max number of 3D mesh elements to render for fast real-time interaction (default: 150).",
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
