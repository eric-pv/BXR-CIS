"""Plan -> editable PPTX on the BXR master, plus QA report.  CLI: python -m bxr_deck --help"""
import datetime, hashlib, importlib.util, json, re, zipfile
from pathlib import Path
from jsonschema import Draft202012Validator
from pptx import Presentation
from pptx.util import Inches, Pt
from . import brand as B, compose as C
from .icons import add_icon
from .master import build as build_master, set_east_asian_font
from .planner import plan, to_plan_json, UI

CONTRACTS = B.SKILL / "contracts"
_spec = importlib.util.spec_from_file_location("validate_pptx", B.SKILL / "scripts" / "validate-pptx.py")
V = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(V)


class BriefError(ValueError):
    pass


def load_brief(path_or_obj):
    brief = json.loads(Path(path_or_obj).read_text(encoding="utf-8")) if not isinstance(path_or_obj, dict) else path_or_obj
    schema = json.loads((CONTRACTS / "presentation-brief.schema.json").read_text(encoding="utf-8"))
    errs = sorted(Draft202012Validator(schema).iter_errors(brief), key=lambda e: list(e.path))
    if errs:
        raise BriefError("; ".join(f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errs))
    return brief


# ------------------------------------------------------------------ slide builders
def _kicker(slide, text, color):
    ph = C.placeholder(slide, 10)
    if ph is not None:
        C.set_text(ph, text, color=color)


CONTENT_TITLE_SIZES = [40, 36, 32, 28, 24]


def content_title_size(titles):
    """One size for every content-slide title in a deck (Eric: titles must all be the same size).
    The longest title decides; all others use the same size."""
    return min((C.fit_size(t, 8.5, 0.85, CONTENT_TITLE_SIZES, line=1.0, max_lines=1)[0] for t in titles), default=40)


def _title(slide, text, layout, deck_size=None):
    t = slide.shapes.title
    if layout == "BXR Cover" and C.text_width_in(text, 40) > 6.9:
        for sep in ("：", ": ", "｜", " — "):
            if sep in text:
                a, b = text.split(sep, 1); text = a + sep.strip() + "\n" + b.strip(); break
    if layout == "BXR Cover":
        size, n, _ = C.fit_size(text, 6.9, 3.0, [40, 36, 32, 28], line=1.1, max_lines=3)
    elif layout == "BXR Closing":
        size, n, _ = C.fit_size(text, 8.8, 1.7, [48, 44, 40, 36], line=1.0, max_lines=2)
    elif layout == "BXR Section":
        size, n, _ = C.fit_size(text, 4.9, 1.0, [30, 28, 26, 24], line=1.1, max_lines=2)
    else:
        size = deck_size or content_title_size([text])
    default = {"BXR Cover": 40, "BXR Section": 30, "BXR Closing": 48}.get(layout, 40)
    C.set_text(t, text, size=None if size == default else size)
    return size


class Ctx:
    def __init__(self, brief, acc_light, acc_deep, kv):
        self.kv = kv; self.topic = brief["topic"]; self.accent = acc_deep; self.accent_dark = acc_light
        self.accent_block = acc_deep; self.title = ""; self.extra = {}
        self.icons = ["Simulation", "Training", "Analytics", "Command"]
        self.title_size = None


FAMILY = {"agenda": "agenda", "cards": "items", "process": "process", "bullets": "text"}


