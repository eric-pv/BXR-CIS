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
from PIL import Image, ImageStat
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


MAX_KV_REPEAT = 2          # one key visual appears at most twice per deck
_TONE = {}
_ACTIVE = [None]           # picker of the deck being built (lets select() respect image capacity)


def kv_tone(f):
    """'dark' | 'light' from the image's mean luminance (cached)."""
    if f not in _TONE:
        with Image.open(KV_DIR / f) as im:
            lum = ImageStat.Stat(im.convert("L").resize((64, 36))).mean[0] / 255
        _TONE[f] = "dark" if lum < 0.45 else "light"
    return _TONE[f]


class KVPicker:
    """Pick approved key visuals by keyword for one deck.
    Rules: a visual is used at most MAX_KV_REPEAT times; consecutive picks alternate light/dark tone;
    corporate decks only get the weapon-free pool (tactical visuals only for police/defense sectors)."""
    def __init__(self, sector=None):
        self.used = []
        self.sector = sector
        self.pool = dict(KV_TAGS)
        if sector in ("police", "army", "navy", "air"):
            self.pool.update(KV_TACTICAL)
        self.overflow = 0
        _ACTIVE[0] = self

    def remaining(self):
        return sum(max(0, MAX_KV_REPEAT - self.used.count(f)) for f in self.pool)

    def pick(self, text):
        t = (text or "").lower()
        last = kv_tone(self.used[-1]) if self.used else None
        free = [f for f in self.pool if self.used.count(f) < MAX_KV_REPEAT]
        if not free:                       # select() avoids this; recorded so QA can flag it
            self.overflow += 1
            free = list(self.pool)
        scored = []
        for i, f in enumerate(self.pool):
            if f not in free: continue
            s = sum(1 for k in self.pool[f].split() if k in t)
            s -= 3 * self.used.count(f)
            if last and kv_tone(f) != last: s += 1.5
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
    per_item_image: bool = False   # one key visual per item (else one per slide)

    def images(self, n):
        return (n if self.per_item_image else 1) if self.needs_image else 0

VARIANTS = []
PER_ITEM_IMAGE = {"agenda.visual-columns", "items.raised-cards", "process.stage-arrow", "process.round-nodes", "data.kpi-visuals",
                  "items.slant-panels", "items.zigzag", "items.capsules", "process.numbered-panels", "text.thumb-list"}


def variant(name, family, ref, nmin, nmax, needs_image=False, prefers=""):
    def deco(fn):
        VARIANTS.append(Variant(name, family, ref, nmin, nmax, fn, needs_image, prefers, name in PER_ITEM_IMAGE)); return fn
    return deco


def features(items):
    lens = [len(x) for x in items] or [0]
    return {"n": len(items), "avg": sum(lens) / len(lens), "max": max(lens)}


def select(family, items, used, sequence=False, prefer=None):
    """Score variants for this content; penalise those already used in the deck.
    `prefer` (variant name from a previous plan) wins whenever it still fits this content."""
    f = features(items); best = None
    kv = _ACTIVE[0]
    room = kv.remaining() if kv is not None else 10 ** 6
    for v in VARIANTS:
        if prefer and v.name == prefer and v.family == family and v.nmin <= f["n"] <= v.nmax and v.images(f["n"]) <= room:
            return v
    for v in VARIANTS:
        if v.family != family or not (v.nmin <= f["n"] <= v.nmax): continue
        if v.images(f["n"]) > room: continue          # would repeat a key visual more than MAX_KV_REPEAT
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
SW_IN = C.SW


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
    """Raised cards with round key-visual medallion over a dark base band (ref p112/p158).
    With body text the cards run tall; title-only cards shrink to their content and sit centred
    across the band, so no card carries an empty lower half."""
    n = len(items); gap = 0.3; w = (W - 0.6 - gap * (n - 1)) / n
    summary = ctx.extra.get("summary")
    has_body = any(_item_body(it) for it in items)
    d = 1.35
    if has_body:
        y = TOP + 0.15; h = (BOT - 1.1 if summary else BOT - 0.35) - y
        base_y = TOP + 2.6
    else:
        h = 3.3                                   # medallion + title + rule, nothing below
        y = TOP + (BOT - TOP - h) / 2 - (0.35 if summary else 0.1)
        base_y = y + h * 0.55                     # band crosses the cards' lower half
    C.rect(slide, M, base_y, W, BOT - base_y, fill=B.BLACK, name="Base band")
    if summary:
        sy = y + h + 0.15 if not has_body else BOT - 0.95
        _txt(slide, M + 0.4, sy, W - 0.8, min(0.7, BOT - sy - 0.05), summary, 15, B.MIST, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, name="Summary")
    for i, it in enumerate(items):
        x = M + 0.3 + i * (w + gap)
        C.rect(slide, x, y, w, h, fill=B.WHITE, line=B.LINE, name=f"Card {i + 1}")
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


