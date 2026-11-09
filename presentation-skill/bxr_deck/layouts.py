"""Content-layout library synthesised from the user's reference library (source-library/500頁.pptx).

The reference deck is organised in families (目錄, 圖文排版 n-items, 中心環繞, 扇形, 發展歷程/流程,
數據, 表格型圖片). Instead of copying a few pages, each family is distilled into several
*variants* (composition rules) that accept different content shapes — item count, text length,
sequence, numbers, available imagery. The selector scores every variant against the actual slide
content and spreads variety across the deck.

Rebuilt natively in CIS v3.2: Command Black/Graphite panels instead of the source's blue/gold,
Noto Sans TC / B612 Mono, the reference's stock photos replaced by approved BXR key visuals
(06_KeyVisuals) cropped to fill. No pixels, logos or text are taken from the purchased file.
`ref` lists the source pages each variant was distilled from (for traceability only)."""
import math, re
from dataclasses import dataclass
from pathlib import Path
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt
from PIL import Image
from . import brand as B
from . import compose as C
from .icons import add_icon

KV_DIR = B.REPO / "06_KeyVisuals"
# approved key visuals, tagged for content matching (CORP_* = no weapons: preferred for corporate)
KV_TAGS = {   # weapon-free set (CIS v3.2: CORP_* = 企業通用、不持槍) + abstract XR/terrain visuals
    "BXR_KV_CORP_DIGITAL_TWIN_v3.2.jpg": "twin 孿生 數位 digital 規劃 plan 版型 母片 設定 configuration 場地 シナリオ",
    "BXR_KV_CORP_TRAINING_SPACE_v3.2.jpg": "training 訓練 空間 研修 準備 需求 演練 執行 pilot 試行",
    "BXR_KV_CORP_AI_TERRAIN_v3.2.jpg": "ai terrain 地形 分析 analytics 數據 評估 evaluation 評価 品質 qa",
    "BXR_KV_CORP_SMART_CITY_v3.2.jpg": "city 城市 防災 fire 消防 救災 police 警 公共 government 応用",
    "BXR_KV_XR_TWIN_v3.jpg": "xr vr mr 虛擬 simulation 模擬 情境 scenario 仮想",
    "BXR_KV_CORP_TWIN_v3.jpg": "corporate 企業 系統 system platform 產出 output 簡報",
    "BXR_KV_UAV_TERRAIN_v3.jpg": "uav drone 無人機 ドローン 空 地圖 map 路徑 path",
    "BXR_KV_NAVY_SEA_DARK_v3.1.jpg": "navy 海 艦 maritime 回饋 檢討 review 振り返り",
    "BXR_KV_CORP_TERRAIN_v3.jpg": "overview 概要 總覽 language 語言 english",
    "BXR_KV_NAVY_SEA_LIGHT_v3.1.jpg": "sea light 確認 assessment ヒアリング 需求",
}
KV_TACTICAL = {   # armed figures: only for police / defense sector decks
    "BXR_KV_C_SIM_v3.jpg": "simulation 模擬 情境 演練",
    "BXR_KV_XR_MR_v3.jpg": "mr 場地 混合",
    "BXR_KV_XR_VR_v3.jpg": "vr 頭戴 虛擬",
    "BXR_KV_AI_NPC_v3.jpg": "ai npc 角色",
    "BXR_KV_TEAM_v3.jpg": "team 團隊 回饋 檢討",
    "BXR_KV_XR_SCAN_v3.jpg": "scan 掃描 確認",
}


class KVPicker:
    """Pick approved key visuals by keyword, avoiding repeats inside one deck."""
    def __init__(self, sector=None):
        self.used = []
        self.sector = sector
        self.pool = dict(KV_TAGS)
        if sector in ("police", "army", "navy", "air"):
            self.pool.update(KV_TACTICAL)

    def pick(self, text):
        t = (text or "").lower()
        scored = []
        for i, (f, tags) in enumerate(self.pool.items()):
            s = sum(1 for k in tags.split() if k in t)
            s -= 3 * self.used.count(f)
            scored.append((s, -i, f))
        f = max(scored)[2]
        self.used.append(f)
        return KV_DIR / f


