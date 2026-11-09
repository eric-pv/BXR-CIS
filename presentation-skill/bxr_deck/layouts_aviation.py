"""Layout families distilled from the purchased "Aviation Slides" library (source-library/Aviation Slides.zip).

The archive holds 249 infographic decks (numbered D001–D249 by sorted path). Seven families that
the 500-page reference did not cover were studied from rendered overview sheets and rebuilt here as
composition rules: compare, timeline, map, team, product, gauge, quote.

Rebuilt natively in CIS v3.2 — Command Black / Graphite / Paper, Noto Sans TC + B612 Mono, approved
BXR key visuals (06_KeyVisuals, weapon-free CORP_* set unless the deck's sector allows tactical
visuals). No pixels, logos, maps, people photos or text are taken from the purchased files, and no
logo is placed on slides (the master/layouts own the logo). `ref` names the pages each variant was
distilled from ("AVI-<deck>-<page>") for traceability only.

Interface (shared contract with the planner/generator, do not change unilaterally):
render(slide, items, ctx) — `items` is always a list (layouts.features/select read n from it);
every other field comes from ctx.extra.
  compare  items=[{"label", "values":[...]}]            extra={"columns":[...]}   n=2–8
  timeline items=[{"year", "title", "body"|None}]                                 n=3–8
  map      items=[{"name", "body"|None}]                                          n=1–6
  team     items=[{"role", "name"|None, "body"|None}]   (name=None → role only)   n=2–6
  product  items=[{"title", "body"|None}]               extra={"name"}            n=2–6
  gauge    items=[{"label", "value", "max", "unit"}]    extra={"notes":[...]}     n=1–4
  quote    items=[str]                                  extra={"attribution"}     n=1–2
Numbers shown by gauge come only from the brief; nothing here invents values or names."""
from lxml import etree
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt
from . import brand as B
from . import compose as C
from .icons import add_icon
from .layouts import variant, KVPicker, picture, oval_picture  # noqa: F401  (KVPicker re-exported for callers)

M, W = C.M, C.BODY_W
TOP, BOT = 1.42, 6.66            # content zone: below the banner (1.036"), above the master footer (6.92")
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


# ------------------------------------------------------------------ helpers
def _acc(ctx):
    return getattr(ctx, "accent", None) or B.GRAPHITE


def _extra(ctx):
    return getattr(ctx, "extra", None) or {}


def _icons(ctx):
    return list(getattr(ctx, "icons", None) or ["Analytics", "Command", "Communication", "Training", "XR", "AI"])


def _pick(ctx, text):
    kv = getattr(ctx, "kv", None) or KVPicker(getattr(ctx, "sector", None))
    return kv.pick(text)


def _fit(text, w, h, sizes, line=1.25, max_lines=None):
    return C.fit_size(text, w, h, sizes, line=line, max_lines=max_lines)[0]


def _txt(slide, x, y, w, h, text, size, color=B.BLACK, **kw):
    return C.textbox(slide, x, y, w, h, text, size=size, color=color, **kw)


def _title_body(slide, x, y, w, h, title, body, name, tsizes=(20, 18, 16, 14), bsizes=(14, 13, 12),
                align=PP_ALIGN.LEFT, tcolor=B.BLACK, bcolor=B.SLATE, tlines=2):
    """Title (≤ tlines) + optional body stacked inside one box; sizes fitted to the box."""
    th_max = min(h, 0.95 if tlines > 1 else 0.5)
    ts = _fit(title, w, th_max, list(tsizes), line=1.2, max_lines=tlines)
    nl = min(tlines, C.wrap_lines(title, ts, w))
    th = nl * ts * 1.2 / 72 + 0.04
    _txt(slide, x, y, w, th, title, ts, tcolor, align=align, name=f"{name} title", line=1.1)
    if body:
        room = h - th - 0.12
        if room > 0.25:
            bs = _fit(body, w, room, list(bsizes), line=1.4)
            _txt(slide, x, y + th + 0.12, w, room, body, bs, bcolor, align=align, name=f"{name} text", line=1.35)


def _arc(slide, x, y, d, start, end, fill, thick=18000, name=None):
    """Native BLOCK_ARC from `start` to `end` degrees (clockwise from 3 o'clock); thickness in 1/100000 of d."""
    s = slide.shapes.add_shape(MSO_SHAPE.BLOCK_ARC, Inches(x), Inches(y), Inches(d), Inches(d))
    C._clean(s, fill)
    if name: s.name = name
    geom = s._element.spPr.find(f"{{{A_NS}}}prstGeom")
    av = geom.find(f"{{{A_NS}}}avLst")
    if av is None: av = etree.SubElement(geom, f"{{{A_NS}}}avLst")
    for g in list(av): av.remove(g)
    for nm, v in (("adj1", int(start % 360 * 60000)), ("adj2", int(end % 360 * 60000)), ("adj3", thick)):
        g = etree.SubElement(av, f"{{{A_NS}}}gd"); g.set("name", nm); g.set("fmla", f"val {v}")
    return s


def _ratio(it):
    try:
        v, mx = float(it["value"]), float(it["max"])
    except (KeyError, TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, v / mx)) if mx > 0 else 0.0


def _num(v):
    try: return f"{float(v):g}"
    except (TypeError, ValueError): return str(v)


def _value_text(it):
    u = it.get("unit") or ""
    return _num(it.get("value")) + ("" if not u else (u if u in ("%", "‰") else f" {u}"))


def _notes(slide, ctx, y=BOT - 0.38):
    notes = [n for n in (_extra(ctx).get("notes") or []) if n]
    if notes:
        t = "　".join(notes)
        _txt(slide, M, y, W, 0.36, t, _fit(t, W, 0.36, [12, 11, 10], max_lines=1), B.SLATE, name="Source note")
        return True
    return False


ROLE_ICONS = (("lead 主管 負責 經理 director manager pm 計畫 総括 責任", "Command"),
              ("engineer 工程 開發 developer 技術 エンジニア 研發", "AI"),
              ("design 設計 美術 ux デザイン", "XR"),
              ("train 訓練 教官 instructor 講師 研修", "Training"),
              ("data 數據 分析 analyst データ 品質 qa", "Analytics"),
              ("sales 業務 客戶 support 支援 窗口 営業 sim", "Communication"))