# ================================================================== 500頁 expansion (PMLD second pass)
# Distilled from a full visual pass over all 604 reference pages (contact sheets, PMLD-NNNN ids).
# Only families the generator already dispatches (agenda / items / process / text). People, timeline,
# map, product, certificate and partner-logo pages are deliberately not used here (Aviation families /
# no BXR facts / third-party marks). Same rules as above: native shapes, CIS v3.2 colours and fonts,
# approved key visuals only, nothing taken from the purchased file.
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_SAFE = 0.88          # LibreOffice / PowerPoint wrap a little earlier than the PIL measurement


def _geom(shape, prst, adj=None):
    """Switch a picture/autoshape to another preset geometry (still native and replaceable)."""
    from lxml import etree
    g = shape._element.spPr.find(_A + "prstGeom")
    g.set("prst", prst)
    av = g.find(_A + "avLst")
    if av is None:
        av = etree.SubElement(g, _A + "avLst")
    for c in list(av): av.remove(c)
    for i, val in enumerate(adj or []):
        gd = etree.SubElement(av, _A + "gd")
        gd.set("name", "adj" if len(adj) == 1 else f"adj{i + 1}"); gd.set("fmla", f"val {int(val)}")
    return shape


def _common(texts, w, h, sizes, line=1.2, max_lines=None):
    """One size for a set of sibling texts. A single-line size (>= 16 pt, no orphan characters) wins when
    it is at most 4 pt smaller than the best wrapped size; otherwise the wrapped size is used."""
    ok = lambda s, ml: all(C.fit_size(t, w * _SAFE, h, [s], line=line, max_lines=ml)[2] for t in texts)
    one = next((s for s in sizes if s >= 16 and ok(s, 1)), None)
    wrapped = next((s for s in sizes if ok(s, max_lines)), sizes[-1])
    return one if one is not None and one >= wrapped - 4 else wrapped


def _lines(text, size, w):
    return C.wrap_lines(text, size, w * _SAFE)


def _num(slide, x, y, w, h, i, size, color, align=PP_ALIGN.LEFT, name=None, anchor=MSO_ANCHOR.TOP):
    return _txt(slide, x, y, w, h, f"{i + 1:02d}", size, color, font=B.MONO, align=align, anchor=anchor, name=name)


def _icon_disc(slide, icon, cx, cy, d, fill, icon_color, name):
    C.rect(slide, cx - d / 2, cy - d / 2, d, d, fill=fill, name=name, shape=MSO_SHAPE.OVAL)
    k = d * 0.52
    add_icon(slide, icon, Inches(cx - k / 2), Inches(cy - k / 2), Inches(k), icon_color)


def _arrow_end(conn):
    from lxml import etree
    ln = conn.line._get_or_add_ln()
    t = etree.SubElement(ln, _A + "tailEnd"); t.set("type", "triangle"); t.set("w", "med"); t.set("len", "med")


