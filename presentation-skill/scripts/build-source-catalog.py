#!/usr/bin/env python3
"""Build a per-slide structural catalog of the purchased reference libraries (read-only).

Sources (never modified, opened read-only):
  * presentation-skill/source-library/500頁.pptx          -> slide IDs PMLD-0001 …
  * presentation-skill/source-library/Aviation Slides.zip -> slide IDs AVI-001-0001 …
    (decks numbered by sorted ZIP entry name; macOS junk such as __MACOSX/ and ._* is skipped)

Every row is keyed by *presentation order* (the page number a person sees in PowerPoint), and also
records the underlying slide part. Categories are derived ONLY from the slide's own XML (text runs and
structural objects) — never from the file/deck name. Slide XML above --max-xml-mb is not parsed and
is recorded as `unparsed` with the reason, rather than silently dropped.

Outputs (no thumbnails, no slide text — only counts and hashes, safe for the public repo):
  catalog/generated/source-slides.csv
  catalog/generated/summary.json

All rows are `source-candidate`: scanning a slide successfully is NOT a CIS approval.
"""
import argparse, csv, hashlib, io, json, posixpath, re, sys, zipfile
from collections import Counter
from pathlib import Path
from lxml import etree

VERSION = "1.0"
NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
Q = {k: "{%s}" % v for k, v in NS.items()}
SLIDE_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")

FIELDS = ["slide_id", "library", "deck_id", "source_file", "source_sha256", "page", "slide_part",
          "slide_xml_bytes", "slide_xml_sha256", "slide_width_emu", "slide_height_emu", "aspect",
          "parse_status", "unparsed_reason", "shapes", "text_paragraphs", "text_runs", "text_chars",
          "pictures", "groups", "charts", "tables", "smartart", "media", "has_timing", "anim_effects",
          "category_auto", "category_basis", "status"]

# Content keywords (simplified + traditional Chinese, English). Matched against slide text only.
KEYWORDS = [
    ("agenda", ["目录", "目錄", "contents", "agenda", "大纲", "大綱"]),
    ("section", ["part 0", "part0", "chapter", "第一部分", "第二部分", "第三部分", "第四部分", "第一章", "第二章"]),
    ("timeline", ["timeline", "milestone", "roadmap", "发展历程", "發展歷程", "时间轴", "時間軸", "历程", "歷程"]),
    ("process", ["process", "step 0", "step0", "流程", "步骤", "步驟"]),
    ("comparison", ["comparison", " vs ", "versus", "对比", "對比", "比较", "比較"]),
    ("team", ["our team", "team member", "团队", "團隊"]),
    ("closing", ["thank you", "thanks", "谢谢", "謝謝", "感谢", "感謝"]),
]


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def aspect(cx, cy):
    if not cx or not cy:
        return ""
    r = cx / cy
    for name, v in (("16:9", 16 / 9), ("16:10", 1.6), ("4:3", 4 / 3), ("1:1", 1.0)):
        if abs(r - v) < 0.01:
            return name
    return f"{r:.3f}:1"


def rels(z, part):
    """Relationship id -> absolute target for a part."""
    d, b = posixpath.split(part)
    rp = posixpath.join(d, "_rels", b + ".rels")
    try:
        root = etree.fromstring(z.read(rp))
    except KeyError:
        return {}
    out = {}
    for r in root.findall(Q["rel"] + "Relationship"):
        t = r.get("Target", "")
        out[r.get("Id")] = t if r.get("TargetMode") == "External" else posixpath.normpath(posixpath.join(d, t))
    return out


def slide_order(z):
    """[(page, slide_part)] in presentation order, plus (cx, cy)."""
    pres = etree.fromstring(z.read("ppt/presentation.xml"))
    rmap = rels(z, "ppt/presentation.xml")
    order = []
    lst = pres.find(Q["p"] + "sldIdLst")
    for sid in (lst if lst is not None else []):
        part = rmap.get(sid.get(Q["r"] + "id"))
        if part:
            order.append(part)
    # slide parts not referenced in sldIdLst (orphans) are appended after, so nothing is lost
    present = sorted((m.filename for m in z.infolist() if SLIDE_RE.match(m.filename)),
                     key=lambda f: int(SLIDE_RE.match(f).group(1)))
    order += [p for p in present if p not in order]
    sz = pres.find(Q["p"] + "sldSz")
    cx = int(sz.get("cx")) if sz is not None else 0
    cy = int(sz.get("cy")) if sz is not None else 0
    return [(i + 1, p) for i, p in enumerate(order)], cx, cy


