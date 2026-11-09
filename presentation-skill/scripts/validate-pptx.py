#!/usr/bin/env python3
"""Read-only OOXML structure + brand-inheritance check for a generated PPTX.

Checks (all automatic, no PowerPoint needed):
  * ZIP opens, every XML part is well-formed, every internal relationship target exists,
    every part has a content type (missing ones are a classic "PowerPoint needs to repair" cause).
  * Slide / layout / master counts, layout used by each slide.
  * Official logo images (byte-identical to files in 01_Logo/PNG) are found on masters/layouts only;
    any logo picture placed directly on a slide is reported as a duplicate-logo error (gate G4).
  * Native editable text runs, tables, charts per slide; slides with no native text are flagged.
PowerPoint open/visual/animation QA is still required separately.

Usage: python validate-pptx.py deck.pptx [--logo-dir 01_Logo/PNG] [--strict]
"""
import argparse, hashlib, json, posixpath, re, sys, zipfile
from pathlib import Path
from lxml import etree

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
      "ct": "http://schemas.openxmlformats.org/package/2006/content-types"}
SLIDE = re.compile(r"ppt/slides/slide\d+\.xml$")
MASTER = re.compile(r"ppt/slideMasters/slideMaster\d+\.xml$")
LAYOUT = re.compile(r"ppt/slideLayouts/slideLayout\d+\.xml$")
DEFAULT_LOGO_DIR = Path(__file__).resolve().parents[2] / "01_Logo" / "PNG"


def _rels_name(part):
    d, f = posixpath.split(part)
    return posixpath.join(d, "_rels", f + ".rels")


def _rels(z, part):
    name = _rels_name(part)
    if name not in z.namelist():
        return {}
    root = etree.fromstring(z.read(name))
    out = {}
    for r in root.findall("rel:Relationship", NS):
        target = r.get("Target")
        if r.get("TargetMode") != "External":
            target = posixpath.normpath(posixpath.join(posixpath.dirname(part), target))
        out[r.get("Id")] = (r.get("Type").rsplit("/", 1)[-1], target, r.get("TargetMode"))
    return out


def _logo_hashes(logo_dir):
    logo_dir = Path(logo_dir)
    return {hashlib.sha256(p.read_bytes()).hexdigest(): p.name for p in logo_dir.glob("*.png")} if logo_dir.exists() else {}


def validate(file, logo_dir=DEFAULT_LOGO_DIR):
    errors, warnings = [], []
    logos = _logo_hashes(logo_dir)
    with zipfile.ZipFile(file) as z:
        bad = z.testzip()
        if bad:
            errors.append("corrupt zip member " + bad)
        members = set(z.namelist())
        ct = etree.fromstring(z.read("[Content_Types].xml"))
        defaults = {d.get("Extension").lower() for d in ct.findall("ct:Default", NS)}
        overrides = {o.get("PartName").lstrip("/") for o in ct.findall("ct:Override", NS)}
        for m in members:
            if m.endswith("/") or m == "[Content_Types].xml":
                continue
            if m not in overrides and m.rsplit(".", 1)[-1].lower() not in defaults:
                errors.append("no content type for " + m)
            if m.endswith(".xml") or m.endswith(".rels"):
                try:
                    etree.fromstring(z.read(m))
                except etree.XMLSyntaxError as exc:
                    errors.append(f"malformed XML {m}: {exc}")
        for o in overrides:
            if o not in members:
                warnings.append("stale content-type override (tolerated by PowerPoint): " + o)
        # relationship integrity
        for m in sorted(members):
            if m.endswith(".rels") or m.endswith("/"):
                continue
            for rid, (typ, target, mode) in _rels(z, m).items():
                if mode != "External" and target not in members:
                    errors.append(f"{m} {rid} -> missing {target}")

        def logo_pics(part):
            found = []
            rels = _rels(z, part)
            for blip in etree.fromstring(z.read(part)).iterfind(".//p:pic//a:blip", NS):
                rid = blip.get("{%s}embed" % NS["r"])
                if rid in rels and rels[rid][1] in members:
                    h = hashlib.sha256(z.read(rels[rid][1])).hexdigest()
                    if h in logos:
                        found.append(logos[h])
            return found

        slides = sorted((s for s in members if SLIDE.fullmatch(s)), key=lambda s: int(re.findall(r"\d+", s)[-1]))
        masters = sorted(s for s in members if MASTER.fullmatch(s))
        layouts = sorted(s for s in members if LAYOUT.fullmatch(s))
        layout_info = {}
        for name in layouts:
            root = etree.fromstring(z.read(name))
            cs = root.find("p:cSld", NS)
            layout_info[name] = {"name": cs.get("name") if cs is not None else None, "logos": logo_pics(name)}
        master_logos = {m: logo_pics(m) for m in masters}
        rows = []
        for name in slides:
            xml = etree.fromstring(z.read(name))
            rels = _rels(z, name)
            layout = next((t for typ, t, _ in rels.values() if typ == "slideLayout"), None)
            slide_logos = logo_pics(name)
            if slide_logos:
                errors.append(f"{name}: logo placed on slide instead of master/layout: {slide_logos}")
            row = {"slide": name,
                   "layout": layout_info.get(layout, {}).get("name"),
                   "inherited_logos": layout_info.get(layout, {}).get("logos", []),
                   "native_text_runs": len(xml.findall(".//a:t", NS)),
                   "placeholders": len(xml.findall(".//p:nvPr/p:ph", NS)),
                   "native_shapes": len(xml.findall(".//p:sp", NS)),
                   "tables": len(xml.findall(".//a:tbl", NS)),
                   "charts": len(xml.findall(".//c:chart", NS)),
                   "pictures": len(xml.findall(".//p:pic", NS)),
                   "timing_xml": int(xml.find(".//p:timing", NS) is not None)}
            rows.append(row)
            if row["native_text_runs"] == 0:
                warnings.append(f"{name}: no native editable text")
        if not masters:
            errors.append("no slide master")
        if logos and not any(master_logos.values()) and not any(v["logos"] for v in layout_info.values()):
            warnings.append("no official logo found on any master/layout")
        warnings.append("PowerPoint open-without-repair, visual and animation QA still required")
        return {"file": str(file), "status": "PASS" if not errors else "FAIL",
                "slides": len(slides), "masters": len(masters), "layouts": len(layouts),
                "master_logos": master_logos, "layout_logos": {v["name"]: v["logos"] for v in layout_info.values()},
                "details": rows, "errors": errors, "warnings": warnings}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("pptx")
    p.add_argument("--logo-dir", default=str(DEFAULT_LOGO_DIR))
    p.add_argument("--strict", action="store_true", help="exit 1 on errors")
    a = p.parse_args()
    res = validate(a.pptx, a.logo_dir)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(1 if (a.strict and res["errors"]) else 0)