@variant("agenda.arc-nodes", "agenda", (19, 41), 2, 6, needs_image=True)
def agenda_arc(slide, items, ctx):
    """D-shaped key visual on the left; numbered icon nodes follow its curve (ref p19/p41)."""
    y0, h = C.BANNER_BOTTOM, 6.85 - C.BANNER_BOTTOM
    pw = 5.0
    pic = picture(slide, ctx.kv.pick(ctx.topic), 0, y0, pw, h, name="Agenda visual")
    _geom(pic, "flowChartDelay")
    cx, cy, rx, ry = pw / 2, y0 + h / 2, pw / 2 + 0.55, h / 2 - 0.25
    pts = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in range(-70, 71, 5)]
    fb = slide.shapes.build_freeform(Inches(pts[0][0]), Inches(pts[0][1]), scale=1.0)
    fb.add_line_segments([(Inches(x), Inches(y)) for x, y in pts[1:]], close=False)
    arc = fb.convert_to_shape(); C._clean(arc, None, line=B.LINE, w=1.0); arc.name = "Agenda arc"
    n = len(items); span = {2: 30, 3: 40, 4: 46, 5: 50, 6: 52}[n]
    pts = []
    for i in range(n):
        a = math.radians(-span + 2 * span * i / (n - 1))
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    tws = [SW_IN - M - (nx + 0.6) for nx, _ in pts]
    size = _common(items, min(tws), 0.55, [26, 24, 22, 20, 18], max_lines=1)
    for i, (it, (nx, ny)) in enumerate(zip(items, pts)):
        _icon_disc(slide, ctx.icons[i % len(ctx.icons)], nx, ny, 0.66, ctx.accent_block, B.WHITE, f"Agenda {i + 1} node")
        tx = nx + 0.6; tw = SW_IN - M - tx
        _num(slide, tx, ny - 0.42, 0.9, 0.3, i, 12, B.TEXT_RED, name=f"Agenda {i + 1} number")
        _txt(slide, tx, ny - 0.14, tw, 0.55, it, size, name=f"Agenda {i + 1} title")
        C.hline(slide, tx, ny + 0.48, tw, name=f"Agenda {i + 1} rule")


@variant("agenda.number-strip", "agenda", (28, 24, 18), 3, 7, needs_image=True, prefers="short")
def agenda_strip(slide, items, ctx):
    """Wide key visual with a strip of numbered cells overlapping its lower edge (ref p28/p24)."""
    n = len(items); gap = 0.1; cw = (W - 0.6 - gap * (n - 1)) / n; pad = 0.25 if n <= 5 else 0.14
    size = _common(items, cw - 2 * pad, 1.5, [24, 22, 20, 18, 16, 14], max_lines=3)
    nl = max(_lines(t, size, cw - 2 * pad) for t in items)
    ch = min(BOT - TOP - 1.6, 1.25 + nl * size * 1.25 / 72 + 0.45)
    y = BOT - ch
    picture(slide, ctx.kv.pick(ctx.topic), M, TOP + 0.05, W, y - TOP + 0.45, name="Agenda visual")
    for i, it in enumerate(items):
        x = M + 0.3 + i * (cw + gap)
        C.rect(slide, x, y, cw, ch, fill=B.BLACK if i % 2 == 0 else B.GRAPHITE, name=f"Agenda {i + 1} cell")
        _num(slide, x + pad, y + 0.22, cw - 2 * pad, 0.6, i, 30, B.MIST, name=f"Agenda {i + 1} number")
        C.rect(slide, x + pad, y + 0.95, 0.45, 0.04, fill=B.WHITE, name=f"Agenda {i + 1} rule")
        _txt(slide, x + pad, y + 1.15, cw - 2 * pad, ch - 1.25, it, size, B.WHITE, name=f"Agenda {i + 1} title", line=1.2)


@variant("agenda.tiles", "agenda", (25,), 3, 6, prefers="short")
def agenda_tiles(slide, items, ctx):
    """Paper field with staggered numbered tiles joined by a dashed path; no imagery (ref p25)."""
    C.rect(slide, M, TOP + 0.05, W, BOT - TOP - 0.05, fill=B.PAPER, name="Agenda field")
    n = len(items); gap = 0.3 if n <= 4 else 0.2; tw = (W - 0.8 - gap * (n - 1)) / n; pad = 0.2 if n <= 4 else 0.1
    size = _common(items, tw - 2 * pad, 1.2, [26, 24, 22, 20, 18, 16], max_lines=3)
    nl = max(_lines(t, size, tw - 2 * pad) for t in items)
    th = 1.35 + nl * size * 1.25 / 72 + 0.4
    mid = (TOP + BOT) / 2 + 0.05; amp = 0.55
    ys = [mid - th / 2 + (-amp if i % 2 == 0 else amp) for i in range(n)]
    xs = [M + 0.4 + i * (tw + gap) for i in range(n)]
    for i in range(n - 1):
        c = slide.shapes.add_connector(1, Inches(xs[i] + tw / 2), Inches(ys[i] + 0.6), Inches(xs[i + 1] + tw / 2), Inches(ys[i + 1] + 0.6))
        c.line.color.rgb = C.rgb(B.SLATE); c.line.width = Pt(1.25); c.line.dash_style = 4; c.name = f"Agenda path {i + 1}"
    for i, it in enumerate(items):
        x, y = xs[i], ys[i]
        C.rect(slide, x, y, tw, th, fill=B.WHITE, line=B.LINE, name=f"Agenda {i + 1} tile")
        d = 0.85
        C.rect(slide, x + tw / 2 - d / 2, y + 0.18, d, d, fill=B.WHITE, line=ctx.accent if i else B.TEXT_RED, line_w=1.75,
               name=f"Agenda {i + 1} ring", shape=MSO_SHAPE.OVAL)
        _num(slide, x + tw / 2 - d / 2, y + 0.18, d, d, i, 20, B.BLACK, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
             name=f"Agenda {i + 1} number")
        _txt(slide, x + pad, y + 1.3, tw - 2 * pad, th - 1.4, it, size, align=PP_ALIGN.CENTER, name=f"Agenda {i + 1} title", line=1.2)


