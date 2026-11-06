---
name: bxr-presentation
description: Build editable Big x Reality presentations using CIS v3.2 and approved PowerPoint layouts.
---

# Big x Reality Presentation Skill

Status: development foundation, not production-ready.

## Sources
Read the complete CIS v3.2 manual, official brand assets in the repository, and approved PPTX layout catalog. Existing official template: `07_Templates/BXR_Presentation_Template_v3.2.pptx`.

## Brand requirements
- Public-facing spelling: Big x Reality; BxR internally.
- Corporate: red #D02753, black #0B0F14, graphite #1E252D, paper #F2F4F6.
- Sector accents: army #596B42, navy #173A55, air #5D8AA8, fire #D2361E, police #2E5C9A. Avoid sector-colored full-page backgrounds.
- Use official logos and fonts. Never recreate logos or invent company data.
- Internal and external presentations require distinct cover styles. External covers can adapt to sectors within CIS limits.

## Deck workflow
1. Extract audience, purpose, language, duration, slide count and supplied facts.
2. Make a concise narrative and content plan.
3. Match slides with approved editable PPTX layouts.
4. Populate native shapes and approved brand visuals.
5. Check logo placement, typography, image crop, chart sourcing and page consistency.
6. Preserve and validate usable animations where technically feasible.
7. Render every slide; fix overflow, overlap, artifacts, sample company names and misleading demo data.
8. Deliver editable PPTX and QA summary.

Source archives must remain immutable. Remove unwanted sample source marks from reusable designs where licensing permits, without deleting required attribution.

Follow `../../docs/implementation-plan.md` for staged engineering and testing.

## PowerPoint Slide Master / Logo policy (mandatory)
- Corporate logos must be managed through **Slide Master and its Slide Layouts** (or native editable master elements), NEVER inserted separately by the generation engine on each slide.
- Use official logo assets already in `01_Logo/`. Brand-approved placement, variant, clear space, and size must follow the original CIS.
- Create purpose-specific layouts for cover, section divider, and content slides. Master/layout design controls whether the logo appears, including its color and position. A layout may intentionally suppress the logo if required by the approved design.
- Do not bake logos, titles, chapter numbers, dates, or other editable presentation content into background PNGs.
- When slides are duplicated or recomposed, prevent duplicate logos from both source masters and slide objects. Check rendered slide and underlying PPTX shapes for duplicates.
- Logo policy applies across all sector variants, not only the military-tech backgrounds.
- Validate one central master/layout edit propagates to all slides of that layout without editing individual slides.

## Implementation contracts (required)
Before generating a deck, read `../../config/presentation-theme.json` (machine-readable starter tokens) and `../../docs/selection-and-master-qa.md` (layout retrieval + acceptance). The CIS v3.2 manual and official PPTX template take precedence over provisional numeric style tokens.

- Apply a real PowerPoint Theme and Slide Master/Slide Layout styles for typography (typeface, sizes, colors, title/body styles), common logo, fields and shared colors. Avoid setting every slide's shared style independently.
- Respect separate cover / section / white-body content layouts. Load the actual approved 16:9 PNG backgrounds from `../../approved-layouts/military-tech/`.
- Index purchased sources with `../../scripts/index-pptx.py`; catalog entries are **unreviewed candidates**, not reusable approved layouts until a human confirms the visual result.
- Run structural QA via `../../scripts/validate-pptx.py` and visually render every slide; neither file checks nor generated mockups replace actual PowerPoint validation.

## Design ownership — explicit user decision (2026-11-06)
The **final PPT layout/design system belongs to Claude**, not to the preliminary ChatGPT prototype. Previous proof-of-concept coordinates, heading locations, sizes, and example slides are engineering demonstrations ONLY and must never be promoted into mandatory design specifications.

Non-negotiable user intent:
- Cover imagery: approximately left one-third, leaving ample right-hand title space.
- Cover and section slides: glowing light point / streak should visually anchor or emphasize editable title text. Claude chooses exact position, grid and size.
- **Content-page title is placed within the top technology banner**, not below it in the white body; the white body is for substantive content.
- Preserve approved source backgrounds, text/logo editability, and official BXR branding.
- Claude decides font-size hierarchy, exact geometry, white space, icon size, diagram structure, table layout, chart composition, and typography in the actual PPTX template while following CIS.
- A test PPTX created by ChatGPT is NOT an approved design and must not be treated as the reference for aesthetic alignment.

This Skill's prep tooling is limited to source inventory, contract schemas, asset integrity, technical checks, security/licensing notes and reproducible test inputs. Claude writes the production generator and owns visual QA signoff.
