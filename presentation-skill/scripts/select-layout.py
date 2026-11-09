#!/usr/bin/env python3
"""Layout registry tool: build `catalog/layout-registry.json` and suggest layouts from it.

Status flow (one direction, one step at a time):
    source-candidate  ->  claude-reviewed  ->  cis-approved
  * source-candidate : a scanned slide / idea from the purchased libraries (catalog/generated/source-slides.csv).
                       Never auto-selected.
  * claude-reviewed  : rebuilt natively in CIS v3.2 by Claude (bxr_deck layout variants); usable in drafts,
                       output still marked visual_approval=pending-eric.
  * cis-approved     : Eric approved the rendered layout. Only a person sets this (edit the registry +
                       `approved_by`/`approved_on`); `--write-registry` keeps existing approvals.

Usage
  python scripts/select-layout.py --write-registry                    # rescan bxr_deck variants
  python scripts/select-layout.py "三個訓練效益重點"                    # suggest from free text
  python scripts/select-layout.py --family items --count 3 --json
"""
import argparse, importlib, json, re, sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]          # presentation-skill/
REGISTRY = HERE / "catalog" / "layout-registry.json"
STATES = ["source-candidate", "claude-reviewed", "cis-approved"]
TRANSITIONS = {"source-candidate": ["claude-reviewed"], "claude-reviewed": ["cis-approved", "source-candidate"],
               "cis-approved": ["claude-reviewed"]}
SELECTABLE = ("claude-reviewed", "cis-approved")
VARIANT_MODULES = ["bxr_deck.layouts", "bxr_deck.layouts_aviation"]   # the second is scanned only if present
REF_SOURCE = "presentation-skill/source-library/500頁.pptx"
AVI_SOURCE = "presentation-skill/source-library/Aviation Slides.zip"

FAMILY_WORDS = {
    "agenda": ["agenda", "contents", "outline", "目錄", "大綱", "議程", "アジェンダ", "目次"],
    "process": ["process", "steps", "workflow", "flow", "phase", "流程", "步驟", "階段", "導入", "ステップ", "手順", "プロセス"],
    "data": ["chart", "kpi", "data", "statistics", "數據", "圖表", "指標", "統計", "データ", "グラフ"],
    "text": ["statement", "summary", "conclusion", "重點", "結論", "摘要", "說明", "まとめ"],
    "items": ["features", "benefits", "pillars", "items", "特色", "效益", "優勢", "功能", "項目", "特長", "メリット"],
}


# ------------------------------------------------------------------ registry build
def scan_variants():
    sys.path.insert(0, str(HERE))
    found = []
    for mod in VARIANT_MODULES:
        if not (HERE / (mod.replace(".", "/") + ".py")).exists():
            continue
        m = importlib.import_module(mod)
        for v in getattr(m, "VARIANTS", []):
            if any(f["variant"] == v.name for f in found):
                continue
            found.append({"variant": v.name, "family": v.family, "ref": list(v.ref), "nmin": v.nmin, "nmax": v.nmax,
                          "needs_image": bool(v.needs_image), "prefers": v.prefers or "", "module": mod,
                          "doc": (v.render.__doc__ or "").strip().split("\n")[0]})
    return found


def record(v, previous=None):
    ref = v["ref"]
    avi = bool(ref) and isinstance(ref[0], str)          # aviation refs are catalog slide_ids ("AVI-064-0018")
    rec = {
        # --- fields required by catalog/layouts.schema.json (kept compatible)
        "id": v["variant"],
        "source_file": (AVI_SOURCE if avi else REF_SOURCE) if ref else "presentation-skill/bxr_deck/compose.py",
        "source_slide": (int(ref[0].rsplit("-", 1)[1]) if avi else ref[0]) if ref else 1,
        "category": v["family"],
        "tags": [v["family"], v["prefers"]] if v["prefers"] else [v["family"]],
        "editable": True,
        "animation_present": False,
        "animation_verified": False,
        "approved": False,
        "license_status": "internal-allowed",
        # --- registry fields
        "variant": v["variant"],
        "family": v["family"],
        "module": v["module"],
        "status": "claude-reviewed",
        "origin": "reference-distilled" if ref else "native",
        "ref_pages": ref,
        "ref_slides": [p if isinstance(p, str) else f"PMLD-{p:04d}" for p in ref],
        "items_min": v["nmin"],
        "items_max": v["nmax"],
        "needs_image": v["needs_image"],
        "prefers": v["prefers"],
        "description": v["doc"],
        "history": [{"status": "claude-reviewed", "by": "claude", "note": "native CIS v3.2 rebuild in bxr_deck"}],
    }
    if previous and previous.get("status") == "cis-approved":          # never downgrade a human approval
        for k in ("status", "approved", "approved_by", "approved_on", "history"):
            if k in previous:
                rec[k] = previous[k]
    return rec