@variant("items.pill-list", "items", (41, 47), 2, 5, needs_image=True)
def items_pills(slide, items, ctx):
    """Tall rounded key visual left; items as dark pill bars with a white icon disc (ref p41/p47)."""
    pw = 4.4
    pic = picture(slide, ctx.kv.pick(ctx.title + " " + " ".join(map(_item_title, items))), M, TOP + 0.05, pw, BOT - TOP - 0.05,
                  name="Items visual")
    _geom(pic, "roundRect", [9000])
    n = len(items); has_body = any(_item_body(i) for i in items)
    row = min(1.55 if has_body else 1.3, (BOT - TOP - 0.1) / n); ph = row - 0.24
    y0 = TOP + 0.05 + (BOT - TOP - 0.05 - row * n) / 2 + 0.12
    xmax = M + pw + 0.45 + (0.4 if n >= 3 else 0)
    tw_min = SW_IN - M - xmax - (ph - 0.16) - 0.7
    titles = [_item_title(i) for i in items]
    size = _common(titles, tw_min, (0.42 if has_body else ph - 0.12), [24, 22, 20, 18, 16, 14], max_lines=1 if has_body else 2)
    for i, it in enumerate(items):
        bow = 0.4 * (1 - abs(2 * i / (n - 1) - 1)) if n >= 3 else 0
        x = M + pw + 0.45 + bow; y = y0 + i * row; w = SW_IN - M - x
        pill = C.rect(slide, x, y, w, ph, fill=B.GRAPHITE if i % 2 == 0 else B.BLACK, name=f"Item {i + 1} bar",
                      shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        pill.adjustments[0] = 0.5
        d = ph - 0.16
        _icon_disc(slide, it["icon"], x + 0.08 + d / 2, y + ph / 2, d, B.WHITE, ctx.accent, f"Item {i + 1} disc")
        tx = x + d + 0.4; tw = w - d - 0.7
        if _item_body(it):
            _txt(slide, tx, y + 0.12, tw, 0.45, titles[i], size, B.WHITE, name=f"Item {i + 1} title")
            _txt(slide, tx, y + 0.58, tw, ph - 0.62, it["body"], 12, B.MIST, name=f"Item {i + 1} text", line=1.25)
        else:
            _txt(slide, tx, y, tw, ph, titles[i], size, B.WHITE, anchor=MSO_ANCHOR.MIDDLE, name=f"Item {i + 1} title", line=1.15)


@variant("items.slant-panels", "items", (92, 96, 97), 3, 4, needs_image=True)
def items_slant(slide, items, ctx):
    """Slanted key-visual panels, one per item, each with a matching dark label (ref p92/p96/p97)."""
    n = len(items); s = 0.55; gap = 0.12
    pw = (W + (n - 1) * (s - gap)) / n
    tw = pw - s - 0.35
    titles = [_item_title(i) for i in items]
    size = _common(titles, tw, 1.0, [22, 20, 18, 16, 14], max_lines=3, line=1.15)
    nl = max(_lines(t, size, tw) for t in titles)
    lh = 0.6 + nl * size * 1.2 / 72 + 0.15; ph = BOT - TOP - 0.05 - lh - 0.1
    off = s * lh / ph                                       # same slope for the label
    for i, it in enumerate(items):
        x = M + i * (pw - s + gap)
        pic = picture(slide, ctx.kv.pick(titles[i]), x, TOP + 0.05, pw, ph, name=f"Item {i + 1} visual")
        _geom(pic, "parallelogram", [s / min(pw, ph) * 100000])
        lx, lw = x - off, pw - s + 2 * off
        lab = C.rect(slide, lx, TOP + 0.05 + ph + 0.1, lw, lh, fill=B.BLACK if i % 2 == 0 else B.GRAPHITE,
                     name=f"Item {i + 1} label", shape=MSO_SHAPE.PARALLELOGRAM)
        lab.adjustments[0] = off / min(lw, lh)
        ly = TOP + 0.05 + ph + 0.1
        _num(slide, x + 0.12, ly + 0.14, 0.6, 0.3, i, 12, B.MIST, name=f"Item {i + 1} number")
        _txt(slide, x + 0.12, ly + 0.45, tw, lh - 0.45, titles[i], size, B.WHITE, name=f"Item {i + 1} title", line=1.15)


@variant("items.overlap-cards", "items", (62, 44), 3, 4, needs_image=True)
def items_overlap(slide, items, ctx):
    """Key-visual band with white icon cards overlapping its lower edge (ref p62/p44)."""
    n = len(items); gap = 0.3; cw = (W - 0.8 - gap * (n - 1)) / n; tw = cw - 0.6
    titles = [_item_title(i) for i in items]
    size = _common(titles, tw, 1.3, [22, 20, 18, 16], max_lines=3)
    nl = max(_lines(t, size, tw) for t in titles)
    body_h = 1.2 if any(_item_body(i) for i in items) else 0
    ch = 1.2 + nl * size * 1.2 / 72 + 0.25 + body_h + 0.45; cy = BOT - ch
    picture(slide, ctx.kv.pick(ctx.title + " " + " ".join(titles)), M, TOP + 0.05, W, cy - TOP + 0.6, name="Items visual")
    for i, it in enumerate(items):
        x = M + 0.4 + i * (cw + gap)
        C.rect(slide, x, cy, cw, ch, fill=B.WHITE, line=B.LINE, name=f"Card {i + 1}")
        C.rect(slide, x, cy, cw, 0.05, fill=B.RED if i == 0 else ctx.accent, name=f"Card {i + 1} top rule")
        _icon_disc(slide, it["icon"], x + 0.65, cy + 0.62, 0.72, ctx.accent_block, B.WHITE, f"Card {i + 1} disc")
        _num(slide, x + cw - 1.0, cy + 0.45, 0.7, 0.35, i, 13, B.SLATE, align=PP_ALIGN.RIGHT, name=f"Card {i + 1} number")
        th = nl * size * 1.2 / 72 + 0.1
        _txt(slide, x + 0.3, cy + 1.2, tw, th, titles[i], size, name=f"Card {i + 1} title", line=1.2)
        if _item_body(it):
            _txt(slide, x + 0.3, cy + 1.25 + th, tw, body_h, it["body"], 14, B.SLATE, name=f"Card {i + 1} text", line=1.35)


@variant("items.zigzag", "items", (65, 71, 72), 2, 3, needs_image=True)
def items_zigzag(slide, items, ctx):
    """Alternating rows: key visual on one side, overlapping dark text block on the other (ref p65/p71)."""
    n = len(items); gap = 0.18; rh = (BOT - TOP - 0.05 - gap * (n - 1)) / n
    pw = W * 0.58; bw = W - pw + 0.6; bh = rh - 0.36; tw = bw - 1.5
    titles = [_item_title(i) for i in items]
    tb = bh - 0.3 - (0.55 if any(_item_body(i) for i in items) else 0)
    size = _common(titles, tw, tb, [26, 24, 22, 20, 18, 16], max_lines=3)
    for i, it in enumerate(items):
        y = TOP + 0.05 + i * (rh + gap); left = i % 2 == 0
        px = M if left else M + W - pw
        picture(slide, ctx.kv.pick(titles[i]), px, y, pw, rh, name=f"Item {i + 1} visual")
        bx = M + pw - 0.6 if left else M
        C.rect(slide, bx, y + 0.18, bw, bh, fill=B.GRAPHITE if left else B.BLACK, name=f"Item {i + 1} block")
        _num(slide, bx + 0.4, y + 0.18, 0.75, bh, i, 22, B.MIST, anchor=MSO_ANCHOR.MIDDLE, name=f"Item {i + 1} number")
        _txt(slide, bx + 1.15, y + 0.33, tw, tb, titles[i], size, B.WHITE, anchor=MSO_ANCHOR.MIDDLE, name=f"Item {i + 1} title", line=1.2)
        if _item_body(it):
            _txt(slide, bx + 1.15, y + 0.18 + bh - 0.65, tw, 0.5, it["body"], 13, B.MIST, name=f"Item {i + 1} text", line=1.25)


@variant("items.quad-center", "items", (177, 178), 4, 4, needs_image=True)
def items_quad(slide, items, ctx):
    """2×2 field of Paper blocks around a central round key visual (ref p177/p178)."""
    cx, cy = M + W / 2, (TOP + 0.05 + BOT) / 2
    bw, bh = W / 2 - 0.08, (BOT - TOP - 0.05) / 2 - 0.08
    d = 2.4; tw = bw - 0.45 - d / 2 - 0.55
    titles = [_item_title(i) for i in items]
    size = _common(titles, tw, 0.95, [24, 22, 20, 18, 16], max_lines=2)
    for i, it in enumerate(items):
        r, c = divmod(i, 2)
        x = M if c == 0 else cx + 0.08; y = TOP + 0.05 if r == 0 else cy + 0.08
        C.rect(slide, x, y, bw, bh, fill=B.PAPER, name=f"Item {i + 1} block")
        tx = x + 0.45 if c == 0 else x + d / 2 + 0.55
        iy = y + 0.4 if r == 0 else y + bh - 1.75
        add_icon(slide, it["icon"], Inches(tx), Inches(iy), Inches(0.5), ctx.accent)
        _txt(slide, tx + 0.75, iy - 0.02, tw - 0.75, 0.55, f"{i + 1:02d}", 14, B.TEXT_RED, font=B.MONO, name=f"Item {i + 1} number")
        _txt(slide, tx, iy + 0.65, tw, 0.95, titles[i], size, name=f"Item {i + 1} title", line=1.2)
        if _item_body(it):
            _txt(slide, tx, iy + 1.25, tw, 0.5, it["body"], 13, B.SLATE, name=f"Item {i + 1} text", line=1.25)
    C.rect(slide, cx - d / 2 - 0.14, cy - d / 2 - 0.14, d + 0.28, d + 0.28, fill=B.WHITE, name="Centre ring", shape=MSO_SHAPE.OVAL)
    oval_picture(slide, ctx.kv.pick(ctx.title), cx - d / 2, cy - d / 2, d, name="Centre visual")


@variant("items.capsules", "items", (411, 415, 419), 3, 4, needs_image=True)
def items_capsules(slide, items, ctx):
    """Staggered capsule-shaped key visuals with captions underneath (ref p411/p415/p419)."""
    n = len(items); gap = 0.5; cw = min(2.4, (W - gap * (n - 1)) / n)
    x0 = M + (W - (cw * n + gap * (n - 1))) / 2
    titles = [_item_title(i) for i in items]
    size = _common(titles, cw + 0.4, 0.8, [22, 20, 18, 16, 14], max_lines=2)
    nl = max(_lines(t, size, cw + 0.4) for t in titles)
    cap_h = 0.35 + nl * size * 1.15 / 72 + (1.0 if any(_item_body(i) for i in items) else 0) + 0.15
    drop = 0.45
    ch = BOT - TOP - 0.1 - drop - cap_h - 0.2
    for i, it in enumerate(items):
        x = x0 + i * (cw + gap); y = TOP + 0.1 + (drop if i % 2 else 0)
        pic = picture(slide, ctx.kv.pick(titles[i]), x, y, cw, ch, name=f"Item {i + 1} visual")
        _geom(pic, "roundRect", [50000])
        ty = y + ch + 0.2
        _num(slide, x, ty, cw, 0.3, i, 12, B.TEXT_RED, align=PP_ALIGN.CENTER, name=f"Item {i + 1} number")
        _txt(slide, x - 0.2, ty + 0.32, cw + 0.4, nl * size * 1.15 / 72 + 0.1, titles[i], size, align=PP_ALIGN.CENTER,
             name=f"Item {i + 1} title", line=1.15)
        if _item_body(it):
            _txt(slide, x - 0.2, ty + 0.45 + nl * size * 1.15 / 72, cw + 0.4, 0.9, it["body"], 13, B.SLATE, align=PP_ALIGN.CENTER,
                 name=f"Item {i + 1} text", line=1.3)


@variant("process.loop", "process", (239,), 3, 6, needs_image=True, prefers="sequence")
def process_loop(slide, steps, ctx):
    """Steps as nodes on a closed loop around a round key visual (cycle; ref p239)."""
    cx, cy = M + W / 2, (TOP + BOT) / 2 + 0.05
    rx, ry = 3.0, 1.95
    ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - rx), Inches(cy - ry), Inches(2 * rx), Inches(2 * ry))
    C._clean(ring, None, line=B.MIST, w=1.75); ring.name = "Loop"
    d = 2.6
    oval_picture(slide, ctx.kv.pick(ctx.title + " " + " ".join(steps)), cx - d / 2, cy - d / 2, d, name="Loop visual")
    n = len(steps); tw = 2.55
    size = _common(steps, tw, 0.8, [22, 20, 18, 16, 14], max_lines=2, line=1.15)
    for i, st in enumerate(steps):
        a = -math.pi / 2 + 2 * math.pi * i / n
        nx, ny = cx + rx * math.cos(a), cy + ry * math.sin(a)
        b = a + math.pi / n                                     # direction marker half-way to the next node
        mx, my = cx + rx * math.cos(b), cy + ry * math.sin(b)
        tri = slide.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(mx - 0.1), Inches(my - 0.09), Inches(0.2), Inches(0.18))
        C._clean(tri, B.SLATE); tri.name = f"Loop marker {i + 1}"
        tri.rotation = math.degrees(math.atan2(ry * math.cos(b), -rx * math.sin(b))) + 90
        C.rect(slide, nx - 0.36, ny - 0.36, 0.72, 0.72, fill=B.TEXT_RED if i == 0 else ctx.accent_block, name=f"Step {i + 1} node",
               shape=MSO_SHAPE.OVAL)
        _num(slide, nx - 0.36, ny - 0.36, 0.72, 0.72, i, 14, B.WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
             name=f"Step {i + 1} number")
        right = math.cos(a) >= -1e-6
        tx = nx + 0.52 if right else nx - 0.52 - tw
        _txt(slide, tx, ny - 0.4, tw, 0.8, st, size, align=PP_ALIGN.LEFT if right else PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE,
             name=f"Step {i + 1} title", line=1.15)


