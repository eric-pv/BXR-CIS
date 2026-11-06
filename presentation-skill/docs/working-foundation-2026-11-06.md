# BXR Presentation — execution status and next-run commands

## Implemented in this PR
1. Restored the three approved PNG backgrounds under `approved-layouts/military-tech/` using original retained Git blob SHAs (unchanged image bytes).
2. Centralized style and master requirements in `config/presentation-theme.json`. This is a **provisional implementation config**, subject to official CIS v3.2 and template.
3. Added `docs/selection-and-master-qa.md` with explicit layout selection hierarchy, native-editability and QA rules.
4. Added a fast scanner `scripts/index-pptx.py` for both original libraries and an OOXML validator `scripts/validate-pptx.py`.
5. Added a reproducible three-slide **technical pilot** generator `scripts/build-military-pilot.js`; requires official logo image input and the approved backgrounds.
6. Connected these paths to the main Skill contract.

## Verified source inventory, 2026-11-06
A scan of local source copies gave **5,788 slide XML entries**, including:
- `500頁.pptx`: **604** slide XMLs.
- `Aviation Slides.zip`: **249 PPTX** source decks containing **5,184** slide XMLs.
- **29 oversized slide XMLs** retained in the catalog as `oversize-unparsed`; do not treat those entries as analyzed layouts.
- All catalog categories are provisional. **Zero layouts are marked CIS-approved.** The full local CSV report is a separate deliverable; it has not been committed to this repository.

## Reproduce catalog on your workstation
From repo root:

```powershell
python .\presentation-skill\scripts\index-pptx.py --big-deck ".\presentation-skill\source-library\500頁.pptx" --aviation-zip ".\presentation-skill\source-library\Aviation Slides.zip" --output ".\presentation-skill\catalog\generated"
```

Generated CSVs: `layouts.csv` and `aviation-decks.csv`. They are review candidates, not design approvals.

## Build three-page pilot on workstation

```powershell
npm install pptxgenjs
node .\presentation-skill\scripts\build-military-pilot.js "." ".\01_Logo\<choose-approved-square-logo>.png" ".\BXR_Military_Pilot.pptx"
python .\presentation-skill\scripts\validate-pptx.py ".\BXR_Military_Pilot.pptx"
```

Select a real logo file from `01_Logo/` that matches the pilot's square-symbol placement. A wide official wordmark requires adapting the master image dimensions.

Pilot validates editable content and shared layout backgrounds conceptually; **actual Microsoft PowerPoint and CIS layout-signoff remain outstanding**. Production implementation must ensure type styles, colors, charts and bullets inherit from true PowerPoint theme/master elements, not per-slide hardcoded visual properties.

## Remaining requirements
- Confirm official master logo variants and placement for cover/section/content.
- Build the final editable .pptx/.potx master, including theme colors and style inheritance; design tokens alone are insufficient.
- Render thumbnails and visually audit candidates. Review paid-template licensing and privacy/access control.
- Select and approve a small pilot set of complex source layouts, with PowerPoint animation retention tests.
- Implement the NL brief -> narrative -> approved layout retrieval -> PPTX generation -> render/QA pipeline.

## Additional implemented tools and reproducible commands

Generate a PPTX with approved layouts and then apply theme + master typography defaults:

```powershell
npm install pptxgenjs
node .\presentation-skill\scripts\build-military-pilot.js "." ".\01_Logo\<approved-square-symbol>.png" ".\pilot-base.pptx"
python .\presentation-skill\scripts\apply-bxr-theme.py ".\pilot-base.pptx" ".\pilot-themed.pptx"
python .\presentation-skill\scripts\validate-pptx.py ".\pilot-themed.pptx"
```

The OOXML patch applies the CIS color scheme, theme font references and default Slide Master title/body typography. Slide-specific explicit text formatting still overrides master styles; verify inheritance in native PowerPoint. Do not replace the official v3.2 template with this technical sample until the relevant design is approved.

Safe candidate selector (blocks all unapproved source layouts):

```powershell
python .\presentation-skill\scripts\select-layout.py ".\presentation-skill\catalog\generated\layouts.csv" "請幫我做一頁訓練流程圖"
```

GitHub Actions `Build BXR PPTX Source Catalog` can also regenerate both catalog CSVs on demand and provides a workflow artifact. Requires Git LFS source downloads. Outputs remain provisional, not official templates.
