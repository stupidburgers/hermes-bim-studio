# Technical Architecture — Hermes BIM Studio

**Date:** 2026-11-04  
**Author:** Lead Architect & DevOps  
**Target Repository:** `stupidburgers/hermes-bim-studio`  

---

## 1. Plugin Packaging & Manifest Specification

The plugin strictly adheres to the Hermes Plugin Developer Guide and Catalog Admission Rules:

```yaml
# plugin.yaml
name: hermes-bim-studio
title: Hermes BIM Studio
version: "0.1.0"
description: "Open-source Building Information Modeling (BIM) inspector, 5D quantity takeoff engine, and interactive 3D WebGL viewer for construction engineering."
maintainer: stupidburgers
category: engineering
requires_hermes: ">=0.22.0"
python_dependencies:
  - ifcopenshell>=0.9.0
  - openpyxl>=3.1.2

capabilities:
  provides_tools:
    - bim_inspect
    - bim_takeoff
    - bim_render_view
  provides_hooks: []
  provides_middleware: []
  requires_env: []
```

---
## 2. Core Agent Tools

### Tool 1: `bim_inspect(ifc_path: str, checks: list[str] = None) -> dict`
- Ingests an IFC file (`.ifc`).
- Extracts spatial decomposition: `IfcProject` -> `IfcSite` -> `IfcBuilding` -> `IfcBuildingStorey` -> `IfcSpace`.
- Catalogs physical elements: Walls, Slabs, Beams, Columns, Doors, Windows, Roofs, Stairs, Coverings, MEP services.
- Executes deterministic compliance checks:
  * Spatial enclosure containment: verifies elements belong to a declared storey.
  * Geometric consistency: detects zero-volume or unmeshed elements.
  * PropertySet verification: checks if standard property sets (`Pset_WallCommon`, `Pset_SlabCommon`) are populated.
  * Material definitions: identifies elements with missing materials or unassigned classifications.

### Tool 2: `bim_takeoff(ifc_path: str, unit_prices: dict = None, output_xlsx: str = None) -> dict`
- Computes exact geometric physical quantities using `ifcopenshell.geom` BRep evaluation and base quantities (`IfcElementQuantity`):
  * Wall gross & net surface area ($m^2$)
  * Structural concrete volume for slabs, beams, columns ($m^3$)
  * Masonry volume ($m^3$)
  * Floor finish area ($m^2$)
  * Door & window counts by type / dimension
- Maps quantities to standard unit rates or custom cost dictionaries.
- Exports an auditable spreadsheet (`takeoff_5d.xlsx`) containing:
  * Summary executive dashboard sheet.
  * Detailed elemental itemization sheet.
  * Audit sheet (SHA-256 of IFC file, tool version, calculation log, timestamp).

### Tool 3: `bim_render_view(ifc_path: str, highlight_elements: list[str] = None, output_html: str = None) -> str`
- Converts the IFC model into an optimized lightweight JSON/Three.js scene buffer.
- Generates a standalone self-contained HTML page embedding Three.js (via CDN or bundled) with OrbitControls, directional lighting, section plane slider, element click inspector, and visual clash/audit highlighting.
- Outputs the file path and registers the directive `::preview{file="..."}` so Hermes Desktop renders the live interactive 3D model right in the chat panel!

---
## 3. Admission Rules Compliance Checklist

- **Rule 1 & 2:** Public repo on GitHub under `stupidburgers`, exact 40-character SHA pinned in `plugin-catalog/hermes-bim-studio.yaml`.
- **Rule 6:** Declared capabilities (`bim_inspect`, `bim_takeoff`, `bim_render_view`) match exact Python registrations.
- **Rule 8 & 9:** Public surfaces only. No monkeypatching of Hermes core, no runtime overrides, no prototype pollution.
- **Rule 11:** 100% local calculation; no secrets, no API keys, no network exfiltration.
- **Rule 17:** Zero committed native binaries or .exe files. `ifcopenshell` installs purely as a standard wheel via uv/pip.