@variant("process.staircase", "process", (438, 439, 444), 3, 5, prefers="sequence")
def process_stairs(slide, steps, ctx):
    """Rising columns, one per step, with an arrow above the tops (stepped growth; ref p438/p439/p444)."""
    n = len(steps); gap = 0.14; cw = (W - gap * (n - 1)) / n
    h0 = 1.75; top_last = TOP + 0.85; dh = ((BOT - top_last) - h0) / (n - 1)
    size = _common(steps, cw - 0.5, 1.0, [24, 22, 20, 18, 16], max_lines=2, line=1.15)
    for i, st in enumerate(steps):
        x = M + i * (cw + gap); h = h0 + i * dh; y = BOT - h
        C.rect(slide, x, y, cw, h, fill=B.GRAPHITE if i % 2 == 0 else B.BLACK, name=f"Step {i + 1} column")
        if i == n - 1: C.rect(slide, x, y, cw, 0.06, fill=B.RED, name="Final step rule")
        C.label(slide, x + 0.25, y + 0.25, cw - 0.5, f"STEP {i + 1:02d}", color=B.MIST, size=10, name=f"Step {i + 1} label")
        _txt(slide, x + 0.25, y + 0.6, cw - 0.5, 1.0, st, size, B.WHITE, name=f"Step {i + 1} title", line=1.15)
    lift = 0.38                                            # parallel to the column corners, never crossing a top
    x1, y1 = M + 0.15, BOT - h0 - lift
    x2 = M + (n - 1) * (cw + gap) + cw * 0.85
    y2 = y1 - (x2 - x1) * dh / (cw + gap)
    c = slide.shapes.add_connector(1, Inches(x1), Inches(y1), Inches(x2), Inches(max(TOP + 0.1, y2)))
    c.line.color.rgb = C.rgb(ctx.accent); c.line.width = Pt(1.5); c.name = "Growth arrow"; _arrow_end(c)


