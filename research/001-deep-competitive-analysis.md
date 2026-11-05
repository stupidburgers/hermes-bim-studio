# Deep Competitive Analysis & Product Strategy for Winning the Hermes Hackathon

**Date:** 2026-11-04  
**Author:** Lead Coordinator & Specialist Panel  
**Target Account:** `stupidburgers`  
**Hackathon:** Nous Research Hermes Agent Plugin Hackathon (Deadline Nov 11, 2026, 5PM EST, $20,000 cash prizes)

---

## 1. Executive Summary & Verdict

To win 1st place in the Hermes Hackathon, an entry must maximize: **Usefulness**, **Reliability**, **Polish**, and **Creativity**, while showing judges a capability that **"does more than a prompt or a skill could"** with a captivating **<=90-second demo on X**.

We evaluated three contenders across all formal scoring dimensions, competition saturation in the Hermes Plugin Catalog, technical feasibility on Windows, and demo appeal:

1. **Pinpoint (Accessibility Auditor / DOM Inspector)**: Ongoing baseline project in `C:/Users/<user>/projects/hermes-plugin-hackathon`. High risk of category fatigue; perceived by judges as a wrapper around existing tools (axe-core/pa11y) that a standard coding agent or skill could largely perform via CLI.
2. **Parametric CAD Studio (Text-to-CAD / build123d / OpenCASCADE)**: Strong visual appeal, but faces competition from PR #136214 (port of `earthtojake/text-to-cad` skills into Nous optional-skills) and PR #149127 (`Rigforge` machine studio), plus complex CAD constraint solver edge cases.
3. **Hermes BIM Studio / ConstructIQ (BIM Ingestion, 3D Building Inspection & 5D Quantity Takeoff)**: **CLEAR WINNER**. Addresses the multi-trillion dollar Architecture, Engineering & Construction (AEC) industry. Zero competition in the catalog or open PRs. Computes deterministic physical quantities ($m^3, m^2$) from 3D IFC models, detects building code violations, generates auditable 5D cost workbooks, and pops up an interactive 3D WebGL building model right in Hermes Desktop preview.

---

## 2. Head-to-Head Scoring Matrix

| Criteria | Weight | Pinpoint (Accessibility) | Parametric CAD Studio | Hermes BIM Studio (Construtech) |
| :--- | :---: | :---: | :---: | :---: |
| **Category Novelty & Open Competition** | 20% | 4/10 (Crowded space; linters common) | 7/10 (PR #136214 & Rigforge #149127 exist) | **10/10 (0 BIM/IFC plugins in catalog or PRs)** |
| **"Does more than prompt/skill"** | 25% | 5/10 (Prompts + CLI linters do similar) | 9/10 (Solid modeling engine) | **10/10 (Full BRep geometry, spatial hierarchy, QTO)** |
| **Demo "Wow" Factor (<=90s on X)** | 25% | 6/10 (DOM text change, color contrast fix) | 8/10 (3D part rendering) | **10/10 (Real 3D house orbit, cost takeoff, clash glow)** |
| **Reliability & Local Windows Execution** | 15% | 8/10 (Playwright/Chrome dependency) | 6/10 (CAD solver failures/slow compilation) | **9.5/10 (ifcopenshell 0.9.0 pre-installed, <1.1s load)** |
| **Real-World Value & Commercial Impact** | 15% | 7/10 (General web devs) | 7/10 (Makers/3D printing hobbyists) | **10/10 (Global AEC industry standard, mandated BIM)** |
| **Total Weighted Score** | **100%** | **5.75 / 10** | **7.60 / 10** | **9.85 / 10** |

---

## 3. Why Construtech (Hermes BIM Studio) Is the Winning Strategy

### A. Uncontested Territory
A census of the 977 Hermes plugin catalog records and 196+ open pull requests reveals:
- CAD / 3D printing has `print3d` (macOS/Linux only, broken on Windows) and `photo-to-part`.
- `teknium1` (Nous founder) personally ported `earthtojake/text-to-cad` skills in PR #136214.
- **Zero BIM, IFC, or construction engineering plugins exist.** A polished BIM plugin stands completely alone in its category, instantly catching the attention of Nous maintainers and judges.

### B. Alignment with Starred Repositories & Local Assets
- User's starred repos include `earthtojake/text-to-cad` (3D viewer and CAD generation concepts) and `pbakaus/impeccable` (high-polish UI).
- The local machine ALREADY has `residential-3br-128m2.ifc` (a complete real-world residential architectural and structural model) in `C:/Users/<user>/projects/quantity-takeoff`.
- Python 3.11 with `ifcopenshell 0.9.0.post1` is already installed and verified to parse 109 walls and 88 slabs with 3D world geometry in **1.096 seconds**!

### C. The 85-Second Demo Arc on X
- **0:00 - 0:15**: Drop `house-model.ifc` into chat: *"Hermes, audit this building: check spatial enclosures, calculate concrete and masonry quantities, and show me the 3D model."*
- **0:15 - 0:35**: Hermes executes `bim_inspect` and `bim_takeoff`. Detects 109 walls ($342.5 m^2$), 88 slabs ($128.2 m^2$ footprint, $15.4 m^3$ concrete). Highlights 2 missing room volume closures and unassociated lintels.
- **0:35 - 0:55**: Hermes generates `budget-5d.xlsx` with deterministic unit prices and an immutable cryptographic SHA-256 audit block, ready for download.
- **0:55 - 0:85**: Hermes triggers the embedded Three.js 3D Viewer right in the Desktop preview pane (`::preview{file="model_view.html"}`). The user orbits the 3D house, isolates the ground floor, clicks on a structural wall to see its dimensions and computed cost, and turns on the audit filter to see flagged issues highlighted in radiant orange.
- **Total Runtime**: ~80 seconds. Pure magic, polished, verifiable, and visually unforgettable.