def picture(slide, path, x, y, w, h, name="Key visual"):
    """Native picture cropped (not stretched) to fill the box."""
    with Image.open(path) as _im: iw, ih = _im.size
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    pic.name = name
    r_img, r_box = iw / ih, w / h
    if r_img > r_box:
        c = (1 - r_box / r_img) / 2; pic.crop_left = pic.crop_right = c
    else:
        c = (1 - r_img / r_box) / 2; pic.crop_top = pic.crop_bottom = c
    return pic


def oval_picture(slide, path, x, y, d, name="Key visual (round)"):
    pic = picture(slide, path, x, y, d, d, name)
    # switch geometry to ellipse (still a native, replaceable picture)
    geom = pic._element.spPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}prstGeom")
    geom.set("prst", "ellipse")
    return pic


# ------------------------------------------------------------------ variant registry
@dataclass
class Variant:
    name: str
    family: str
    ref: tuple
    nmin: int
    nmax: int
    render: object
    needs_image: bool = False
    prefers: str = ""        # 'short' | 'long' | 'sequence' | ''

VARIANTS = []


def variant(name, family, ref, nmin, nmax, needs_image=False, prefers=""):
    def deco(fn):
        VARIANTS.append(Variant(name, family, ref, nmin, nmax, fn, needs_image, prefers)); return fn
    return deco


def features(items):
    lens = [len(x) for x in items] or [0]
    return {"n": len(items), "avg": sum(lens) / len(lens), "max": max(lens)}


def select(family, items, used, sequence=False, prefer=None):
    """Score variants for this content; penalise those already used in the deck.
    `prefer` (variant name from a previous plan) wins whenever it still fits this content."""
    f = features(items); best = None
    for v in VARIANTS:
        if prefer and v.name == prefer and v.family == family and v.nmin <= f["n"] <= v.nmax:
            return v
    for v in VARIANTS:
        if v.family != family or not (v.nmin <= f["n"] <= v.nmax): continue
        s = 10.0
        if v.prefers == "short": s += 2 if f["max"] <= 14 else -4
        if v.prefers == "long": s += 2 if f["avg"] > 14 else -1
        if v.prefers == "sequence": s += 3 if sequence else -2
        s -= 4 * used.count(v.name)
        s -= 0.01 * VARIANTS.index(v)      # deterministic tie-break
        if best is None or s > best[0]: best = (s, v)
    return best[1] if best else None


# ------------------------------------------------------------------ helpers
M, W, TOP, BOT = C.M, C.BODY_W, 1.42, 6.66


def _txt(slide, x, y, w, h, text, size, color=B.BLACK, **kw):
    return C.textbox(slide, x, y, w, h, text, size=size, color=color, **kw)


def _fit(text, w, h, sizes, line=1.25, max_lines=None):
    return C.fit_size(text, w, h, sizes, line=line, max_lines=max_lines)[0]


# ================================================================== AGENDA family
@variant("agenda.side-visual", "agenda", (21, 19, 20), 2, 6, needs_image=True)
def agenda_side(slide, items, ctx):
    """Left key-visual panel with chevron edge; numbered list on the right (ref p21)."""
    pw = 4.3
    picture(slide, ctx.kv.pick(ctx.topic), 0, C.BANNER_BOTTOM, pw, 6.85 - C.BANNER_BOTTOM)
    tri = slide.shapes.add_shape(MSO_SHAPE.RIGHT_TRIANGLE, Inches(pw - 0.9), Inches(C.BANNER_BOTTOM), Inches(0.9), Inches(6.85 - C.BANNER_BOTTOM))
    tri.rotation = 180
    C._clean(tri, B.WHITE); tri.name = "Panel edge"
    n = len(items); row = min(0.92, (BOT - TOP - 0.3) / n); y0 = TOP + (BOT - TOP - row * n) / 2
    for i, it in enumerate(items):
        y = y0 + i * row; x = pw + 0.55 + i * 0.18          # staggered like the reference
        _txt(slide, x, y, 0.85, row, f"{i + 1:02d}", 26, B.TEXT_RED, font=B.MONO, anchor=MSO_ANCHOR.MIDDLE, name=f"Agenda {i + 1} number")
        _txt(slide, x + 0.95, y, 12.6 - x - 0.95, row, it, _fit(it, 12.6 - x - 0.95, row, [24, 22, 20, 18], max_lines=1),
             anchor=MSO_ANCHOR.MIDDLE, name=f"Agenda {i + 1} title")