@variant("process.numbered-panels", "process", (100, 156, 201), 3, 5, needs_image=True, prefers="sequence")
def process_panels(slide, steps, ctx):
    """Key-visual panels per step with a dark caption bar carrying a large mono numeral (ref p100/p156/p201)."""
    n = len(steps); gap = 0.12; cw = (W - gap * (n - 1)) / n
    bar = 1.2; ph = BOT - TOP - 0.05 - bar
    big = 54 if cw > 2.6 else 40; nw = 0.9 if big == 54 else 0.65; tw = cw - nw - 0.4
    size = _common(steps, tw, bar - 0.2, [22, 20, 18, 16, 14], max_lines=2, line=1.15)
    for i, st in enumerate(steps):
        x = M + i * (cw + gap)
        picture(slide, ctx.kv.pick(st), x, TOP + 0.05, cw, ph, name=f"Step {i + 1} visual")
        C.rect(slide, x, TOP + 0.05 + ph, cw, bar, fill=B.BLACK if i % 2 == 0 else B.GRAPHITE, name=f"Step {i + 1} bar")
        _txt(slide, x + 0.18, TOP + 0.05 + ph, nw, bar, str(i + 1), big, B.WHITE, font=B.MONO, anchor=MSO_ANCHOR.MIDDLE,
             name=f"Step {i + 1} number")
        _txt(slide, x + nw + 0.25, TOP + 0.05 + ph, tw, bar, st, size, B.WHITE, anchor=MSO_ANCHOR.MIDDLE, name=f"Step {i + 1} title", line=1.15)


