# Hermes BIM Studio

Building Information Modeling (BIM) inspection, deterministic 5D quantity takeoff, and interactive 3D WebGL building model viewer for Hermes Agent — built for AEC (architecture, engineering, construction) workflows.

## Features

- **Semantic BIM ingestion** — parses IFC2x3, IFC4, and IFC4X3 building models natively via `ifcopenshell`. No external APIs or vendor subscriptions.
- **Deterministic quantity takeoff (QTO)** — computes physical quantities (wall gross/net areas m², slab and structural concrete volumes m³, beam lengths, door/window counts) with real 3D geometry calculations, zero LLM involvement.
- **Model & compliance auditing** — flags spatial anomalies: uncontained elements, missing property sets, zero-volume geometry.
- **5D cost estimation** — maps quantities to unit-rate tables and produces styled, auditable Excel (.xlsx) budget workbooks with a SHA-256 audit trail.
- **Embedded 3D BIM viewer** — generates a self-contained Three.js HTML visualization with orbit controls, element click inspection, and storey isolation, displayed in the Hermes Desktop preview pane via `::preview{file="..."}`.

## Tools

| Tool | Purpose |
| --- | --- |
| `bim_inspect` | Inspect an IFC model: project metadata, storeys, spaces, element counts, compliance checks. |
| `bim_takeoff` | Generate a deterministic 5D QTO + cost estimate as an .xlsx workbook (custom unit rates supported). |
| `bim_render_view` | Render an interactive 3D WebGL viewer of the IFC model (self-contained HTML). |

## Requirements

- Hermes Agent `>=0.22.0`
- Python dependencies (installed automatically by Hermes from this declaration):
  `ifcopenshell>=0.9.0,<0.10`, `openpyxl>=3.1.2,<4`
- No environment variables, API keys, or network access required — runs fully local.

## Usage

Provide a path to any IFC2x3/IFC4 model (`.ifc`) to any of the three tools. A sample model ships in the repository at `samples/sample_house.ifc`.

```
bim_takeoff(ifc_path="samples/sample_house.ifc")
```

## License

MIT — see repository root for source, tests, and hackathon evidence.