@variant("agenda.visual-columns", "agenda", (22, 23, 27), 3, 5, needs_image=True, prefers="short")
def agenda_columns(slide, items, ctx):
    """Equal columns: key-visual strip, big mono numeral, title (ref p22/p23/p27)."""
    n = len(items); gap = 0.22; w = (W - gap * (n - 1)) / n
    for i, it in enumerate(items):
        x = M + i * (w + gap)
        picture(slide, ctx.kv.pick(it), x, TOP + 0.1, w, 2.55)
        _txt(slide, x, TOP + 2.85, w, 0.9, f"{i + 1:02d}", 44, B.MIST, font=B.MONO, name=f"Agenda {i + 1} number")
        C.rect(slide, x, TOP + 3.85, 0.5, 0.04, fill=ctx.accent, name=f"Agenda {i + 1} rule")
        _txt(slide, x, TOP + 4.05, w, 1.0, it, _fit(it, w, 1.0, [22, 20, 18, 16], max_lines=2), name=f"Agenda {i + 1} title", line=1.15)


@variant("agenda.list", "agenda", (19,), 2, 10)
def agenda_list(slide, items, ctx):
    C.agenda(slide, items, details=ctx.extra.get("details"))


# ================================================================== ITEMS family (2–8 parallel points)
def _item_body(it): return it.get("body") if isinstance(it, dict) else None
def _item_title(it): return it["title"] if isinstance(it, dict) else it


@variant("items.visual-band", "items", (102, 151, 111), 2, 4, needs_image=True)
def items_band(slide, items, ctx):
    """Full-width key-visual band on top, dark info band below with icon columns (ref p102/p151)."""
    picture(slide, ctx.kv.pick(ctx.title + " " + " ".join(map(_item_title, items))), M, TOP + 0.05, W, 2.35)
    band_y = TOP + 2.55
    C.rect(slide, M, band_y, W, BOT - band_y, fill=B.GRAPHITE, name="Info band")
    n = len(items); w = W / n
    for i, it in enumerate(items):
        x = M + i * w
        if i: C.hline(slide, x, band_y + 0.45, 0, color=B.SLATE)
        add_icon(slide, it["icon"], Inches(x + w / 2 - 0.27), Inches(band_y + 0.42), Inches(0.54), ctx.accent_dark)
        t = _item_title(it)
        _txt(slide, x + 0.3, band_y + 1.15, w - 0.6, 0.8, t, _fit(t, w - 0.6, 0.8, [22, 20, 18, 16], max_lines=2), B.WHITE,
             align=PP_ALIGN.CENTER, name=f"Item {i + 1} title", line=1.15)
        if _item_body(it):
            _txt(slide, x + 0.3, band_y + 1.95, w - 0.6, BOT - band_y - 2.1, it["body"], 14, B.MIST, align=PP_ALIGN.CENTER, name=f"Item {i + 1} text", line=1.35)
    for k in range(1, n):
        C.hline(slide, M + k * w, band_y + 0.5, 0.001, color=B.SLATE)


