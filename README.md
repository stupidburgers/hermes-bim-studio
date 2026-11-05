# Hermes BIM Studio (ConstructIQ)

[![CI](https://github.com/stupidburgers/hermes-bim-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/stupidburgers/hermes-bim-studio/actions/workflows/ci.yml)

**An IFC model-inspection and quantity-reporting plugin for Hermes Agent.**

Built for the **Hermes Agent Plugin Hackathon** (Nous Research, Nov 2026, $20,000 cash prizes).
Owner: `stupidburgers`

---

## What It Does

Hermes BIM Studio provides Hermes with a local IFC inspection, quantity-reporting, and interactive model-viewing workflow:
1. **Semantic BIM Ingestion:** Directly parses standard IFC2x3, IFC4, and IFC4X3 building models using native `ifcopenshell`.
2. **Transparent IFC quantities:** Reports `BaseQuantities.NetSideArea` for walls and `BaseQuantities.NetVolume` for slabs, converts using the quantity's IFC unit, and shows measured coverage/missing values. Door and window quantities are entity counts. It does not invent a quantity where the model omits one.
3. **Model-quality checks:** Flags missing spatial containment and unnamed walls/slabs. These limited checks are not building-code or regulatory compliance certification.
4. **Optional cost arithmetic:** Uses only rates the user supplies; a total, when available, covers only the four listed categories (walls, slabs, doors, windows), not the whole project. This is not a professional bid or quantity-surveying certification.
5. **Embedded 3D viewer:** Generates a self-contained Three.js page for orbit/zoom and click-to-inspect element identity, displayed in Hermes Desktop preview.

---

## AEC workflow fit

- **Specific data surface:** IFC model quantities and interactive geometry are more than a prompt-only workflow.
- **Transparent limits:** quantities depend on exporter-supplied IFC BaseQuantities; unsupported or missing values are reported, not estimated.
- **Local runtime:** the viewer embeds its JavaScript dependencies and the plugin does not need an external service or API key at runtime.
- **Demo status:** the short demo is still to be recorded and must show a real model, its reported coverage, and the generated viewer.

## Third-party viewer assets

The viewer bundles Three.js r128 and OrbitControls under the upstream MIT license. See [`plugin/vendor/THIRD_PARTY_NOTICES.md`](plugin/vendor/THIRD_PARTY_NOTICES.md).
