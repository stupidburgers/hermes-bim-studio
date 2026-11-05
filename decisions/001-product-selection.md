# Decision 001: Product Selection & Hackathon Strategy

**Status:** APPROVED FOR BUILD  
**Date:** 2026-11-04  
**Product Name:** Hermes BIM Studio (`hermes-bim-studio`)  
**Target Account:** `stupidburgers`  
**Hackathon:** Nous Research Hermes Agent Plugin Hackathon (Nov 11, 2026, 5PM EST)

---

## 1. Context & User Directive
The user requested a deep, unbiased search and analysis to identify a winning plugin for the Nous Research hackathon, granting 100% autonomy and specifically noting:
*"I am already running one option we brainstormed in another session, called pinpoint. BUT i want to make a really winning plugin. Do a deep search, deep analysis, deep think, it should be something made for winning this hackaton... Maybe we can build some construtech plugin like we were brainstorming before."*

## 2. Decision
We formally select and initiate development of **Hermes BIM Studio**: an open-source Building Information Modeling (BIM) inspector, compliance auditor, 5D quantity takeoff engine, and embedded 3D WebGL viewer for Hermes Desktop.

We deliberately de-prioritize building a second accessibility linter (Pinpoint), which faces severe category saturation, low novelty, and high risk of being judged as "just a prompt or CLI skill wrapper".

## 3. Justification & Verification Evidence
1. **Category Novelty (10/10):** A verified audit of all 977 catalog entries and 196+ open pull requests in `NousResearch/hermes-agent` confirmed **0 BIM or IFC plugins exist**. While 3D printing (`print3d`) exists for macOS/Linux (broken on Windows), professional AEC engineering is 100% unrepresented.
2. **Beyond Prompt/Skill Boundary (10/10):** The hackathon guidelines explicitly state that judges favor plugins that do *more than a prompt or skill could*. BIM Studio uses native `ifcopenshell` to parse complex BRep geometry, spatial containment hierarchies, compute deterministic volume/area quantities, and generate an interactive Three.js 3D viewer. A prompt or skill cannot do this.
3. **Proven Feasibility on Windows (9.5/10):** Executed spike `spikes/ifc_inspector_spike.py` verified that Python 3.11 with `ifcopenshell 0.9.0.post1` loaded a real 16MB building model (`residential-3br-128m2.ifc`) in **1.42 seconds**, audited 109 walls and 88 slabs, computed a 5D cost breakdown ($92,639.50), and exported a self-contained 266KB interactive 3D WebGL viewer.
4. **85-Second Demo Arc:** Designed specifically for Twitter/X video format, transitioning from natural language command to 3D orbit controls, clash highlights, and an audit-stamped XLSX workbook.

## 4. Immediate Roadmap (Nov 5 - Nov 10)
- **Day 1 (Nov 5):** Package core plugin manifest (`plugin.yaml`), register tools `bim_inspect`, `bim_takeoff`, `bim_render_view`.
- **Day 2 (Nov 6):** Refine deterministic QTO formula calculations (slabs, columns, walls) and XLSX export with openpyxl.
- **Day 3 (Nov 7):** Polish Three.js 3D viewer template (materials, colors, wireframes, click-to-inspect overlay, Hermes theme variables).
- **Day 4 (Nov 8):** End-to-end integration with Hermes Desktop preview pane (`::preview{file="..."}`) and `hermes plugins validate` pass.
- **Day 5 (Nov 9):** Record the <=85-second demo video, upload to X, create `plugin-catalog/hermes-bim-studio.yaml` PR against NousResearch/hermes-agent, and submit Typeform.
