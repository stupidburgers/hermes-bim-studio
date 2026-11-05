# 80-Second Demo Script — Hermes BIM Studio

**Target:** 80–85 seconds (keep the published cut under 90 seconds).
**Demo data:** `samples/sample_house.ifc` (IFC4, project `Projekt-FZK-Haus`).
**Pricing disclaimer:** rates in this demo are illustrative inputs, not market prices or a construction quote.

## 0:00–0:12 — The problem

- **Screen:** Hermes Desktop with `sample_house.ifc` ready.
- **Voiceover:** “An agent shouldn’t make up building quantities from a drawing it can’t reliably measure. This plugin reads the IFC’s own quantity records and shows what is—and isn’t—covered.”
- **Prompt:** “Inspect this IFC model, report wall and slab quantities with source and coverage, create a quantity workbook using these illustrative USD rates, then open the model in 3D.”

## 0:12–0:28 — Inspect the actual model

- **Screen:** `bim_inspect` result for the bundled fixture.
- **Show:** IFC4 schema, project name, and element counts from the live output.
- **Voiceover:** “Hermes parses the actual IFC locally. These are model contents, not guessed from text.”

## 0:28–0:49 — Quantity report with explicit provenance

- **Screen:** `bim_takeoff` result and workbook. Pass rates: wall `70 USD/m²`, slab `480 USD/m³`, door `250 USD/unit`, window `320 USD/unit`.
- **Show:** wall `BaseQuantities.NetSideArea` = `190.465524 m²`; slab `BaseQuantities.NetVolume` = `76.991590 m³`; door/window entity counts; source and coverage columns.
- **Show:** illustrative listed-scope total `$55,058.55` for walls, slabs, doors, and windows only, labelled as arithmetic on the caller’s sample rates—not a whole-project estimate, bid, certified takeoff, or market estimate.
- **Voiceover:** “The source field tells you exactly which IFC quantity was used. If any element lacks a usable quantity, coverage drops and the plugin withholds the affected line total and listed-scope total instead of filling the gap with a guess.”

## 0:49–1:12 — Inspect the model in 3D

- **Screen:** `bim_render_view` result and Hermes Desktop preview.
- **Action:** orbit and zoom the model, click a visible element.
- **Show:** displayed element identity/type. Do not promise dimensions, storey isolation, clash detection, or code-compliance findings.
- **Voiceover:** “The viewer is self-contained: it works without loading Three.js from a CDN.”

## 1:12–1:20 — Close

- **Screen:** brief plugin repo / catalog PR shot, only after the PR is actually open.
- **Voiceover:** “Hermes BIM Studio: transparent IFC quantities and an interactive model viewer, inside Hermes.”

## Recording gates

- Re-run the current tests and capture actual tool output; do not fabricate cards or replace missing values in editing.
- Show the explicit rate inputs and label them illustrative.
- Keep the final export under 90 seconds. Do not say “bid-ready”, “certified”, “exact”, “code compliant”, or “zero hallucinations”.
- Do not imply catalog admission, Marketplace availability, or hackathon submission until each has actually occurred.