@variant("items.raised-cards", "items", (112, 158, 159), 3, 4, needs_image=True)
def items_cards(slide, items, ctx):
    """Raised cards with round key-visual medallion, on a dark base band (ref p112/p158)."""
    n = len(items); gap = 0.3; w = (W - 0.6 - gap * (n - 1)) / n
    base_y = TOP + 2.6
    C.rect(slide, M, base_y, W, BOT - base_y, fill=B.BLACK, name="Base band")
    summary = ctx.extra.get("summary")
    if summary:
        _txt(slide, M + 0.4, BOT - 0.95, W - 0.8, 0.7, summary, 15, B.MIST, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name="Summary")
    for i, it in enumerate(items):
        x = M + 0.3 + i * (w + gap); y = TOP + 0.15; h = (BOT - 1.1 if summary else BOT - 0.35) - y
        C.rect(slide, x, y, w, h, fill=B.WHITE, line=B.LINE, name=f"Card {i + 1}")
        d = 1.35
        oval_picture(slide, ctx.kv.pick(_item_title(it)), x + (w - d) / 2, y + 0.35, d, name=f"Card {i + 1} visual")
        t = _item_title(it)
        _txt(slide, x + 0.25, y + 1.95, w - 0.5, 0.85, t, _fit(t, w - 0.5, 0.85, [22, 20, 18, 16], max_lines=2), align=PP_ALIGN.CENTER,
             name=f"Card {i + 1} title", line=1.15)
        C.rect(slide, x + w / 2 - 0.25, y + 2.9, 0.5, 0.04, fill=ctx.accent, name=f"Card {i + 1} rule")
        if _item_body(it):
            _txt(slide, x + 0.3, y + 3.1, w - 0.6, h - 3.25, it["body"], 14, B.SLATE, align=PP_ALIGN.CENTER, name=f"Card {i + 1} text", line=1.35)


@variant("items.fan", "items", (142, 59, 89), 3, 4, needs_image=True)
def items_fan(slide, items, ctx):
    """Semi-circle key visual at the base, items fanned along the arc (ref p142/p59)."""
    d = 4.2; cx = M + W / 2
    oval_picture(slide, ctx.kv.pick(ctx.title), cx - d / 2, BOT - d / 2 - 0.15, d, name="Fan visual")
    cover = C.rect(slide, M - 0.1, BOT - 0.15 + 0.02, W + 0.2, 0.6, fill=B.WHITE, name="Fan base mask")
    arc = slide.shapes.add_shape(MSO_SHAPE.ARC, Inches(cx - d / 2 - 0.25), Inches(BOT - d / 2 - 0.4), Inches(d + 0.5), Inches(d + 0.5))
    C._clean(arc, None, line=ctx.accent, w=1.5); arc.adjustments[0] = 180; arc.adjustments[1] = 0
    n = len(items)
    pos = {3: [(-1, 0.55), (0, 0.0), (1, 0.55)], 4: [(-1.15, 1.25), (-0.5, 0.0), (0.5, 0.0), (1.15, 1.25)]}[n]
    bw = 3.0
    for i, (it, (dx, dy)) in enumerate(zip(items, pos)):
        x = cx + dx * 4.3 - bw / 2 if n == 3 else cx + dx * 4.6 - bw / 2
        y = TOP + 0.1 + dy
        add_icon(slide, it["icon"], Inches(x + bw / 2 - 0.3), Inches(y), Inches(0.6), ctx.accent)
        t = _item_title(it)
        _txt(slide, x, y + 0.75, bw, 0.8, t, _fit(t, bw, 0.8, [22, 20, 18, 16], max_lines=2), align=PP_ALIGN.CENTER, name=f"Item {i + 1} title", line=1.15)
        if _item_body(it):
            _txt(slide, x, y + 1.5, bw, 1.0, it["body"], 14, B.SLATE, align=PP_ALIGN.CENTER, name=f"Item {i + 1} text", line=1.35)