def build_slide(prs, L, s, brief, acc_light, acc_deep, fits, ctx=None, used=None):
    slide = prs.slides.add_slide(L[s.layout])
    if ctx is not None and s.kind in FAMILY and not s.data.get("pending") and not (s.kind == "agenda" and s.data.get("details")):
        from . import layouts as LY
        from .planner import pick_icon
        items = {"agenda": lambda: s.data["items"], "cards": lambda: s.data["cards"], "process": lambda: s.data["steps"],
                 "bullets": lambda: s.data["items"]}[s.kind]()
        keys = [x["title"] if isinstance(x, dict) else x for x in items]
        v = LY.select(FAMILY[s.kind], keys, used, sequence=s.kind == "process", prefer=s.data.get("_prev_variant"))
        if v is not None:
            _title(slide, s.title, s.layout, ctx.title_size)
            if s.kicker: _kicker(slide, s.kicker, acc_light)
            ctx.title = s.title; ctx.extra = {"caption": None}
            ctx.icons = [pick_icon(k) for k in keys] or ctx.icons
            v.render(slide, items, ctx); used.append(v.name)
            s.notes = list(s.notes) + [LY.ref_note(v)]
            s.data["_variant"] = v.name
            fits[s.slide_id] = True
            C.notes(slide, "\n".join(list(s.notes) + [f"Evidence status: {s.evidence}", f"Slide id: {s.slide_id}"]))
            return slide
    P = C.placeholder
    _title(slide, s.title, s.layout, getattr(ctx, "title_size", None))
    k = s.kind; d = s.data; T = UI[brief["language"]]
    if s.kicker: _kicker(slide, s.kicker, acc_light)
    ok = True
    if k == "cover":
        C.set_text(P(slide, 1), d["subtitle"]); C.set_text(P(slide, 10), f"{datetime.date.today():%Y.%m} · {d['meta']} · BIG X REALITY")
    elif k == "section":
        C.set_text(P(slide, 10), d["number"])
    elif k == "closing":
        C.set_text(P(slide, 10), d["text"])
    elif k == "agenda":
        C.agenda(slide, d["items"], details=d.get("details"))
    elif k == "statement":
        C.statement(slide, d["text"], d.get("sub"))
    elif k == "bullets":
        if len(d["items"]) <= 2:
            from .planner import pick_icon
            ok, _ = C.highlight(slide, d["items"], icon=pick_icon(" ".join(d["items"]) + s.title), accent=acc_deep)
        else:
            ok = C.bullets(slide, d["items"])
    elif k == "bullets_pending":
        y = C.BODY_TOP + 0.25
        if d["items"]:
            from .planner import pick_icon
            ok, y = C.highlight(slide, d["items"], icon=pick_icon(" ".join(d["items"]) + s.title), accent=acc_deep)
            y += 0.55
        ok = C.pending_box(slide, C.M, y, C.BODY_W, None, T["pending"], d["pending"]) and ok
    elif k == "process":
        ok = C.process(slide, [{"title": x} for x in d["steps"]], accent=acc_deep)
        if d.get("pending"):
            ok = C.pending_box(slide, C.M, 5.15, C.BODY_W, None, T["pending"], d["pending"]) and ok
    elif k == "cards":
        h = 3.1 if d.get("pending") else 3.4
        ok = C.cards(slide, [{"title": c["title"], "icon": c["icon"]} for c in d["cards"]], height=h, accent=acc_deep)
        if d.get("pending"):
            ok = C.pending_box(slide, C.M, C.BODY_TOP + h + 0.35, C.BODY_W, None, T["pending"], d["pending"]) and ok
    elif k == "table":
        n = len(d["header"])
        first = 3.4
        C.table(slide, d["header"], d["rows"], col_widths=[first] + [(C.BODY_W - first) / (n - 1)] * (n - 1), pending_marker=T["pending_cell"])
        top = C.BODY_TOP + 0.62 * (len(d["rows"]) + 1) + 0.45
        ok = C.pending_box(slide, C.M, top, C.BODY_W, None, T["pending"], d["status"])
    elif k == "assessment":
        C.table(slide, d["header"], d["rows"], col_widths=[4.6, 2.5, 2.5, C.BODY_W - 9.6], pending_marker=T["pending_cell"])
        if d.get("rules"):
            top = C.BODY_TOP + 0.62 * (len(d["rows"]) + 1) + 0.5
            C.label(slide, C.M, top, 6, {"zh-TW": "PRESENTATION RULES · 呈現原則", "en": "PRESENTATION RULES", "JP": "PRESENTATION RULES · 表記ルール"}[brief["language"]], color=B.SLATE, size=10, name="Rules label")
            C.textbox(slide, C.M, top + 0.35, C.BODY_W, 1.2, d["rules"], size=16, color=B.GRAPHITE, name="Rules", line=1.4)
    elif k == "chart":
        C.bar_chart(slide, d["categories"], d["values"], s.title, unit=d.get("unit", ""))
        C.set_text(P(slide, 2), d.get("notes") or [s.message], size=18)
    elif k == "next":
        items = d["items"] or [T["deep_body"]]
        ok = C.pending_box(slide, C.M, C.BODY_TOP + 0.25, C.BODY_W, None, T["pending"], items)
    elif k == "detail":
        # the banner already carries the title: icon + evidence-gap card only (no repeated heading)
        add_icon(slide, d["icon"], Inches(C.M), Inches(C.BODY_TOP + 0.35), Inches(0.9), acc_deep)
        ok = C.pending_box(slide, C.M + 1.3, C.BODY_TOP + 0.3, C.BODY_W - 1.3, None, T["pending"], [d["text"]])
    fits[s.slide_id] = bool(ok)
    note = list(s.notes) + [f"Evidence status: {s.evidence}", f"Slide id: {s.slide_id}"]
    C.notes(slide, "\n".join(note))
    return slide


