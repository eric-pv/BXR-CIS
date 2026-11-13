# Big x Reality Presentation Skill — Foundation

Status: initial planning and audit, not yet a production-ready slide generator.

## Goal
Create editable, high-quality PowerPoint decks from natural-language briefs using existing licensed slide designs and BXR CIS v3.2. Claude Code will perform primary design and implementation. Users should not need to select layouts or manually remove sample content.

## Existing authoritative assets
- `../00_Brand_Guidelines/v3.2/README_v3.2.txt` — v3.2 brand release notes.
- `../02_Color/BXR_Colors_v3.2.json` — machine-readable color system.
- `07_Templates/` PowerPoint templates v3.1/v3.2 were removed (Eric, 2026-11-13): do not use or recreate them; build decks with `bxr_deck` and the approved layouts.
- `../00_Brand_Guidelines/v3.2/Asset_Inventory_v3.2.csv` — official asset inventory.
- The two PDFs in `../00_Brand_Guidelines/v3.2/` together form the definitive 89-page CIS v3.2 manual (pages 1–45 and 46–89).

## Proposed workflow
1. Read CIS and user's brief; identify internal/external audience and sector.
2. Outline story, evidence, slide roles and information density.
3. Search the layout catalog and select approved BXR-adapted PPTX slides.
4. Duplicate native slides and substitute content while retaining editable objects and appropriate animations where validated.
5. Adapt design to CIS without flattening complex layouts or inventing proprietary logos.
6. Render and visually inspect EVERY slide, plus verify file opens, text fit and content accuracy.
7. Return editable PPTX and optionally PDF. Log source-layout IDs and unresolved limitations.

## Source vs approved material
- `source-library/` (future): immutable upstream licensed original materials, access controlled.
- `approved-layouts/` (future): transformed/reviewed BXR layout assets with clean editable placeholders.
- `catalog/` (future): index of sources, preview images, animation tests, editability, selection tags.
Never overwrite original licensed archives.

## Security and licensing
**Important: This repository was verified PUBLIC on 2026-11-06.** Do NOT upload purchased template archives, confidential product images, paid fonts, or sensitive internal content until repository visibility and license permissions are verified. Git LFS does not make a public repository private.
Ensure paid-template terms permit internal multi-user adaptation/distribution. Do not remove mandatory attribution/legal notices.

## Current phase
Initial skill contract and acceptance plan, no automated template conversion yet. See `docs/implementation-plan.md`.

## 2026-11-06 verified foundation status
- **Source archives now present:** `source-library/500頁.pptx` and `source-library/Aviation Slides.zip` via Git LFS.
- **Approved background assets now present in this branch:** `approved-layouts/military-tech/BXR_Military_{Cover,Section,Content_White}_16x9.png` (see actual filenames).
- **Additional icons** indexed under `../04_Graphics/Icons/` and `catalog/icon-catalog.csv`.
- **Theme and Slide Master contract** in `config/presentation-theme.json`; selection and QA in `docs/selection-and-master-qa.md`.
- **Runnable tools:** `scripts/index-pptx.py`, `scripts/build-military-pilot.js`, `scripts/apply-bxr-theme.py`, `scripts/validate-pptx.py`.
- **On-demand index:** `.github/workflows/build-presentation-catalog.yml` produces downloadable CSV artifacts. No claim that all source slides are visually approved.
- **Structural source scan:** 604 slide XMLs in main deck, 249 PPTX decks in Aviation with 5,184 slides. 29 oversized XML entries unparsed.
- **Prototype limitation:** master/logo/layout proof demonstrated, but production-grade dynamic layout retrieval, theme inheritance validation, source-template adaptation, and actual PowerPoint tests remain pending.