def _role_icon(role, i, ctx):
    t = (role or "").lower()
    for keys, icon in ROLE_ICONS:
        if any(k in t for k in keys.split()):
            return icon
    ic = _icons(ctx)
    return ic[i % len(ic)]


# ================================================================== COMPARE family
def _cmp_cells(items, columns):
    k = len(columns)
    return [(it.get("label", ""), [(list(it.get("values") or []) + [""] * k)[j] for j in range(k)]) for it in items]


@variant("compare.table", "compare", ("AVI-D064-18", "AVI-D064-19", "AVI-D063-14"), 2, 8)
def compare_table(slide, items, ctx):
    """Native table: criteria rows × option columns, Graphite header (ref D064-18/19)."""
    cols = list(_extra(ctx).get("columns") or [])
    rows = _cmp_cells(items, cols)
    lw = min(3.6, max(2.4, W * 0.28))
    widths = [lw] + [(W - lw) / max(1, len(cols))] * len(cols)
    head = [_extra(ctx).get("label_header", "")] + cols
    gf = C.table(slide, head, [[lab] + vals for lab, vals in rows], top=TOP + 0.08, col_widths=widths, name="Comparison table")
    n = len(rows) + 1
    rh = min(0.62, (BOT - TOP - 0.2) / n)
    if rh < 0.62:   # many rows: shrink type so the rows keep their height
        for r in gf.table.rows:
            for cell in r.cells:
                for p in cell.text_frame.paragraphs:
                    for run in p.runs: run.font.size = Pt(13)
    return gf


@variant("compare.split-panels", "compare", ("AVI-D064-12", "AVI-D063-08", "AVI-D064-07"), 2, 6)
def compare_panels(slide, items, ctx):
    """Option columns as panels with dark headers; each criterion is a labelled row (ref D064-12/D063-08)."""
    cols = list(_extra(ctx).get("columns") or [])
    if not 2 <= len(cols) <= 4:
        return compare_table(slide, items, ctx)
    rows = _cmp_cells(items, cols)
    k = len(cols); gap = 0.3; pw = (W - gap * (k - 1)) / k
    head_h = 0.78; y0 = TOP + 0.08
    rh = (BOT - y0 - head_h - 0.15) / len(rows)
    for j, col in enumerate(cols):
        x = M + j * (pw + gap)
        C.rect(slide, x, y0, pw, BOT - y0, fill=B.PAPER, name=f"Panel {j + 1}")
        C.rect(slide, x, y0, pw, head_h, fill=B.BLACK if j % 2 == 0 else B.GRAPHITE, name=f"Panel {j + 1} header")
        C.label(slide, x + 0.3, y0 + 0.1, pw - 0.6, f"OPTION {j + 1:02d}", color=B.MIST, size=9, name=f"Panel {j + 1} label")
        _txt(slide, x + 0.3, y0 + 0.32, pw - 0.6, 0.42, col, _fit(col, pw - 0.6, 0.42, [20, 18, 16, 14], max_lines=1), B.WHITE,
             anchor=MSO_ANCHOR.MIDDLE, name=f"Panel {j + 1} title")
        for i, (lab, vals) in enumerate(rows):
            y = y0 + head_h + 0.1 + i * rh
            if i: C.hline(slide, x + 0.3, y, pw - 0.6, name=f"Panel {j + 1} rule {i}")
            C.label(slide, x + 0.3, y + 0.1, pw - 0.6, lab[:40], color=B.SLATE, size=9, name=f"Panel {j + 1} row {i + 1} label")
            v = vals[j]
            if v:
                vh = rh - 0.42
                _txt(slide, x + 0.3, y + 0.36, pw - 0.6, vh, v, _fit(v, pw - 0.6, vh, [18, 16, 15, 14, 13, 12], line=1.3), B.BLACK,
                     name=f"Panel {j + 1} row {i + 1} value", line=1.25)