def categorise(m, text):
    """Category from slide content only. Returns (category, basis)."""
    t = " " + text.casefold() + " "
    if m["charts"]:
        return "data", "native chart"
    if m["tables"]:
        return "table", "native table"
    for cat, keys in KEYWORDS:
        hit = next((k for k in keys if k in t), None)
        if hit:
            return cat, f"slide text keyword '{hit.strip()}'"
    if m["smartart"]:
        return "diagram", "SmartArt"
    if m["pictures"] >= 3:
        return "image-grid", "3+ pictures"
    if m["pictures"] >= 1 and m["text_chars"] < 120:
        return "image-feature", "picture with little text"
    if m["text_chars"] == 0 and m["shapes"] + m["pictures"] <= 2:
        return "background", "no text, <=2 objects"
    if m["text_chars"] >= 600:
        return "text-dense", "600+ text characters"
    if m["shapes"] + m["groups"] >= 15:
        return "infographic", "15+ native shapes/groups"
    if m["text_paragraphs"] >= 4:
        return "text-list", "4+ text paragraphs"
    return "general", "no specific signal"


def measure(xml):
    root = etree.fromstring(xml, parser=etree.XMLParser(huge_tree=True, resolve_entities=False))
    m = {
        "shapes": len(root.findall(".//" + Q["p"] + "sp")),
        "pictures": len(root.findall(".//" + Q["p"] + "pic")),
        "groups": len(root.findall(".//" + Q["p"] + "grpSp")),
        "charts": len(root.findall(".//" + Q["c"] + "chart")),
        "tables": len(root.findall(".//" + Q["a"] + "tbl")),
        "smartart": len(root.findall(".//" + Q["dgm"] + "relIds")),
        "media": len(root.findall(".//" + Q["a"] + "videoFile")) + len(root.findall(".//" + Q["a"] + "audioFile"))
                 + len(root.findall(".//{http://schemas.microsoft.com/office/powerpoint/2010/main}media")),
    }
    runs = [t.text or "" for t in root.iter(Q["a"] + "t")]
    paras = 0
    for p in root.iter(Q["a"] + "p"):
        if any((t.text or "").strip() for t in p.iter(Q["a"] + "t")):
            paras += 1
    m["text_paragraphs"] = paras
    m["text_runs"] = len(runs)
    text = " ".join(runs)
    m["text_chars"] = len(re.sub(r"\s", "", text))
    timing = root.find(Q["p"] + "timing")
    m["has_timing"] = int(timing is not None)
    m["anim_effects"] = 0 if timing is None else sum(1 for c in timing.iter(Q["p"] + "cTn") if c.get("presetClass"))
    return m, text


def scan_deck(data, library, deck_id, source_file, id_prefix, max_bytes):
    rows, err = [], None
    digest = sha256(data)
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        order, cx, cy = slide_order(z)
    except (zipfile.BadZipFile, KeyError, etree.XMLSyntaxError) as e:
        return [], digest, f"{type(e).__name__}: {e}"
    names = set(z.namelist())
    for page, part in order:
        if part not in names:
            continue
        info = z.getinfo(part)
        base = {"slide_id": f"{id_prefix}-{page:04d}", "library": library, "deck_id": deck_id,
                "source_file": source_file, "source_sha256": digest, "page": page, "slide_part": part,
                "slide_xml_bytes": info.file_size, "slide_width_emu": cx, "slide_height_emu": cy,
                "aspect": aspect(cx, cy), "status": "source-candidate"}
        if info.file_size > max_bytes:
            base.update(parse_status="unparsed", slide_xml_sha256="",
                        unparsed_reason=f"slide XML {info.file_size / 1e6:.1f} MB exceeds {max_bytes / 1e6:.0f} MB parse limit",
                        category_auto="unparsed", category_basis="not parsed")
            rows.append(base)
            continue
        xml = z.read(part)
        base["slide_xml_sha256"] = sha256(xml)
        try:
            m, text = measure(xml)
        except etree.XMLSyntaxError as e:
            base.update(parse_status="unparsed", unparsed_reason=f"XML syntax error: {e}"[:200],
                        category_auto="unparsed", category_basis="not parsed")
            rows.append(base)
            continue
        cat, basis = categorise(m, text)
        base.update(m, parse_status="parsed", unparsed_reason="", category_auto=cat, category_basis=basis)
        rows.append(base)
    return rows, digest, err


