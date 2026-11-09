# AUTORUN_LOW — V0.1 low-cost docs/tests run

Resumable log. LOW=DONE → stop. IN-PROGRESS updated < 2 h ago → another session is running → stop.
Branch: `dev/claude-v01-low-docs-tests` · PR: https://github.com/eric-pv/BXR-CIS/pull/16

| Item | Status | Updated (UTC) | Notes |
|------|--------|---------------|-------|
| L1 tests/test_pipeline.py | DONE | 2026-11-09T05:58Z | 8 tests; all fixtures, no render; master built from code in a temp dir |
| L2 README_V01.md | DONE | 2026-11-09T05:58Z | |
| L3 SKILL.md status/usage | DONE | 2026-11-09T05:58Z | |
| L4 presentation-preflight.yml | DONE | 2026-11-09T05:58Z | python-pptx/lxml/pillow; runs test_master + test_pipeline |
| PR + CI + squash merge | IN-PROGRESS | 2026-11-09T05:58Z | |

## Decisions (conservative, scope = 5 allowed files)
- Earlier commits on this branch touched `bxr_deck/generator.py`, `layouts.py`, `master.py`; reverted to `main` to stay inside the allowed file set.
- `bxr_deck/master.py` line ~187 uses a backslash inside an f-string expression → SyntaxError on Python 3.11.
  Not fixable here (file out of scope). CI pinned to Python 3.12; README states 3.12+. Follow-up: one-line fix in master.py to restore 3.11.
- CI checks out without LFS, so `templates/BXR_Military_Master_v0.1.pptx` is a pointer: test_pipeline builds the master
  with `bxr_deck.master.build` into a temp dir and calls `generate(render=False, master=...)` (same path as `build --no-render`).
  The real-CLI test and the source-library SHA256 test skip without LFS files; both ran and passed locally after `git lfs pull`.

## Known issues
- `07_Templates/*.pptx` show as modified (Git LFS config issue). Not committed, not modified, not restored.