def build_registry(path=REGISTRY):
    old = {}
    if path.exists():
        old = {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8")).get("layouts", [])}
    layouts = [record(v, old.get(v["variant"])) for v in scan_variants()]
    reg = {
        "version": 1,
        "description": "BXR layout registry. Status flow source-candidate -> claude-reviewed -> cis-approved. "
                       "Only cis-approved layouts are approved=true; only a person promotes to cis-approved.",
        "states": STATES,
        "transitions": TRANSITIONS,
        "selectable_states": list(SELECTABLE),
        "source_candidates": {"catalog": "presentation-skill/catalog/generated/source-slides.csv",
                              "status": "source-candidate",
                              "note": "every scanned purchased slide; not selectable until rebuilt and reviewed"},
        "record_schema": "presentation-skill/catalog/layouts.schema.json",
        "layouts": layouts,
    }
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return reg


def load_registry(path=REGISTRY):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def promote(reg, layout_id, new_status, by, note=""):
    """Move one layout one step along the flow; validates the transition."""
    rec = next(r for r in reg["layouts"] if r["id"] == layout_id)
    if new_status not in TRANSITIONS[rec["status"]]:
        raise ValueError(f"{layout_id}: {rec['status']} -> {new_status} is not an allowed transition")
    rec["status"] = new_status
    rec["approved"] = new_status == "cis-approved"
    if rec["approved"]:
        rec["approved_by"] = by; rec["approved_on"] = date.today().isoformat()
    rec.setdefault("history", []).append({"status": new_status, "by": by, "note": note})
    return rec


# ------------------------------------------------------------------ selection
def guess_family(text):
    t = (text or "").casefold()
    scores = [(sum(len(w) for w in words if w in t), -i, fam) for i, (fam, words) in enumerate(FAMILY_WORDS.items())]
    s, _, fam = max(scores)
    return fam if s else "items"


def guess_count(text):
    t = text or ""
    m = re.search(r"(\d+)\s*(個|項|点|點|つ|steps?|items?|points?|phases?|階段|步)", t, re.I)
    if m:
        return int(m.group(1))
    zh = {"二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8}
    m = re.search(r"([二兩三四五六七八])\s*(個|項|點|大|階段|步)", t)
    return zh[m.group(1)] if m else None


def suggest(reg, family=None, count=None, text="", include_candidates=False, limit=5):
    family = family or guess_family(text)
    allowed = set(SELECTABLE) | ({"source-candidate"} if include_candidates else set())
    out = []
    for r in reg["layouts"]:
        if r["family"] != family or r["status"] not in allowed:
            continue
        if count is not None and not (r["items_min"] <= count <= r["items_max"]):
            continue
        score = 10.0 + (3 if r["status"] == "cis-approved" else 0) + (0.5 if r["needs_image"] else 0)
        out.append({"id": r["id"], "status": r["status"], "score": score, "ref_slides": r["ref_slides"],
                    "items": [r["items_min"], r["items_max"]], "description": r["description"]})
    out.sort(key=lambda x: (-x["score"], x["id"]))
    return {"family": family, "count": count, "candidates": out[:limit],
            "fallback": None if out else "no registered layout fits; use the plain native layout of the family "
                                         "(agenda.list / items.cards / process.track / text.bullets / data.chart)"}


def main(argv=None):
    p = argparse.ArgumentParser(description="BXR layout registry / selector")
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--family"); p.add_argument("--count", type=int)
    p.add_argument("--registry", default=str(REGISTRY))
    p.add_argument("--write-registry", action="store_true")
    p.add_argument("--include-candidates", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if a.write_registry:
        reg = build_registry(Path(a.registry))
        print(f"wrote {a.registry}: {len(reg['layouts'])} layouts")
        return 0
    reg = load_registry(a.registry)
    count = a.count if a.count is not None else guess_count(a.text)
    print(json.dumps(suggest(reg, a.family, count, a.text, a.include_candidates), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