def aviation_entries(archive):
    def ok(i):
        n = i.filename
        leaf = n.split("/")[-1]
        return n.lower().endswith(".pptx") and "__MACOSX" not in n and not leaf.startswith("._") and not leaf.startswith("~$")
    return sorted((i for i in archive.infolist() if ok(i)), key=lambda i: i.filename)


def build(big_deck, aviation_zip, out_dir, max_mb=8.0):
    max_bytes = int(max_mb * 1_000_000)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    rows, decks, deck_errors = [], [], []
    sources = {}
    if big_deck:
        data = Path(big_deck).read_bytes()
        r, digest, err = scan_deck(data, "500pages", "PMLD", Path(big_deck).name, "PMLD", max_bytes)
        rows += r; sources[Path(big_deck).name] = digest
        decks.append({"deck_id": "PMLD", "source_file": Path(big_deck).name, "sha256": digest, "slides": len(r)})
        if err: deck_errors.append({"deck_id": "PMLD", "error": err})
    if aviation_zip:
        zname = Path(aviation_zip).name
        sources[zname] = sha256(Path(aviation_zip).read_bytes())
        with zipfile.ZipFile(aviation_zip) as archive:
            for i, item in enumerate(aviation_entries(archive), 1):
                did = f"AVI-{i:03d}"
                src = f"{zname}!/{item.filename}"
                r, digest, err = scan_deck(archive.read(item), "aviation", did, src, did, max_bytes)
                rows += r
                decks.append({"deck_id": did, "source_file": src, "sha256": digest, "slides": len(r)})
                if err: deck_errors.append({"deck_id": did, "source_file": src, "error": err})
    with (out_dir / "source-slides.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in FIELDS})
    parsed = [r for r in rows if r["parse_status"] == "parsed"]
    summary = {
        "generator": f"build-source-catalog.py {VERSION}",
        "parse_limit_mb": max_mb,
        "sources": sources,
        "slides_total": len(rows),
        "by_library": dict(sorted(Counter(r["library"] for r in rows).items())),
        "decks_total": len(decks),
        "parsed": len(parsed),
        "unparsed": [{"slide_id": r["slide_id"], "source_file": r["source_file"], "page": r["page"],
                      "slide_xml_bytes": r["slide_xml_bytes"], "reason": r["unparsed_reason"]}
                     for r in rows if r["parse_status"] != "parsed"],
        "deck_errors": deck_errors,
        "aspect_ratios": dict(sorted(Counter(r["aspect"] for r in rows).items())),
        "categories": dict(sorted(Counter(r["category_auto"] for r in rows).items())),
        "with_charts": sum(1 for r in parsed if r["charts"]),
        "with_tables": sum(1 for r in parsed if r["tables"]),
        "with_smartart": sum(1 for r in parsed if r["smartart"]),
        "with_timing": sum(1 for r in parsed if r["has_timing"]),
        "with_media": sum(1 for r in parsed if r["media"]),
        "status": {"source-candidate": len(rows)},
        "notes": [
            "Structural catalog only; no thumbnails and no slide text are stored.",
            "Categories are heuristics from slide XML content, never from file names.",
            "Every row is source-candidate; p:timing presence is not proof that an animation plays correctly.",
            "Third-party logos / watermarks / licence marks are not detected automatically; keep them when reusing.",
        ],
        "decks": decks,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return summary


def main(argv=None):
    here = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--big-deck", default=str(here / "source-library" / "500頁.pptx"))
    p.add_argument("--aviation-zip", default=str(here / "source-library" / "Aviation Slides.zip"))
    p.add_argument("--output", default=str(here / "catalog" / "generated"))
    p.add_argument("--max-xml-mb", type=float, default=8.0, help="slide XML above this size is recorded as unparsed")
    a = p.parse_args(argv)
    for src in (a.big_deck, a.aviation_zip):
        if src and Path(src).stat().st_size < 1000:
            sys.exit(f"{src} looks like a Git LFS pointer; run `git lfs pull` first")
    s = build(a.big_deck, a.aviation_zip, a.output, a.max_xml_mb)
    print(f"slides={s['slides_total']} decks={s['decks_total']} parsed={s['parsed']} unparsed={len(s['unparsed'])} "
          f"deck_errors={len(s['deck_errors'])} -> {a.output}")


if __name__ == "__main__":
    main()
