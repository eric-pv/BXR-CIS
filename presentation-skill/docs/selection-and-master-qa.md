# BXR Presentation Skill — selection engine and acceptance rules

## Status
This document defines executable acceptance contracts. It does NOT imply a fully functioning slide generator exists yet.

## Slide selection (ranked)
1. Determine slide **role**: cover, section, content, comparison, process, timeline, data, map, product, people, summary.
2. For cover / section / content **in the military-tech series**, start from the 3 approved backgrounds in `approved-layouts/military-tech/`; backgrounds MUST NOT include text or logo.
3. For complex content pages: use an **approved BXR-adapted editable layout** matching role (the former `07_Templates` PowerPoint templates were removed on 2026-11-13 and must not be used).
4. Purchased libraries (`500頁.pptx` and Aviation Slides) are **source candidates**, not approved BXR templates. After adapting / inspecting a specific slide, mark `cis_approved=true` with proof of visual and editability QA before automatic use.
5. Default to one key message per slide; split dense content rather than shrinking text to unreadable size.
6. Preserve original animation only if editable objects and timing have been validated using actual PowerPoint.
7. Do not select a layout solely by filename: validate thumbnail, content density, native shapes, media types and aspect ratio.
8. Do not invent facts, third-party logos, target metrics, or military product specifications.

## PowerPoint master and theme implementation
- `presentation-skill/config/presentation-theme.json` is a machine-readable **implementation configuration**, secondary to the CIS manual and actual official v3.2 PowerPoint.
- Use a **real PPTX Theme color scheme** and `theme1.xml` + theme font scheme where supported, and title/body text styles on Slide Masters and Slide Layouts.
- The corporate Logo belongs in master/layout geometry, not per-slide shapes. Place only official `01_Logo/` assets. Never rasterize Logo into page background.
- Different Slide Layouts: cover, section, content, and feature-specific editable layouts.
- Titles, body, date, chapter numbers, page numbers and data are native editable placeholders or shapes.
- For dark pages, choose accessible white/light text and brand accent only where contrast is sufficient; for white body slides use Command Black or Graphite main body.
- Do not fill the entire slide with Army/Navy/Fire/Police sector colors; use restrained accents.
- Typography sizes in configuration are **provisional implementation defaults**, to be revised after comparison with the official v3.2 PPTX rather than marketed as CIS-mandated constants.
- PowerPoint theme colors and chart series should be derived from CIS, not sampled from background artwork.

## QA: must be verified from generated PPTX
- No content-overflow, unintended overlaps, or clipped text on any page.
- Brand logo inherited from Slide Layout / Slide Master; no duplicated per-slide logo image.
- Changing a master/layout logo should change all corresponding pages.
- Title/body fonts and color inherit from theme/master placeholders rather than being hard-coded on each shape unless an intentional override is required.
- No source-watermarks, sample-company names, unverified numbers, or license-required credits improperly removed.
- PowerPoint opens without repair and all slide-specific text/tables/charts remain editable.
- Presentation content appropriate to audience, not one layout repeated for every slide.
- Every rendered slide receives a manual or automated visual QA pass.

## Licensing
The user permits these provided assets in the project. This is distinct from confirmation that a third-party license allows public redistribution. Access to the repo and commercial assets should be controlled appropriately.

## Creative-direction boundary (2026-11-06 user feedback)
This document describes *content-fit* and *technical compliance*, not layout design specifications. The final design is owned by Claude.

- The approved military content-slide BANNER is a **title-bearing element**, not an empty decorative strip. White area starts beneath it and holds the page content.
- Cover and section transitions use a luminous flare; arrange title/chapter lettering to use the flare as a meaningful emphasis and focal anchor. The exact placement is a Claude design decision.
- Do not adopt any ChatGPT prototype's content-title coordinates, font sizes, or detailed geometry. No prescriptive font-size chart in the prep package.
- Use brand family/colors from CIS and approved assets; Claude develops the specific layout, style scale and page compositions for signoff.
- Quality review must include layout aesthetics and visual hierarchy, not merely lack of clipping.
