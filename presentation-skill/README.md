# Big x Reality Presentation Skill — Foundation

Status: initial planning and audit, not yet a production-ready slide generator.

## Goal
Create editable, high-quality PowerPoint decks from natural-language briefs using existing licensed slide designs and BXR CIS v3.2. Claude Code will perform primary design and implementation. Users should not need to select layouts or manually remove sample content.

## Existing authoritative assets
- `../README_v3.2.txt` — v3.2 brand release notes.
- `../02_Color/BXR_Colors_v3.2.json` — machine-readable color system.
- `../07_Templates/BXR_Presentation_Template_v3.2.pptx` — official starting presentation template.
- `../Asset_Inventory_v3.2.csv` — official asset inventory.
- The 89-page `BXR_CIS_Brand_Guidelines_v3.2.pdf` is the definitive manual. If split, both parts together constitute the complete source.

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