@variant("text.framed-visual", "text", (49, 63), 1, 3, needs_image=True)
def text_framed(slide, lines, ctx):
    """Key visual in an offset frame; the first statement leads, others follow numbered (ref p49/p63)."""
    pw, ph = 5.0, BOT - TOP - 0.55
    C.rect(slide, M + 0.28, TOP + 0.33, pw, ph, fill=None, line=B.MIST, line_w=1.25, name="Visual frame")
    picture(slide, ctx.kv.pick(ctx.title + " " + " ".join(lines)), M, TOP + 0.05, pw, ph, name="Text visual")
    x = M + pw + 0.85; tw = SW_IN - M - x
    n = len(lines)
    lead = _common(lines[:1], tw, 2.4 if n > 1 else 3.6, [36, 32, 30, 28, 26, 24, 22], line=1.3)
    lead_h = _lines(lines[0], lead, tw) * lead * 1.3 / 72 + 0.1
    rest = _common(lines[1:], tw - 0.75, 1.0, [22, 20, 18, 16], line=1.3) if n > 1 else 0
    rows = [_lines(l, rest, tw - 0.75) * rest * 1.3 / 72 + 0.45 for l in lines[1:]]
    total = 0.4 + lead_h + (0.35 + sum(rows) if rows else 0)
    y = TOP + 0.05 + max(0.2, (ph - total) / 2)
    C.rect(slide, x, y, 0.6, 0.05, fill=B.RED, name="Lead rule")
    y += 0.4
    _txt(slide, x, y, tw, lead_h, lines[0], lead, name="Statement 1", line=1.25)
    y += lead_h + 0.35
    for i, (ln, rh) in enumerate(zip(lines[1:], rows), 1):
        C.hline(slide, x, y, tw, name=f"Statement {i + 1} rule")
        _num(slide, x, y + 0.22, 0.7, 0.35, i, 13, B.TEXT_RED, name=f"Statement {i + 1} number")
        _txt(slide, x + 0.75, y + 0.18, tw - 0.75, rh - 0.25, ln, rest, B.GRAPHITE, name=f"Statement {i + 1}", line=1.25)
        y += rh