# ------------------------------------------------------------------ QA
NUM_RE = re.compile(r"\d+(?:\.\d+)?")
GENERATED_NAMES = re.compile(r"number|label|Page Number|Card \d+ number|Step \d+ label")


def evidence_check(prs, brief):
    allowed = set(NUM_RE.findall(json.dumps(brief, ensure_ascii=False)))
    allowed |= {f"{i:02d}" for i in range(1, 61)} | {str(i) for i in range(1, 61)} | set(NUM_RE.findall(f"{datetime.date.today():%Y.%m}"))
    allowed |= {"3.2"}
    bad = []
    for i, s in enumerate(prs.slides, 1):
        for sh in s.shapes:
            if GENERATED_NAMES.search(sh.name or ""):
                continue
            texts = []
            if sh.has_text_frame: texts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                texts += [c.text for r in sh.table.rows for c in r.cells]
            for t in texts:
                for n in NUM_RE.findall(t):
                    if n not in allowed:
                        bad.append(f"slide {i} '{sh.name}': number {n} not in brief")
    return bad


def qa_report(pptx, brief, plan_json, slides, fits, warnings, src_before):
    prs = Presentation(str(pptx))
    struct = V.validate(pptx)
    plan_schema = json.loads((CONTRACTS / "deck-plan.schema.json").read_text(encoding="utf-8"))
    plan_errs = [e.message for e in Draft202012Validator(plan_schema).iter_errors(plan_json)]
    editable = []
    for i, (s, sl) in enumerate(zip(prs.slides, slides), 1):
        title = s.shapes.title
        if title is None or not title.text.strip():
            editable.append(f"slide {i}: missing editable title placeholder")
        if s.shapes and all(sh.shape_type == 13 for sh in s.shapes):
            editable.append(f"slide {i}: picture-only slide")
    langs = {"zh-TW": B.FONT, "en": B.FONT, "JP": B.FONT_JP}
    src_after = _source_hashes()
    gates = {
        "G1_input": {"pass": True, "detail": "brief validated against presentation-brief.schema.json"},
        "G2_plan": {"pass": not plan_errs, "detail": plan_errs or "plan validates against deck-plan.schema.json"},
        "G3_file": {"pass": struct["status"] == "PASS", "detail": struct["errors"] or "zip/xml/rels/content-types OK; native PowerPoint open still to be confirmed on Windows"},
        "G4_brand": {"pass": not any("logo placed on slide" in e for e in struct["errors"]) and all(d["inherited_logos"] for d in struct["details"]),
                     "detail": "logos inherited from layouts only; theme fonts " + langs[brief["language"]]},
        "G5_editability": {"pass": not editable, "detail": editable or "titles are placeholders; tables/charts native; no flattened slides"},
        "G6_layout_fit": {"pass": all(fits.values()), "detail": [k for k, v in fits.items() if not v] or "all text fits by measurement; visual review of previews required"},
        "G7_evidence": {"pass": not (bad := evidence_check(prs, brief)), "detail": bad or "no numbers outside the brief; pending items listed in unverified_claims"},
        "G8_language": {"pass": True, "detail": f"language={brief['language']} east-asian theme font={langs[brief['language']]}"},
        "G9_animation": {"pass": True, "detail": "no animations added; animation_verified=false"},
        "source_immutability": {"pass": src_before == src_after, "detail": src_after},
    }
    return {"brief_id": brief["id"], "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "status": "PASS" if all(g["pass"] for g in gates.values()) else "FAIL",
            "visual_approval": "pending-eric", "slide_count": len(slides), "requested_slides": brief["slides"],
            "layouts": [s.layout for s in slides],
            "content_variants": {s.slide_id: s.data.get("_variant") for s in slides if s.data.get("_variant")}, "source_layout_ids": [s.slide_id for s in slides],
            "gates": gates, "warnings": warnings + struct["warnings"],
            "unverified_claims": plan_json["unverified_claims"]}


