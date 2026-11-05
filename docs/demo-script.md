# 85-Second Demo Video Script for Twitter/X

**Target:** <= 90 seconds (Per Nous Research rules: "Keep the demo under 90 seconds and show the plugin working").
**Format:** Screen recording of Hermes Desktop with voiceover or upbeat tech music + callout captions.

---

### Scene 1: The Pitch (0:00 - 0:12)
- **Screen:** Hermes Desktop in clean dark mode.
- **Caption / Voiceover:** *"What if your AI agent wasn't just a chatbot, but a full-stack BIM Engineer? Meet Hermes BIM Studio."*
- **Action:** User drags and drops `FAICALVILLE_128m2.ifc` into the chat with the prompt:  
  `Hermes, inspect this building model, run a deterministic 5D quantity takeoff, and render the interactive 3D model.`

### Scene 2: Semantic BIM Ingestion & Compliance (0:12 - 0:32)
- **Screen:** Hermes invokes `bim_inspect`.
- **Output card appears:**
  - Project: `Residencial Faicalville (128.22 m²)`
  - Architecture: 109 walls, 88 slabs, 22 doors, 10 windows, 24 roof sections.
  - Compliance Engine: 8 uncontained spatial elements detected and flagged.
- **Caption:** *"Instant boundary-representation parsing using ifcopenshell — zero hallucinations, 100% deterministic spatial audit."*

### Scene 3: Deterministic 5D Takeoff & Excel Audit Trail (0:32 - 0:52)
- **Screen:** Hermes invokes `bim_takeoff`.
- **Action:** An executive 5D takeoff card appears showing Grand Total: `$117,119.50`.
- **Action:** Clicks to preview or open the generated `takeoff_5d.xlsx`. Shows the formatted Excel workbook with WBS codes, concrete volumes ($m^3$), masonry surface area ($m^2$), unit rates, and the cryptographic SHA-256 model provenance tab.
- **Caption:** *"Generates an auditable 5D construction budget with SHA-256 model fingerprinting in seconds."*

### Scene 4: Live 3D WebGL Building Inspection (0:52 - 1:18)
- **Screen:** Hermes invokes `bim_render_view` returning `::preview{file="viewer.html"}`.
- **Action:** The Hermes Desktop preview pane slides open with the full 3D interactive building model!
- **Action:** Cursor smoothly orbits around the house in 3D, zooms into the patio slab, clicks a structural wall — element inspector pops up showing ID `#2589`, Type `IfcWall`, dimensions, and highlights it in radiant orange.
- **Caption:** *"Full Three.js WebGL orbit controls, element inspection, and storey isolation right inside Hermes Desktop."*

### Scene 5: Call to Action & Catalog Listing (1:18 - 1:25)
- **Screen:** Quick flash of the open PR on NousResearch/hermes-agent and GitHub repo `stupidburgers/hermes-bim-studio`.
- **Caption / Voiceover:** *"Hermes BIM Studio: Bringing AEC engineering to open-source autonomous agents. Install via Hermes Marketplace today. Built for the Nous Research Plugin Hackathon."*
