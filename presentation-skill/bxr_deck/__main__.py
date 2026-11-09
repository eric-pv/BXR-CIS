"""CLI.
  python -m bxr_deck build  --brief brief.json --output out/ [--previous-plan out/x.plan.json] [--no-render]
  python -m bxr_deck brief  --text outline.txt --id my-deck --output brief.json   (outline text -> brief)
  python -m bxr_deck master [--potx]                                               (rebuild master template)
"""
import argparse, json, sys
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bxr_deck")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--brief", required=True); b.add_argument("--output", required=True)
    b.add_argument("--previous-plan"); b.add_argument("--no-render", action="store_true")
    t = sub.add_parser("brief"); t.add_argument("--text", required=True); t.add_argument("--id", required=True); t.add_argument("--output", required=True)
    t.add_argument("--audience", default="internal"); t.add_argument("--slides", type=int)
    m = sub.add_parser("master"); m.add_argument("--potx", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        from .generator import generate, BriefError
        try:
            pptx, plan, qa = generate(a.brief, a.output, a.previous_plan, render=not a.no_render)
        except BriefError as exc:
            print(f"INVALID BRIEF: {exc}", file=sys.stderr); return 2
        print(json.dumps({"pptx": str(pptx), "slides": qa["slide_count"], "status": qa["status"],
                          "failed_gates": [k for k, g in qa["gates"].items() if not g["pass"]], "warnings": qa["warnings"][:3]},
                         ensure_ascii=False, indent=2))
        return 0 if qa["status"] == "PASS" else 1
    if a.cmd == "brief":
        from .nl import brief_from_text
        brief = brief_from_text(Path(a.text).read_text(encoding="utf-8"), a.id, a.audience, a.slides)
        Path(a.output).write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
        print(a.output); return 0
    if a.cmd == "master":
        from .master import build
        print(build(potx=a.potx)); return 0


if __name__ == "__main__":
    sys.exit(main())
