# AUTORUN_MEDIUM — catalog / registry / layout fixes run

Resumable log. MEDIUM=DONE → stop. An item IN-PROGRESS updated < 2 h ago → another session is running → stop.
Branch: `claude/sweet-allen-xj6vig` (system-assigned), rebuilt from origin/main f62362b.

| Item | Status | Updated (UTC) | Notes |
|------|--------|---------------|-------|
| Prereqs (LFS, fonts) | DONE | 2026-11-09T10:58Z | git lfs pull OK; fonts-noto-cjk; fontconfig aliases Noto Sans TC/JP → Noto Sans CJK TC/JP; B612 Mono woff2 (@fontsource/b612-mono 5.3.0) → ttf via fonttools; preflight PASS; contracts 0 failures |
| M1 build-source-catalog.py | DONE | 2026-11-09T11:05Z | 5,788 slides (604 PMLD + 5,184 AVI in 249 decks), 33 unparsed (>8 MB XML, reasons in summary.json), 0 deck errors, all 16:9; ~38 s full run; no thumbnails / no slide text stored |
| M2 layout-registry + icons + select-layout + test_catalog | IN-PROGRESS | 2026-11-09T11:05Z | |
| M3 layout fixes | TODO | | |
| M4 fixtures, previews, tests, PR, merge | TODO | | |

## Known issues
- `07_Templates/*.pptx` may show as modified (Git LFS config issue). Not committed, not modified, not restored.

## Decisions
- M1: IDs use presentation order (page a person sees), slide part recorded separately. Categories use slide XML only
  (chart/table objects, text keywords, object counts); deck/file names are never read for categorisation.
- M1: parse limit 8 MB per slide XML (`--max-xml-mb`); larger slides recorded `unparsed` with size reason.
- M1: `.github/workflows/build-presentation-catalog.yml` still calls the old `index-pptx.py`; the workflow is outside
  this run's file scope, so it was left unchanged. Switch it to `build-source-catalog.py` in a later PR.