@variant("items.hub", "items", (56, 57, 58), 4, 8, needs_image=True)
def items_hub(slide, items, ctx):
    """Central round key visual with items on a ring (4/6/8 points; ref p56–58)."""
    n = len(items); cx, cy = M + W / 2, (TOP + BOT) / 2 + 0.05
    R = 1.55
    ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - R - 0.45), Inches(cy - R - 0.45), Inches(2 * R + 0.9), Inches(2 * R + 0.9))
    C._clean(ring, None, line=B.LINE, w=1.0); ring.name = "Hub ring"
    oval_picture(slide, ctx.kv.pick(ctx.title), cx - R, cy - R, 2 * R, name="Hub visual")
    left = [i for i in range(n) if i < (n + 1) // 2]
    rows = (n + 1) // 2
    for i, it in enumerate(items):
        side = -1 if i < rows else 1; k = i if i < rows else i - rows
        span = rows - 1 or 1
        ang = math.radians(-50 + 100 * k / span) if rows > 1 else 0
        nx = cx + side * (R + 0.45) * math.cos(ang); ny = cy + (R + 0.45) * math.sin(ang)
        node = C.rect(slide, nx - 0.26, ny - 0.26, 0.52, 0.52, fill=ctx.accent_block, name=f"Node {i + 1}", shape=MSO_SHAPE.OVAL)
        add_icon(slide, it["icon"], Inches(nx - 0.16), Inches(ny - 0.16), Inches(0.32), B.WHITE)
        tw = 3.2
        tx = nx - 0.5 - tw if side < 0 else nx + 0.5
        t = _item_title(it)
        _txt(slide, tx, ny - 0.3, tw, 0.5, t, _fit(t, tw, 0.5, [20, 18, 16], max_lines=1), align=PP_ALIGN.RIGHT if side < 0 else PP_ALIGN.LEFT,
             name=f"Item {i + 1} title")
        if _item_body(it):
            _txt(slide, tx, ny + 0.18, tw, 0.7, it["body"], 13, B.SLATE, align=PP_ALIGN.RIGHT if side < 0 else PP_ALIGN.LEFT, name=f"Item {i + 1} text", line=1.3)


@variant("items.visual-grid", "items", (46, 48), 4, 6, needs_image=True)
def items_grid(slide, items, ctx):
    """Tall key visual left, icon grid (2 columns) right (ref p46)."""
    pw = 4.4
    picture(slide, ctx.kv.pick(ctx.title), M, TOP + 0.05, pw, BOT - TOP - 0.05)
    n = len(items); rows = (n + 1) // 2; gx = M + pw + 0.5; gw = (W - pw - 0.5 - 0.4) / 2
    rh = (BOT - TOP) / rows
    for i, it in enumerate(items):
        r, c = divmod(i, 2); x = gx + c * (gw + 0.4); y = TOP + 0.2 + r * rh
        add_icon(slide, it["icon"], Inches(x), Inches(y), Inches(0.5), ctx.accent)
        t = _item_title(it)
        _txt(slide, x + 0.75, y, gw - 0.75, 0.55, t, _fit(t, gw - 0.75, 0.55, [20, 18, 16], max_lines=1), name=f"Item {i + 1} title")
        C.hline(slide, x + 0.75, y + 0.62, gw - 0.75, name=f"Item {i + 1} rule")
        if _item_body(it):
            _txt(slide, x + 0.75, y + 0.75, gw - 0.75, rh - 0.95, it["body"], 14, B.SLATE, name=f"Item {i + 1} text", line=1.35)


@variant("items.cards", "items", (103,), 2, 4)
def items_plain(slide, items, ctx):
    C.cards(slide, [{"title": _item_title(i), "icon": i["icon"], "body": _item_body(i)} for i in items], height=3.4, accent=ctx.accent)


# ================================================================== PROCESS family
@variant("process.stage-arrow", "process", (175, 131), 3, 5, needs_image=True, prefers="sequence")
def process_stage(slide, steps, ctx):
    """Icon nodes on a connector line, visual strip per stage, chevron arrow band (ref p175)."""
    n = len(steps); w = W / n; line_y = TOP + 0.45
    C.hline(slide, M + w / 2, line_y, W - w, color=B.MIST, weight=1.25, name="Stage line")
    for i, st in enumerate(steps):
        x = M + i * w
        node = C.rect(slide, x + w / 2 - 0.3, line_y - 0.3, 0.6, 0.6, fill=B.WHITE, line=ctx.accent, line_w=1.5, name=f"Stage {i + 1} node", shape=MSO_SHAPE.OVAL)
        _txt(slide, x + w / 2 - 0.3, line_y - 0.3, 0.6, 0.6, f"{i + 1:02d}", 14, ctx.accent, font=B.MONO, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Stage {i + 1} number")
        picture(slide, ctx.kv.pick(st), x + 0.12, line_y + 0.6, w - 0.24, 2.35, name=f"Stage {i + 1} visual")
        chev = slide.shapes.add_shape(MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON, Inches(x + (0.0 if i else 0.12)), Inches(BOT - 1.55),
                                      Inches(w + (0.15 if i < n - 1 else -0.12) - (0 if i else 0.12)), Inches(0.62))
        chev.adjustments[0] = 0.28
        C._clean(chev, B.GRAPHITE if i % 2 == 0 else B.BLACK); chev.name = f"Stage {i + 1} arrow"
        _txt(slide, x + 0.35, BOT - 1.55, w - 0.6, 0.62, st, _fit(st, w - 0.7, 0.55, [18, 16, 14], max_lines=1), B.WHITE,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Stage {i + 1} title")
    if ctx.extra.get("caption"):
        _txt(slide, M, BOT - 0.75, W, 0.5, ctx.extra["caption"], 14, B.SLATE, align=PP_ALIGN.CENTER, name="Process caption")


@variant("process.round-nodes", "process", (237, 254), 3, 6, needs_image=True, prefers="sequence")
def process_nodes(slide, steps, ctx):
    """Statement band, then round key-visual nodes on a line with step names (ref p237)."""
    C.rect(slide, M, TOP + 0.05, W, 1.05, fill=B.GRAPHITE, name="Statement band")
    stmt = ctx.extra.get("caption") or " → ".join(steps)
    _txt(slide, M + 0.5, TOP + 0.05, W - 1.0, 1.05, stmt, _fit(stmt, W - 1.0, 0.9, [22, 20, 18, 16], max_lines=2), B.WHITE,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name="Statement")
    n = len(steps); w = W / n; d = min(1.55, w - 0.5); cy = TOP + 2.45
    C.hline(slide, M + 0.2, cy, W - 0.4, color=B.MIST, weight=1.25, name="Process line")
    for i, st in enumerate(steps):
        x = M + i * w + w / 2
        oval_picture(slide, ctx.kv.pick(st), x - d / 2, cy - d / 2, d, name=f"Step {i + 1} visual")
        ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x - d / 2 - 0.08), Inches(cy - d / 2 - 0.08), Inches(d + 0.16), Inches(d + 0.16))
        C._clean(ring, None, line=ctx.accent if i == 0 else B.MIST, w=1.5); ring.name = f"Step {i + 1} ring"
        C.label(slide, x - w / 2 + 0.2, cy + d / 2 + 0.3, w - 0.4, f"STEP {i + 1:02d}", color=B.SLATE, size=10, name=f"Step {i + 1} label").text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        _txt(slide, x - w / 2 + 0.15, cy + d / 2 + 0.62, w - 0.3, 0.9, st, _fit(st, w - 0.3, 0.9, [22, 20, 18, 16], max_lines=2),
             align=PP_ALIGN.CENTER, name=f"Step {i + 1} title", line=1.15)


@variant("process.track", "process", (131, 441), 3, 6, prefers="sequence")
def process_track(slide, steps, ctx):
    C.process(slide, [{"title": s} for s in steps], accent=ctx.accent)


# ================================================================== TEXT family (1–4 statements)
@variant("text.visual-left", "text", (46, 49, 125), 1, 4, needs_image=True)
def text_visual(slide, lines, ctx):
    """Key visual on the left 40 %, statements with icon markers on the right (ref p46/p49)."""
    pw = 4.9
    picture(slide, ctx.kv.pick(ctx.title + " " + " ".join(lines)), M, TOP + 0.05, pw, BOT - TOP - 0.05)
    x = M + pw + 0.6; tw = W - pw - 0.6
    n = len(lines); rh = min(1.35, (BOT - TOP - 0.3) / n); y0 = TOP + 0.25
    for i, ln in enumerate(lines):
        y = y0 + i * rh
        add_icon(slide, ctx.icons[i % len(ctx.icons)], Inches(x), Inches(y + 0.05), Inches(0.42), ctx.accent)
        _txt(slide, x + 0.7, y, tw - 0.7, rh - 0.2, ln, _fit(ln, tw - 0.7, rh - 0.25, [22, 20, 18, 16], line=1.3), name=f"Point {i + 1}", line=1.25)
        if i < n - 1: C.hline(slide, x + 0.7, y + rh - 0.12, tw - 0.7, name=f"Point {i + 1} rule")


@variant("text.statement-band", "text", (63, 237), 1, 2, needs_image=True)
def text_band(slide, lines, ctx):
    """Wide key visual with a dark statement panel overlapping it (ref p63)."""
    picture(slide, ctx.kv.pick(ctx.title + " " + " ".join(lines)), M + 3.2, TOP + 0.05, W - 3.2, BOT - TOP - 0.05)
    C.rect(slide, M, TOP + 0.75, 6.2, BOT - TOP - 1.5, fill=B.BLACK, name="Statement panel")
    body = "\n".join(lines)
    _txt(slide, M + 0.5, TOP + 1.2, 5.2, BOT - TOP - 2.4, lines, _fit(body, 5.2, BOT - TOP - 2.4, [28, 26, 24, 22, 20], line=1.35), B.WHITE,
         name="Statement", line=1.3)


@variant("text.bullets", "text", (), 3, 8, prefers="long")
def text_bullets(slide, lines, ctx):
    C.bullets(slide, lines)


# ================================================================== DATA family
@variant("data.kpi-visuals", "data", (155, 73, 179), 2, 4, needs_image=True)
def data_kpi(slide, d, ctx):
    """KPI numerals row, visual strip below, source note (ref p155/p73). Values only from the brief."""
    cats, vals, unit = d["categories"], d["values"], d.get("unit", "")
    n = len(cats); w = W / n
    for i, (c, v) in enumerate(zip(cats, vals)):
        x = M + i * w
        num = (f"{v:g}") + (f" {unit}" if unit else "")
        _txt(slide, x + 0.2, TOP + 0.1, w - 0.4, 0.95, num, 40, B.TEXT_RED if i == d.get("highlight", -1) else B.BLACK, name=f"KPI {i + 1} value")
        C.hline(slide, x + 0.2, TOP + 1.12, w - 0.6, color=B.LINE, name=f"KPI {i + 1} rule")
        _txt(slide, x + 0.2, TOP + 1.25, w - 0.4, 0.5, c, _fit(c, w - 0.4, 0.5, [16, 15, 14], max_lines=1), B.SLATE, name=f"KPI {i + 1} label")
        picture(slide, ctx.kv.pick(c), x + 0.12, TOP + 2.0, w - 0.24, BOT - TOP - 2.75, name=f"KPI {i + 1} visual")
    if d.get("notes"):
        _txt(slide, M, BOT - 0.55, W, 0.4, d["notes"][0], 12, B.SLATE, name="Source note")


@variant("data.chart", "data", (125, 135), 2, 12)
def data_chart(slide, d, ctx):
    raise NotImplementedError  # handled by generator (needs chart layout)


def ref_note(v):
    return f"layout variant {v.name}; distilled from reference library pages {', '.join('#' + str(p) for p in v.ref) or '—'}"