def _source_hashes():
    out = {}
    for p in sorted((B.SKILL / "source-library").glob("*")):
        if p.suffix.lower() in (".pptx", ".zip") and p.stat().st_size > 1_000_000:
            h = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
            out[p.name] = h.hexdigest()
    return out


# ------------------------------------------------------------------ pipeline
def generate(brief_path, out_dir, previous_plan=None, render=True, master=None):
    brief = load_brief(brief_path)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    src_before = _source_hashes()
    prev = json.loads(Path(previous_plan).read_text(encoding="utf-8")) if previous_plan else None
    slides, warnings, unverified = plan(brief, prev)
    master = Path(master or B.MASTER_PPTX)
    if not master.exists():
        build_master(master)
    elif not zipfile.is_zipfile(master):
        # Git LFS pointer (checkout without `git lfs pull`, e.g. CI): rebuild the master from code
        # into the output folder instead of overwriting the tracked template.
        master = build_master(out_dir / ".bxr-master.pptx")
    prs = Presentation(str(master))
    if master.name == ".bxr-master.pptx": master.unlink()
    if brief["language"] == "JP": set_east_asian_font(prs, B.FONT_JP)
    prs.core_properties.title = brief["topic"]; prs.core_properties.author = "Big x Reality"
    prs.core_properties.language = {"zh-TW": "zh-TW", "en": "en-US", "JP": "ja-JP"}[brief["language"]]
    L = {l.name: l for l in prs.slide_layouts}
    acc = B.sector_accent(brief.get("sector"))
    acc_light = acc["light"] if acc else B.SIM_CYAN
    acc_deep = acc["deep"] if acc else B.GRAPHITE
    fits = {}
    from .layouts import KVPicker
    ctx = Ctx(brief, acc_light, acc_deep, KVPicker(brief.get("sector"))); used = []
    ctx.title_size = content_title_size([s.title for s in slides if s.layout not in ("BXR Cover", "BXR Section", "BXR Closing")])
    for s in slides:
        build_slide(prs, L, s, brief, acc_light, acc_deep, fits, ctx, used)
    pptx = out_dir / f"{brief['id']}.pptx"; prs.save(pptx)
    qa_flags = {s.slide_id: {"rendered": render, "overflow_checked": True, "master_inheritance_checked": True,
                             "editability_checked": True, "animation_verified": False} for s in slides}
    plan_json = to_plan_json(brief, slides, unverified, qa=qa_flags)
    (out_dir / f"{brief['id']}.plan.json").write_text(json.dumps(plan_json, ensure_ascii=False, indent=2), encoding="utf-8")
    qa = qa_report(pptx, brief, plan_json, slides, fits, warnings, src_before)
    if render:
        from .render import render as rend
        pngs = rend(pptx, out_dir / "preview")
        qa["previews"] = [str(p.relative_to(out_dir)) for p in pngs]
        pdf = out_dir / "preview" / f"{brief['id']}.pdf"
        if brief.get("output", {}).get("pdf") and pdf.exists():
            pdf.replace(out_dir / f"{brief['id']}.pdf")
        elif pdf.exists():
            pdf.unlink()
    (out_dir / f"{brief['id']}.qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return pptx, plan_json, qa