@variant("text.thumb-list", "text", (127, 104), 2, 4, needs_image=True, prefers="long")
def text_thumbs(slide, lines, ctx):
    """Statement rows, each with a mono index block and a key-visual thumbnail at the end (ref p127/p104)."""
    n = len(lines); gap = 0.16; rh = (BOT - TOP - 0.05 - gap * (n - 1)) / n
    tw_img = 3.0; tx = M + 1.25; tw = W - tw_img - 1.6
    size = _common(lines, tw, rh - 0.25, [24, 22, 20, 18, 16], line=1.3)
    for i, ln in enumerate(lines):
        y = TOP + 0.05 + i * (rh + gap)
        C.rect(slide, M, y, W, rh, fill=B.PAPER, name=f"Row {i + 1}")
        C.rect(slide, M, y, 0.9, rh, fill=B.GRAPHITE if i % 2 == 0 else B.BLACK, name=f"Row {i + 1} index block")
        _num(slide, M, y, 0.9, rh, i, 18, B.WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Row {i + 1} number")
        picture(slide, ctx.kv.pick(ln), M + W - tw_img, y, tw_img, rh, name=f"Row {i + 1} visual")
        _txt(slide, tx, y, tw, rh, ln, size, anchor=MSO_ANCHOR.MIDDLE, name=f"Row {i + 1} text", line=1.25)


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
