# Hermes BIM Studio (ConstructIQ)

[![CI](https://github.com/stupidburgers/hermes-bim-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/stupidburgers/hermes-bim-studio/actions/workflows/ci.yml)

**The premier BIM, 3D Building Inspection, and 5D Quantity Takeoff Plugin for Hermes Agent.**

Built for the **Hermes Agent Plugin Hackathon** (Nous Research, Nov 2026, $20,000 cash prizes).
Owner: `stupidburgers`

---

## What It Does

Hermes BIM Studio transforms Hermes Agent into an AI-powered Construction Engineer and BIM Auditor:
1. **Semantic BIM Ingestion:** Directly parses standard IFC2x3, IFC4, and IFC4X3 building models using native `ifcopenshell`.
2. **Deterministic Quantity Takeoff (QTO):** Computes exact physical quantities (wall gross/net areas $m^2$, slab and structural concrete volumes $m^3$, beam lengths, door/window counts) using real 3D geometry calculations — zero LLM hallucination.
3. **Model & Compliance Auditing:** Checks for spatial anomalies (uncontained elements, missing property sets, zero-volume geometry, code compliance rule violations).
4. **5D Cost Estimation:** Mappings to unit cost composition tables to produce auditable, professional budget workbooks (.xlsx) with SHA-256 cryptographic audit trails.
5. **Embedded 3D BIM Viewer:** Generates interactive Three.js 3D building visualizations directly inside the Hermes Desktop preview pane (`::preview{file="..."}`), featuring full orbit controls, element inspection, storey isolation, and visual clash/audit highlighting.

---

## Competitive Edge & Hackathon Fit

- **Zero Catalog Saturation:** 0 BIM or IFC plugins exist in the catalog or open PRs.
- **Beyond Prompts & Skills:** Employs geometric boundary-representation engines and WebGL rendering that no prompt or basic skill can duplicate.
- **85-Second Video Punch:** Delivers a complete user journey from raw IFC drop to 3D interactive orbit and verified 5D cost spreadsheet.
- **100% Local & Reliable:** Runs purely on Python on Windows, no external API keys or vendor subscriptions required.
