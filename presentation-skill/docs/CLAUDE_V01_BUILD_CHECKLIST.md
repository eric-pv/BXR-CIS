# Claude Code V0.1 — implementation-ready engineering checklist

**Authority**: `docs/CLAUDE_HANDOFF_DESIGN_AUTHORITY.md`. The user delegates all spatial layout / aesthetics / font-size systems to Claude. This document defines engineering contracts and testable behavior, **not design choices**.

## Inputs
- Accept JSON conforming to `contracts/presentation-brief.schema.json`; support `zh-TW`, `en`, and `JP`.
- Treat brief `facts`, `source_refs`, and `source_policy` as authoritative inputs. Never fabricate ROI, specifications, customers or figures.
- Follow `must_include` and `must_avoid`; if constraints conflict, flag before output.
- Keep user content separate from source PPTX placeholders and branding.

## Intermediate plan
- Emit a JSON planning artifact conforming to `contracts/deck-plan.schema.json`.
- Each slide has a role, human-readable message, content references, source layout, editable element roles, evidence status and QA flags.
- Only `cis-approved-layout` entries that have passed visual review may be chosen automatically from purchased libraries.
- Every unverified claim must appear in `unverified_claims`, not silently inserted into the deck.
- Keep plan and generated PPTX traceable through slide IDs.

## Generator
1. Read CIS source and the three approved military-tech backgrounds, official logos, icons and templates.
2. Claude independently designs and signs off final PowerPoint master/layout theme, including actual typography/spacing/palette rules.
3. Build editability-first PowerPoint with real master/layout logo placement, theme fonts and colors, text placeholders and editable data charts/tables.
4. Use top Banner as **title area** for white military content page. Use luminous flare as design focus for cover/section titles. Exact coordinates belong to Claude.
5. Support meaningful different compositions (not one-page design duplicated). Preserve copy and avoid clipped text.
6. Produce `<brief-id>.pptx`, `<brief-id>.plan.json`, and `<brief-id>.qa.json` (include status, tests, warnings, source layout IDs, slide count). PDF optional per brief.

## Test cases already defined
| Test fixture | Primary challenge |
|---|---|
| `tests/fixtures/briefs/police-xr-overview.json` | Chinese police proposal; restricted facts; process + section pages |
| `tests/fixtures/briefs/cross-sector-english.json` | English copy, cross-sector taxonomy, 15-slide density |
| `tests/fixtures/briefs/fire-rescue-brief.json` | Fire-sector CIS accents without replacing corporate red |
| `tests/fixtures/briefs/data-comparison.json` | Honest comparisons with incomplete cost/performance data |

## Automated acceptance gates (Claude owns implementation)
- **G1 Input**: all fixture JSON validates; malformed brief rejected with actionable error.
- **G2 Plan**: plan JSON validates and slide roles/content refs exist.
- **G3 File**: PPTX ZIP/OOXML valid and opens in native PowerPoint without repair.
- **G4 Brand**: official logo inherited from master/layout; no slide-level duplicate; theme font/color source traceable.
- **G5 Editability**: title/text/chart/table remain editable where applicable; no flattened text.
- **G6 Layout quality**: visual inspection on rendered images catches overflows, crowding, poor focal hierarchy, incorrect title zones, inconsistent spacing.
- **G7 Evidence**: no invented claims; source refs and unverified flags preserved.
- **G8 Consistency**: Chinese/English fonts render; titles do not collide with banners/visual focus.
- **G9 Animation**: only mark `animation_verified=true` after actual PowerPoint playback check; unsupported effects are explicitly disclosed.

## Delivery milestones
- **M0 (repo ready)**: asset paths, three approved backgrounds, icon index, schemas, fixtures, preflight and CI all pass.
- **M1 (design signoff)**: Claude creates and user visually approves three actual slide masters/layouts; prior ChatGPT mockup is not reference.
- **M2 (functional prototype)**: generator consumes one fixture and outputs PPTX + plan + QA data.
- **M3 (V0.1)**: generator processes all four fixtures, outputs editable slides, passes automated gates and has manual visual review.
- **M4 (expansion)**: selectively adapt licensed complex layouts and test animation retention.

## Explicit non-goals for V0.1
- Converting all 5,788 source slides.
- Guaranteeing all paid-template animations survive.
- Guaranteeing no post-generation visual iteration.
- Treating structural XML flags alone as proof of design quality.

## Commands
```powershell
python presentation-skill/scripts/preflight.py --repo .
python -m pip install "jsonschema>=4.18,<5"
python presentation-skill/tests/test_contracts.py
```

Generated catalog workflow: GitHub Actions → **Build BXR PPTX Source Catalog** → download CSV artifact. Those rows are not considered design-approved until Claude/user review.