@variant("compare.center-axis", "compare", ("AVI-D064-17", "AVI-D064-11", "AVI-D064-14"), 2, 6, prefers="short")
def compare_axis(slide, items, ctx):
    """Two options mirrored around a central criteria spine with a VS marker (ref D064-17/D064-11)."""
    cols = list(_extra(ctx).get("columns") or [])
    if len(cols) != 2:
        return compare_panels(slide, items, ctx)
    rows = _cmp_cells(items, cols)
    cx = M + W / 2; spine_w = 2.6; side_w = (W - spine_w) / 2 - 0.35
    y0 = TOP + 0.05
    for j, col in enumerate(cols):
        x = M if j == 0 else cx + spine_w / 2 + 0.35
        _txt(slide, x, y0, side_w, 0.6, col, _fit(col, side_w, 0.6, [26, 24, 22, 20, 18], max_lines=1), B.BLACK,
             align=PP_ALIGN.RIGHT if j == 0 else PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE, name=f"Option {j + 1} title")
        C.rect(slide, x if j else x + side_w - 1.2, y0 + 0.7, 1.2, 0.05, fill=_acc(ctx) if j == 0 else B.GRAPHITE, name=f"Option {j + 1} rule")
    vs = C.rect(slide, cx - 0.42, y0 - 0.05, 0.84, 0.84, fill=B.BLACK, name="VS marker", shape=MSO_SHAPE.OVAL)
    _txt(slide, cx - 0.42, y0 - 0.05, 0.84, 0.84, "VS", 18, B.WHITE, font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name="VS text")
    ry0 = y0 + 1.1; rh = (BOT - ry0) / len(rows)
    C.rect(slide, cx - 0.015, ry0, 0.03, BOT - ry0, fill=B.LINE, name="Spine")
    for i, (lab, vals) in enumerate(rows):
        y = ry0 + i * rh; ph = min(0.56, rh - 0.18)
        pill = C.rect(slide, cx - spine_w / 2, y + (rh - ph) / 2, spine_w, ph, fill=B.GRAPHITE, name=f"Criterion {i + 1} pill", shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        pill.adjustments[0] = 0.5
        _txt(slide, cx - spine_w / 2 + 0.15, y + (rh - ph) / 2, spine_w - 0.3, ph, lab, _fit(lab, spine_w - 0.3, ph, [15, 14, 13, 12], max_lines=1),
             B.WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Criterion {i + 1}")
        for j in range(2):
            x = M if j == 0 else cx + spine_w / 2 + 0.35
            v = vals[j]
            if v:
                _txt(slide, x, y + 0.06, side_w, rh - 0.12, v, _fit(v, side_w, rh - 0.12, [18, 16, 15, 14, 13, 12], line=1.3), B.BLACK,
                     align=PP_ALIGN.RIGHT if j == 0 else PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE, name=f"Option {j + 1} row {i + 1}", line=1.25)


# ================================================================== TIMELINE family
@variant("timeline.horizontal", "timeline", ("AVI-D224-05", "AVI-D224-17", "AVI-D155-10"), 3, 8, prefers="sequence")
def timeline_horizontal(slide, items, ctx):
    """Axis with nodes; year numerals above, milestone title and text below (ref D224-05/D155-10)."""
    n = len(items); w = W / n; ay = TOP + 1.35
    C.hline(slide, M, ay, W, color=B.MIST, weight=1.5, name="Timeline axis")
    for i, it in enumerate(items):
        x = M + i * w; cx = x + w / 2
        yr = str(it.get("year", ""))
        _txt(slide, x + 0.1, TOP + 0.15, w - 0.2, 0.75, yr, _fit(yr, w - 0.2, 0.75, [32, 28, 24, 20, 18], max_lines=1),
             B.TEXT_RED if i == n - 1 else B.BLACK, font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM, name=f"Milestone {i + 1} year")
        C.rect(slide, cx - 0.13, ay - 0.13, 0.26, 0.26, fill=_acc(ctx) if i == n - 1 else B.WHITE, line=_acc(ctx), line_w=1.75,
               name=f"Milestone {i + 1} node", shape=MSO_SHAPE.OVAL)
        C.hline(slide, cx, ay + 0.2, 0.0001, name=f"Milestone {i + 1} tick")
        _title_body(slide, x + 0.12, ay + 0.45, w - 0.24, BOT - ay - 0.5, it.get("title", ""), it.get("body"),
                    f"Milestone {i + 1}", align=PP_ALIGN.CENTER,
                    tsizes=(20, 18, 16, 14) if n <= 5 else (16, 15, 14, 13), bsizes=(14, 13, 12) if n <= 5 else (12, 11))


@variant("timeline.alternating", "timeline", ("AVI-D224-13", "AVI-D224-15", "AVI-D155-13"), 4, 8, prefers="sequence")
def timeline_alternating(slide, items, ctx):
    """Central year band; milestones alternate above and below it (ref D224-13/D224-15/D155-13)."""
    n = len(items); w = W / n; bh = 0.56; by = (TOP + BOT) / 2 - bh / 2
    for i, it in enumerate(items):
        x = M + i * w
        seg = C.rect(slide, x, by, w + (0.001 if i < n - 1 else 0), bh, fill=B.BLACK if i % 2 == 0 else B.GRAPHITE, name=f"Year band {i + 1}")
        yr = str(it.get("year", ""))
        _txt(slide, x + 0.08, by, w - 0.16, bh, yr, _fit(yr, w - 0.16, bh - 0.1, [20, 18, 16, 14], max_lines=1), B.WHITE,
             font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Milestone {i + 1} year")
        up = i % 2 == 0; cx = x + w / 2
        bw = min(2 * w - 0.3, 3.2, 2 * (cx - M), 2 * (M + W - cx))   # same-side neighbours are 2w apart
        bx = cx - bw / 2
        if up:
            C.hline(slide, cx, by - 0.32, 0.0001, name=f"Milestone {i + 1} stem")
            C.rect(slide, cx - 0.06, by - 0.2, 0.12, 0.12, fill=_acc(ctx), name=f"Milestone {i + 1} marker", shape=MSO_SHAPE.DIAMOND)
            box_y, box_h = TOP + 0.1, by - 0.35 - TOP - 0.1
        else:
            C.rect(slide, cx - 0.06, by + bh + 0.08, 0.12, 0.12, fill=_acc(ctx), name=f"Milestone {i + 1} marker", shape=MSO_SHAPE.DIAMOND)
            box_y, box_h = by + bh + 0.35, BOT - (by + bh + 0.35)
        _title_body(slide, bx, box_y, bw, box_h, it.get("title", ""), it.get("body"), f"Milestone {i + 1}", align=PP_ALIGN.CENTER,
                    tsizes=(18, 16, 15, 14), bsizes=(13, 12, 11))


@variant("timeline.vertical-visual", "timeline", ("AVI-D224-14", "AVI-D224-20", "AVI-D155-08"), 3, 6, needs_image=True, prefers="sequence")
def timeline_vertical(slide, items, ctx):
    """Key visual on the left; vertical spine with year, title and text per milestone (ref D224-20/D155-08)."""
    pw = 4.2
    picture(slide, _pick(ctx, getattr(ctx, "title", "") + " " + " ".join(i.get("title", "") for i in items)), M, TOP + 0.05, pw, BOT - TOP - 0.05, name="Timeline visual")
    n = len(items); sx = M + pw + 0.7; rh = (BOT - TOP - 0.1) / n
    C.rect(slide, sx - 0.01, TOP + 0.05 + rh / 2 - 0.2, 0.02, rh * (n - 1) + 0.4, fill=B.LINE, name="Timeline spine")
    yw = 1.35; tx = sx + 0.35 + yw; tw = M + W - tx
    for i, it in enumerate(items):
        y = TOP + 0.05 + i * rh; cy = y + rh / 2
        C.rect(slide, sx - 0.12, cy - 0.12, 0.24, 0.24, fill=_acc(ctx) if i == n - 1 else B.WHITE, line=_acc(ctx), line_w=1.75,
               name=f"Milestone {i + 1} node", shape=MSO_SHAPE.OVAL)
        yr = str(it.get("year", ""))
        _txt(slide, sx + 0.3, y, yw, rh, yr, _fit(yr, yw, 0.5, [22, 20, 18, 16, 14], max_lines=1), B.TEXT_RED if i == n - 1 else B.BLACK,
             font=B.MONO, anchor=MSO_ANCHOR.MIDDLE, name=f"Milestone {i + 1} year")
        body = it.get("body")
        title = it.get("title", "")
        ts = _fit(title, tw, 0.45, [20, 18, 16, 14], max_lines=1)
        bh = rh - 0.62
        if body and bh > 0.25:
            _txt(slide, tx, y + 0.1, tw, 0.45, title, ts, B.BLACK, anchor=MSO_ANCHOR.BOTTOM, name=f"Milestone {i + 1} title")
            _txt(slide, tx, y + 0.6, tw, bh, body, _fit(body, tw, bh, [14, 13, 12, 11], line=1.35), B.SLATE, name=f"Milestone {i + 1} text", line=1.3)
        else:
            _txt(slide, tx, y, tw, rh, title, ts, B.BLACK, anchor=MSO_ANCHOR.MIDDLE, name=f"Milestone {i + 1} title")
        if i < n - 1: C.hline(slide, tx, y + rh, tw, name=f"Milestone {i + 1} rule")


# ================================================================== MAP family
# No map artwork is reused (purchased map shapes are licensed pixels/vectors). Regions are shown as
# numbered markers on an approved terrain/city key visual plus a matching legend; markers are
# placeholders the author drags onto the real location.
MARKER_SPOTS = [(0.28, 0.32), (0.62, 0.22), (0.45, 0.58), (0.78, 0.55), (0.2, 0.74), (0.66, 0.82)]


def _marker(slide, x, y, i, ctx, d=0.46):
    pin = C.rect(slide, x - d / 2, y - d / 2, d, d, fill=B.BLACK, line=B.WHITE, line_w=1.5, name=f"Region {i + 1} marker (move to location)", shape=MSO_SHAPE.OVAL)
    _txt(slide, x - d / 2, y - d / 2, d, d, f"{i + 1:02d}", 12, B.WHITE, font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Region {i + 1} marker number")
    return pin


@variant("map.visual-markers", "map", ("AVI-D019-04", "AVI-D249-08", "AVI-D019-12"), 1, 6, needs_image=True)
def map_markers(slide, items, ctx):
    """Large terrain visual with numbered region markers, legend list on the right (ref D019-04/D019-12)."""
    pw = 7.0; ph = BOT - TOP - 0.05
    picture(slide, _pick(ctx, "map 地圖 terrain uav " + getattr(ctx, "title", "")), M, TOP + 0.05, pw, ph, name="Map visual")
    for i, _ in enumerate(items):
        fx, fy = MARKER_SPOTS[i]
        _marker(slide, M + fx * pw, TOP + 0.05 + fy * ph, i, ctx)
    n = len(items); lx = M + pw + 0.5; lw = M + W - lx
    rh = min(1.6, (BOT - TOP - 0.1) / n); y0 = TOP + 0.05 + (BOT - TOP - 0.1 - rh * n) / 2
    for i, it in enumerate(items):
        y = y0 + i * rh
        C.rect(slide, lx, y + 0.06, 0.4, 0.4, fill=B.BLACK, name=f"Region {i + 1} legend chip", shape=MSO_SHAPE.OVAL)
        _txt(slide, lx, y + 0.06, 0.4, 0.4, f"{i + 1:02d}", 11, B.WHITE, font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Region {i + 1} legend number")
        _title_body(slide, lx + 0.6, y + 0.06, lw - 0.6, rh - 0.18, it.get("name", ""), it.get("body"), f"Region {i + 1}",
                    tsizes=(20, 18, 16), bsizes=(14, 13, 12, 11), tlines=1)
        if i < n - 1: C.hline(slide, lx + 0.6, y + rh - 0.06, lw - 0.6, name=f"Region {i + 1} rule")


@variant("map.region-cards", "map", ("AVI-D019-17", "AVI-D019-11", "AVI-D019-07"), 1, 6, needs_image=True)
def map_cards(slide, items, ctx):
    """Visual band with markers; one card per region below, tied by number (ref D019-17/D019-07)."""
    bh = 2.25; by = TOP + 0.05
    picture(slide, _pick(ctx, "city 城市 terrain map " + getattr(ctx, "title", "")), M, by, W, bh, name="Map visual band")
    n = len(items); gap = 0.24; cw = (W - gap * (n - 1)) / n
    for i, it in enumerate(items):
        x = M + i * (cw + gap)
        _marker(slide, x + cw / 2, by + bh * (0.35 + 0.3 * (i % 2)), i, ctx, d=0.42)
        cy = by + bh + 0.25
        C.rect(slide, x, cy, cw, BOT - cy, fill=B.PAPER, name=f"Region {i + 1} card")
        C.rect(slide, x, cy, cw, 0.05, fill=_acc(ctx) if i == 0 else B.GRAPHITE, name=f"Region {i + 1} card accent")
        C.label(slide, x + 0.25, cy + 0.25, cw - 0.5, f"REGION {i + 1:02d}", color=B.SLATE, size=9, name=f"Region {i + 1} label")
        _title_body(slide, x + 0.25, cy + 0.6, cw - 0.5, BOT - cy - 0.8, it.get("name", ""), it.get("body"), f"Region {i + 1}",
                    tsizes=(20, 18, 16, 14) if n <= 4 else (16, 15, 14), bsizes=(14, 13, 12) if n <= 4 else (12, 11))


# ================================================================== TEAM family
# Roles are shown with official BXR icons — never stock portraits — and names only when the brief
# provides them (name=None → role only).
@variant("team.cards", "team", ("AVI-D215-15", "AVI-D215-20", "AVI-D215-03"), 2, 6)
def team_cards(slide, items, ctx):
    """Equal role cards: icon medallion, role, optional name and remit (ref D215-15/D215-20)."""
    n = len(items); gap = 0.26; cw = (W - gap * (n - 1)) / n
    y0 = TOP + 0.1
    for i, it in enumerate(items):
        x = M + i * (cw + gap)
        C.rect(slide, x, y0, cw, BOT - y0, fill=B.PAPER, name=f"Role {i + 1} card")
        d = 1.1 if n <= 4 else 0.9
        C.rect(slide, x + (cw - d) / 2, y0 + 0.4, d, d, fill=B.BLACK if i % 2 == 0 else B.GRAPHITE, name=f"Role {i + 1} medallion", shape=MSO_SHAPE.OVAL)
        add_icon(slide, _role_icon(it.get("role"), i, ctx), Inches(x + cw / 2 - d * 0.25), Inches(y0 + 0.4 + d * 0.25), Inches(d * 0.5), B.WHITE)
        y = y0 + 0.4 + d + 0.3
        role = it.get("role", "")
        rs = _fit(role, cw - 0.4, 0.8, [20, 18, 16, 14], max_lines=2)
        _txt(slide, x + 0.2, y, cw - 0.4, 0.8, role, rs, B.BLACK, align=PP_ALIGN.CENTER, name=f"Role {i + 1} title", line=1.1)
        y += 0.85
        C.rect(slide, x + cw / 2 - 0.25, y, 0.5, 0.04, fill=_acc(ctx), name=f"Role {i + 1} rule")
        y += 0.2
        if it.get("name"):
            _txt(slide, x + 0.2, y, cw - 0.4, 0.4, it["name"], _fit(it["name"], cw - 0.4, 0.4, [14, 13, 12], max_lines=1), B.SLATE,
                 align=PP_ALIGN.CENTER, name=f"Role {i + 1} name")
            y += 0.45
        if it.get("body"):
            room = BOT - y - 0.25
            _txt(slide, x + 0.25, y, cw - 0.5, room, it["body"], _fit(it["body"], cw - 0.5, room, [14, 13, 12, 11], line=1.35), B.SLATE,
                 align=PP_ALIGN.CENTER, name=f"Role {i + 1} text", line=1.3)


@variant("team.lead-tree", "team", ("AVI-D215-19", "AVI-D215-04", "AVI-D177-01"), 3, 6)
def team_tree(slide, items, ctx):
    """First role leads; the others hang from a connector bar below (org-chart reading, ref D215-19)."""
    lead, rest = items[0], items[1:]
    cx = M + W / 2; lw, lh = 4.4, 1.25; ly = TOP + 0.1
    C.rect(slide, cx - lw / 2, ly, lw, lh, fill=B.BLACK, name="Lead block")
    add_icon(slide, _role_icon(lead.get("role"), 0, ctx), Inches(cx - lw / 2 + 0.35), Inches(ly + lh / 2 - 0.3), Inches(0.6), B.WHITE)
    tx = cx - lw / 2 + 1.2; tw = lw - 1.45
    role = lead.get("role", "")
    if lead.get("name"):
        _txt(slide, tx, ly + 0.18, tw, 0.5, role, _fit(role, tw, 0.5, [22, 20, 18, 16], max_lines=1), B.WHITE, anchor=MSO_ANCHOR.BOTTOM, name="Lead role")
        _txt(slide, tx, ly + 0.72, tw, 0.36, lead["name"], 13, B.MIST, name="Lead name")
    else:
        _txt(slide, tx, ly, tw, lh, role, _fit(role, tw, lh - 0.2, [22, 20, 18, 16], max_lines=2), B.WHITE, anchor=MSO_ANCHOR.MIDDLE, name="Lead role", line=1.1)
    if lead.get("body"):
        _txt(slide, M + 1.5, ly + lh + 0.12, W - 3.0, 0.45, lead["body"], _fit(lead["body"], W - 3.0, 0.45, [14, 13, 12], max_lines=1), B.SLATE,
             align=PP_ALIGN.CENTER, name="Lead text")
    n = len(rest); gap = 0.3; cw = (W - gap * (n - 1)) / n
    bar_y = ly + lh + 0.75; cy = bar_y + 0.45
    C.hline(slide, cx, ly + lh, 0.0001, color=B.MIST, weight=1.25, name="Lead connector")
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(cx), Inches(ly + lh), Inches(cx), Inches(bar_y))
    c.line.color.rgb = C.rgb(B.MIST); c.line.width = Pt(1.25); c.name = "Lead stem"
    C.hline(slide, M + cw / 2, bar_y, W - cw, color=B.MIST, weight=1.25, name="Team bar")
    for i, it in enumerate(rest):
        x = M + i * (cw + gap); mx = x + cw / 2
        s = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(mx), Inches(bar_y), Inches(mx), Inches(cy))
        s.line.color.rgb = C.rgb(B.MIST); s.line.width = Pt(1.25); s.name = f"Role {i + 2} stem"
        C.rect(slide, x, cy, cw, BOT - cy, fill=B.PAPER, name=f"Role {i + 2} card")
        C.rect(slide, x, cy, cw, 0.05, fill=_acc(ctx), name=f"Role {i + 2} accent")
        add_icon(slide, _role_icon(it.get("role"), i + 1, ctx), Inches(x + 0.3), Inches(cy + 0.32), Inches(0.46), _acc(ctx))
        y = cy + 0.95
        role = it.get("role", "")
        _txt(slide, x + 0.3, y, cw - 0.6, 0.75, role, _fit(role, cw - 0.6, 0.75, [18, 16, 15, 14], max_lines=2), B.BLACK, name=f"Role {i + 2} title", line=1.1)
        y += 0.8
        if it.get("name"):
            _txt(slide, x + 0.3, y, cw - 0.6, 0.35, it["name"], 13, B.SLATE, name=f"Role {i + 2} name"); y += 0.42
        if it.get("body"):
            room = BOT - y - 0.2
            if room > 0.3:
                _txt(slide, x + 0.3, y, cw - 0.6, room, it["body"], _fit(it["body"], cw - 0.6, room, [13, 12, 11], line=1.35), B.SLATE,
                     name=f"Role {i + 2} text", line=1.3)


@variant("team.side-visual", "team", ("AVI-D215-13", "AVI-D215-05", "AVI-D215-16"), 2, 6, needs_image=True)
def team_side(slide, items, ctx):
    """Team key visual on the left; role tiles in a 2-column grid on the right (ref D215-13/D215-16)."""
    pw = 4.3
    picture(slide, _pick(ctx, "team 團隊 training 訓練 " + getattr(ctx, "title", "")), M, TOP + 0.05, pw, BOT - TOP - 0.05, name="Team visual")
    n = len(items); cols = 1 if n <= 3 else 2; rows = (n + cols - 1) // cols
    gx = M + pw + 0.35; gap = 0.22
    tw = (M + W - gx - gap * (cols - 1)) / cols; th = (BOT - TOP - 0.05 - gap * (rows - 1)) / rows
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x = gx + c * (tw + gap); y = TOP + 0.05 + r * (th + gap)
        dark = (r + c) % 2 == 0
        C.rect(slide, x, y, tw, th, fill=B.GRAPHITE if dark else B.PAPER, name=f"Role {i + 1} tile")
        fg = B.WHITE if dark else B.BLACK; sub = B.MIST if dark else B.SLATE
        add_icon(slide, _role_icon(it.get("role"), i, ctx), Inches(x + 0.3), Inches(y + 0.3), Inches(0.42), B.WHITE if dark else _acc(ctx))
        tx = x + 0.95; tww = tw - 1.2
        role = it.get("role", "")
        _txt(slide, tx, y + 0.22, tww, 0.55, role, _fit(role, tww, 0.55, [20, 18, 16, 14], max_lines=1), fg, anchor=MSO_ANCHOR.MIDDLE, name=f"Role {i + 1} title")
        yy = y + 0.82
        if it.get("name"):
            _txt(slide, tx, yy, tww, 0.32, it["name"], 13, sub, name=f"Role {i + 1} name"); yy += 0.38
        if it.get("body"):
            room = y + th - yy - 0.18
            if room > 0.3:
                _txt(slide, tx, yy, tww, room, it["body"], _fit(it["body"], tww, room, [14, 13, 12, 11], line=1.35), sub, name=f"Role {i + 1} text", line=1.3)


# ================================================================== PRODUCT family
def _feature_rows(slide, items, ctx, x, w, y0, y1, prefix="Feature"):
    n = len(items); rh = (y1 - y0) / n
    for i, it in enumerate(items):
        y = y0 + i * rh
        chip = C.rect(slide, x, y + 0.08, 0.62, 0.62, fill=B.BLACK if i % 2 == 0 else B.GRAPHITE, name=f"{prefix} {i + 1} chip", shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        chip.adjustments[0] = 0.18
        ic = _icons(ctx)
        add_icon(slide, ic[i % len(ic)], Inches(x + 0.15), Inches(y + 0.23), Inches(0.32), B.WHITE)
        _title_body(slide, x + 0.85, y + 0.06, w - 0.85, rh - 0.16, it.get("title", ""), it.get("body"), f"{prefix} {i + 1}",
                    tsizes=(20, 18, 16, 14), bsizes=(14, 13, 12, 11), tlines=1)
        if i < n - 1: C.hline(slide, x + 0.85, y + rh - 0.05, w - 0.85, name=f"{prefix} {i + 1} rule")


def _name_tag(slide, x, y, w, name, dark=True):
    C.rect(slide, x, y, w, 0.7, fill=B.BLACK if dark else B.WHITE, name="Product name panel")
    C.rect(slide, x, y, 0.08, 0.7, fill=B.RED, name="Product name mark")      # the one red focus on the page
    _txt(slide, x + 0.3, y, w - 0.45, 0.7, name, _fit(name, w - 0.45, 0.6, [24, 22, 20, 18, 16], max_lines=1), B.WHITE if dark else B.BLACK,
         anchor=MSO_ANCHOR.MIDDLE, name="Product name")


@variant("product.visual-left", "product", ("AVI-D161-01", "AVI-D161-12", "AVI-D161-20"), 2, 6, needs_image=True)
def product_left(slide, items, ctx):
    """Product key visual left with a name tag; feature list with icon chips on the right (ref D161-01/D161-20)."""
    name = _extra(ctx).get("name") or ""
    pw = 5.4
    picture(slide, _pick(ctx, name + " " + getattr(ctx, "title", "")), M, TOP + 0.05, pw, BOT - TOP - 0.05, name="Product visual")
    if name: _name_tag(slide, M, BOT - 0.95, min(pw - 0.5, 4.8), name)
    fx = M + pw + 0.55
    _feature_rows(slide, items, ctx, fx, M + W - fx, TOP + 0.1, BOT)


@variant("product.visual-top", "product", ("AVI-D161-10", "AVI-D161-18", "AVI-D161-11"), 2, 4, needs_image=True)
def product_top(slide, items, ctx):
    """Wide product visual band with the name panel overlapping; feature columns below (ref D161-10/D161-18)."""
    name = _extra(ctx).get("name") or ""
    bh = 2.55
    picture(slide, _pick(ctx, name + " " + getattr(ctx, "title", "")), M, TOP + 0.05, W, bh, name="Product visual band")
    if name: _name_tag(slide, M, TOP + 0.05 + bh - 0.7, 5.0, name)
    n = len(items); gap = 0.4; cw = (W - gap * (n - 1)) / n; y0 = TOP + bh + 0.4
    for i, it in enumerate(items):
        x = M + i * (cw + gap)
        ic = _icons(ctx)
        add_icon(slide, ic[i % len(ic)], Inches(x), Inches(y0), Inches(0.46), _acc(ctx))
        C.label(slide, x + 0.65, y0 + 0.12, cw - 0.65, f"FEATURE {i + 1:02d}", color=B.SLATE, size=9, name=f"Feature {i + 1} label")
        _title_body(slide, x, y0 + 0.65, cw, BOT - y0 - 0.65, it.get("title", ""), it.get("body"), f"Feature {i + 1}",
                    tsizes=(20, 18, 16, 14), bsizes=(14, 13, 12))


@variant("product.spotlight", "product", ("AVI-D161-04", "AVI-D161-16", "AVI-D081-09"), 2, 6, needs_image=True)
def product_spotlight(slide, items, ctx):
    """Round product visual at the centre, name beneath, features split left and right (ref D161-04/D081-09)."""
    name = _extra(ctx).get("name") or ""
    d = 3.3; cx = M + W / 2; vy = TOP + 0.2
    ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2 - 0.14), Inches(vy - 0.14), Inches(d + 0.28), Inches(d + 0.28))
    C._clean(ring, None, line=B.LINE, w=1.0); ring.name = "Spotlight ring"
    oval_picture(slide, _pick(ctx, name + " " + getattr(ctx, "title", "")), cx - d / 2, vy, d, name="Product visual")
    if name:
        ny = vy + d + 0.4
        _txt(slide, cx - 2.2, ny, 4.4, 0.6, name, _fit(name, 4.4, 0.6, [26, 24, 22, 20, 18], max_lines=1), B.BLACK, align=PP_ALIGN.CENTER, name="Product name")
        C.rect(slide, cx - 0.35, ny + 0.7, 0.7, 0.05, fill=B.RED, name="Product name mark")
    n = len(items); left = (n + 1) // 2
    sw = (W - d - 1.4) / 2
    for side, group in ((0, items[:left]), (1, items[left:])):
        if not group: continue
        x = M if side == 0 else cx + d / 2 + 0.7
        rh = (BOT - TOP - 0.1) / max(len(group), 1)
        for k, it in enumerate(group):
            i = k if side == 0 else left + k
            y = TOP + 0.05 + k * rh
            al = PP_ALIGN.RIGHT if side == 0 else PP_ALIGN.LEFT
            ic = _icons(ctx)
            ix = x + sw - 0.46 if side == 0 else x
            add_icon(slide, ic[i % len(ic)], Inches(ix), Inches(y + 0.1), Inches(0.46), _acc(ctx))
            _title_body(slide, x, y + 0.7, sw, rh - 0.8, it.get("title", ""), it.get("body"), f"Feature {i + 1}", align=al,
                        tsizes=(20, 18, 16, 14), bsizes=(14, 13, 12, 11))


# ================================================================== GAUGE family
@variant("gauge.dials", "gauge", ("AVI-D135-17", "AVI-D135-14", "AVI-D135-18"), 1, 4)
def gauge_dials(slide, items, ctx):
    """Half-circle dials: track arc + value arc, value numeral in the hub (ref D135-17/D135-14)."""
    n = len(items); cw = W / n; d = min(3.4, cw - 0.6)
    has_notes = bool([x for x in (_extra(ctx).get("notes") or []) if x])
    y0 = TOP + 0.35
    for i, it in enumerate(items):
        x = M + i * cw; dx = x + (cw - d) / 2
        _arc(slide, dx, y0, d, 180, 0, B.PAPER, name=f"Gauge {i + 1} track")
        f = _ratio(it)
        if f > 0:
            _arc(slide, dx, y0, d, 180, 180 + 180 * f if f < 1 else 359.99, _acc(ctx) if i else B.BLACK, name=f"Gauge {i + 1} value arc")
        val = _value_text(it)
        _txt(slide, dx + d * 0.18, y0 + d * 0.22, d * 0.64, d * 0.27, val, _fit(val, d * 0.64, d * 0.27, [40, 36, 32, 28, 24, 20], max_lines=1),
             B.BLACK, font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM, name=f"Gauge {i + 1} value")
        C.label(slide, dx, y0 + d / 2 + 0.06, 1.0, "0", color=B.SLATE, size=9, name=f"Gauge {i + 1} min")
        mx = f"{_num(it.get('max'))}"
        mt = C.label(slide, dx + d - 1.0, y0 + d / 2 + 0.06, 1.0, mx, color=B.SLATE, size=9, name=f"Gauge {i + 1} max")
        mt.text_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT
        lab = it.get("label", "")
        ly = y0 + d / 2 + 0.45
        _txt(slide, x + 0.2, ly, cw - 0.4, 0.9, lab, _fit(lab, cw - 0.4, 0.9, [20, 18, 16, 14], max_lines=2), B.BLACK,
             align=PP_ALIGN.CENTER, name=f"Gauge {i + 1} label", line=1.15)
    _notes(slide, ctx)


@variant("gauge.rings", "gauge", ("AVI-D135-03", "AVI-D081-07", "AVI-D063-18"), 1, 4)
def gauge_rings(slide, items, ctx):
    """Full progress rings on Paper cards, value inside, label below (ref D135-03/D081-07)."""
    n = len(items); gap = 0.3; cw = (W - gap * (n - 1)) / n
    has_notes = bool([x for x in (_extra(ctx).get("notes") or []) if x])
    cb = BOT - (0.55 if has_notes else 0.0)
    d = min(2.7, cw - 0.9, cb - TOP - 2.0)
    for i, it in enumerate(items):
        x = M + i * (cw + gap)
        C.rect(slide, x, TOP + 0.08, cw, cb - TOP - 0.08, fill=B.PAPER, name=f"Gauge {i + 1} card")
        dx = x + (cw - d) / 2; dy = TOP + 0.45
        _arc(slide, dx, dy, d, 270, 269.99, B.LINE, thick=12000, name=f"Gauge {i + 1} track")
        f = _ratio(it)
        if f > 0:
            _arc(slide, dx, dy, d, 270, 270 + 360 * f if f < 1 else 269.99, _acc(ctx) if i else B.BLACK, thick=12000, name=f"Gauge {i + 1} value arc")
        val = _value_text(it)
        _txt(slide, dx + d * 0.15, dy + d * 0.24, d * 0.7, d * 0.38, val, _fit(val, d * 0.7, d * 0.38, [36, 32, 28, 24, 20, 18], max_lines=1),
             B.BLACK, font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Gauge {i + 1} value")
        mx = C.label(slide, dx, dy + d * 0.64, d, f"/ {_num(it.get('max'))}", color=B.SLATE, size=9, name=f"Gauge {i + 1} max")
        mx.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        lab = it.get("label", "")
        ly = dy + d + 0.3
        _txt(slide, x + 0.25, ly, cw - 0.5, cb - ly - 0.2, lab, _fit(lab, cw - 0.5, cb - ly - 0.2, [20, 18, 16, 14], max_lines=2), B.BLACK,
             align=PP_ALIGN.CENTER, name=f"Gauge {i + 1} label", line=1.15)
    _notes(slide, ctx)


@variant("gauge.bars", "gauge", ("AVI-D064-07", "AVI-D063-12", "AVI-D064-03"), 1, 4, prefers="long")
def gauge_bars(slide, items, ctx):
    """Labelled progress tracks with value at the end (ref D064-07/D063-12)."""
    n = len(items)
    has_notes = bool([x for x in (_extra(ctx).get("notes") or []) if x])
    y1 = BOT - (0.6 if has_notes else 0.1)
    rh = min(1.35, (y1 - TOP - 0.1) / n); y0 = TOP + 0.1 + (y1 - TOP - 0.1 - rh * n) / 2
    lw = 3.6; vx = M + W - 1.9; tx = M + lw + 0.3; tw = vx - tx - 0.3
    for i, it in enumerate(items):
        y = y0 + i * rh; cy = y + rh / 2
        lab = it.get("label", "")
        _txt(slide, M, y, lw, rh, lab, _fit(lab, lw, rh - 0.2, [20, 18, 16, 14], max_lines=2), B.BLACK, anchor=MSO_ANCHOR.MIDDLE, name=f"Gauge {i + 1} label", line=1.15)
        tr = C.rect(slide, tx, cy - 0.14, tw, 0.28, fill=B.PAPER, name=f"Gauge {i + 1} track", shape=MSO_SHAPE.ROUNDED_RECTANGLE); tr.adjustments[0] = 0.5
        f = _ratio(it)
        if f > 0:
            fb = C.rect(slide, tx, cy - 0.14, max(0.28, tw * f), 0.28, fill=_acc(ctx) if i else B.BLACK, name=f"Gauge {i + 1} value bar",
                        shape=MSO_SHAPE.ROUNDED_RECTANGLE); fb.adjustments[0] = 0.5
        val = _value_text(it)
        _txt(slide, vx, y, 1.9, rh, val, _fit(val, 1.9, 0.6, [28, 24, 22, 20, 18], max_lines=1), B.BLACK, font=B.MONO, align=PP_ALIGN.RIGHT,
             anchor=MSO_ANCHOR.MIDDLE, name=f"Gauge {i + 1} value")
        mx = C.label(slide, tx, cy + 0.2, tw, f"0 — {_num(it.get('max'))}", color=B.SLATE, size=9, name=f"Gauge {i + 1} scale")
        if i < n - 1: C.hline(slide, M, y + rh, W, name=f"Gauge {i + 1} rule")
    _notes(slide, ctx)


# ================================================================== QUOTE family
@variant("quote.panel", "quote", ("AVI-D242-10", "AVI-D242-06", "AVI-D131-01"), 1, 2)
def quote_panel(slide, items, ctx):
    """Command Black panel across the content zone; large quote mark, centred statement, attribution (ref D242-10)."""
    py = TOP + 0.1
    C.rect(slide, M, py, W, BOT - py, fill=B.BLACK, name="Quote panel")
    _txt(slide, M + W / 2 - 0.6, py + 0.12, 1.2, 1.1, "“", 60, B.RED, align=PP_ALIGN.CENTER, name="Quote mark")
    attr = _extra(ctx).get("attribution")
    qh = BOT - py - (2.25 if attr else 1.7)
    body = "\n".join(items)
    _txt(slide, M + 1.3, py + 1.25, W - 2.6, qh, items, _fit(body, W - 2.6, qh, [32, 28, 26, 24, 22, 20, 18], line=1.4), B.WHITE,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name="Quote", line=1.35)
    if attr:
        ay = py + 1.25 + qh + 0.2
        C.rect(slide, M + W / 2 - 0.3, ay, 0.6, 0.03, fill=B.MIST, name="Attribution rule")
        _txt(slide, M + 1.3, ay + 0.15, W - 2.6, 0.4, attr, _fit(attr, W - 2.6, 0.4, [15, 14, 13, 12], max_lines=1), B.MIST,
             align=PP_ALIGN.CENTER, name="Attribution")


@variant("quote.visual-side", "quote", ("AVI-D242-15", "AVI-D242-17", "AVI-D242-11"), 1, 2, needs_image=True)
def quote_side(slide, items, ctx):
    """Statement on the left with a vertical accent bar; approved key visual on the right (ref D242-15/D242-17)."""
    pw = 4.6; px = M + W - pw
    picture(slide, _pick(ctx, getattr(ctx, "title", "") + " " + " ".join(items)), px, TOP + 0.05, pw, BOT - TOP - 0.05, name="Quote visual")
    tw = px - M - 0.9
    _txt(slide, M, TOP + 0.02, 1.0, 0.95, "“", 52, B.MIST, name="Quote mark")
    attr = _extra(ctx).get("attribution")
    qy = TOP + 1.0; qh = BOT - qy - (1.0 if attr else 0.3)
    C.rect(slide, M, qy, 0.07, qh, fill=B.RED, name="Quote accent bar")
    body = "\n".join(items)
    _txt(slide, M + 0.45, qy, tw - 0.45, qh, items, _fit(body, tw - 0.45, qh, [30, 28, 26, 24, 22, 20, 18], line=1.4), B.BLACK,
         anchor=MSO_ANCHOR.MIDDLE, name="Quote", line=1.35)
    if attr:
        _txt(slide, M + 0.45, BOT - 0.7, tw - 0.45, 0.4, "— " + attr, _fit(attr, tw - 0.45, 0.4, [15, 14, 13, 12], max_lines=1), B.SLATE, name="Attribution")


AVIATION_FAMILIES = ("compare", "timeline", "map", "team", "product", "gauge", "quote")
