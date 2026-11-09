"""Native, editable slide components on top of the BXR master layouts.

Every visible element is a PowerPoint object (placeholder, text box, autoshape, table, chart,
freeform icon). Shared typography comes from the Theme/Master; components only set the sizes that
belong to the specific composition. Red is reserved for the Reality Line / one focus (CIS)."""
from functools import lru_cache
from pathlib import Path
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt
from . import brand as B
from .icons import add_icon

SW, SH = 13.333333, 7.5
M = 0.62
BODY_TOP, BODY_BOTTOM = 1.50, 6.62
BODY_W = SW - 2 * M

# ------------------------------------------------------------------ text measurement
_FONT_FILES = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
               "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]


@lru_cache(maxsize=None)
def _font(px):
    try:
        from PIL import ImageFont
        for f in _FONT_FILES:
            if Path(f).exists():
                return ImageFont.truetype(f, px, index=3)  # TC face
    except Exception:
        pass
    return None


def text_width_in(text, pt):
    f = _font(int(pt * 4))
    if f is not None:
        return f.getlength(text) / 4 / 72
    return sum((1.0 if ord(c) > 0x2E80 else 0.56) for c in text) * pt / 72


def wrap_lines(text, pt, width_in):
    """Greedy wrap (CJK breaks anywhere, latin at spaces). Returns number of lines."""
    lines = 0
    for para in str(text).split("\n"):
        cur = ""; n = 1
        tokens = []
        word = ""
        for ch in para:
            if ord(ch) > 0x2E80:
                if word: tokens.append(word); word = ""
                tokens.append(ch)
            elif ch == " ":
                word += ch; tokens.append(word); word = ""
            else:
                word += ch
        if word: tokens.append(word)
        for t in tokens:
            if text_width_in(cur + t, pt) <= width_in or not cur:
                cur += t
            else:
                n += 1; cur = t.lstrip()
        lines += n
    return lines


def fit_size(text, width_in, height_in, sizes, line=1.2, max_lines=None):
    """Largest size in `sizes` whose wrapped text fits the box. Returns (size, lines, fits)."""
    for s in sizes:
        n = wrap_lines(text, s, width_in)
        if n * s * line / 72 <= height_in and (max_lines is None or n <= max_lines):
            return s, n, True
    s = sizes[-1]
    return s, wrap_lines(text, s, width_in), False


# ------------------------------------------------------------------ primitives
def rgb(h): return RGBColor.from_string(h)


def placeholder(slide, idx):
    for p in slide.placeholders:
        if p.placeholder_format.idx == idx:
            return p
    return None


def set_text(shape, text, size=None, color=None, font=None, lang=None):
    tf = shape.text_frame
    lines = text if isinstance(text, list) else [text]
    tf.text = ""
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = line
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = rgb(color)
        if font: r.font.name = font
    return shape


def textbox(slide, x, y, w, h, text, size=14, color=B.GRAPHITE, font=None, align=PP_ALIGN.LEFT,
            anchor=MSO_ANCHOR.TOP, name=None, line=None, caps=False, spacing=None, wrap=True):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name: tb.name = name
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text if isinstance(text, list) else [text]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line: p.line_spacing = line
        r = p.add_run(); r.text = ln
        f = r.font; f.size = Pt(size); f.color.rgb = rgb(color); f.bold = False
        if font: f.name = font
        rPr = r._r.get_or_add_rPr()
        if caps: rPr.set("cap", "all")
        if spacing is not None: rPr.set("spc", str(spacing))
    return tb


def label(slide, x, y, w, text, color=B.SLATE, size=9, name=None):
    """B612 Mono technical label (CIS Label/Technical style: caps, tracked)."""
    return textbox(slide, x, y, w, 0.22, text, size=size, color=color, font=B.MONO, caps=True, spacing=160, name=name)


def rect(slide, x, y, w, h, fill=None, line=None, line_w=0.75, name=None, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name: s.name = name
    if fill: s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    else: s.fill.background()
    if line: s.line.color.rgb = rgb(line); s.line.width = Pt(line_w)
    else: s.line.fill.background()
    style = s._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
    if style is not None: s._element.remove(style)   # no theme shadow/effects; explicit fill/line only
    if s.has_text_frame: s.text_frame.text = ""
    return s


def hline(slide, x, y, w, color=B.LINE, weight=0.75, name=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    c.line.color.rgb = rgb(color); c.line.width = Pt(weight)
    style = c._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}style")
    if style is not None: c._element.remove(style)
    if name: c.name = name
    return c


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ------------------------------------------------------------------ compositions
def bullets(slide, items, accent=None):
    """Body placeholder bullets with auto-fit size (inherits master bullet styles)."""
    body = placeholder(slide, 1)
    joined = "\n".join(items)
    size, _, fits = fit_size(joined, BODY_W - 0.3, BODY_BOTTOM - BODY_TOP, [24, 22, 20, 18, 16], line=1.45)
    set_text(body, items, size=size)
    return fits


def cards(slide, items, top=BODY_TOP + 0.05, height=None, accent=None, numbered=True):
    """2–4 equal cards: Paper block, icon/number, title, body. items: dict(title, body, icon)."""
    n = len(items); gap = 0.28
    w = (BODY_W - gap * (n - 1)) / n
    h = height or (BODY_BOTTOM - top)
    acc = accent or B.GRAPHITE
    fits = True
    for i, it in enumerate(items):
        x = M + i * (w + gap)
        rect(slide, x, top, w, h, fill=B.PAPER, name=f"Card {i + 1}")
        rect(slide, x, top, w, 0.05, fill=acc, name=f"Card {i + 1} accent")
        y = top + 0.42
        if it.get("icon"):
            add_icon(slide, it["icon"], Inches(x + 0.36), Inches(y), Inches(0.54), acc)
            y += 0.86
        if numbered:
            label(slide, x + 0.36, y, w - 0.72, f"{i + 1:02d}", color=B.SLATE, size=10, name=f"Card {i + 1} number")
            y += 0.34
        tsize, tl, f1 = fit_size(it["title"], w - 0.72, 1.0, [22, 20, 18, 16], line=1.25, max_lines=2)
        textbox(slide, x + 0.36, y, w - 0.72, 1.0, it["title"], size=tsize, color=B.BLACK, name=f"Card {i + 1} title", line=1.15)
        y += tl * tsize * 1.25 / 72 + 0.22
        if it.get("body"):
            room = top + h - y - 0.3
            bsize, _, f2 = fit_size(it["body"], w - 0.72, room, [16, 15, 14, 13, 12], line=1.5)
            textbox(slide, x + 0.36, y, w - 0.72, room, it["body"], size=bsize, color=B.SLATE, name=f"Card {i + 1} body", line=1.4)
            fits = fits and f2
        fits = fits and f1
    return fits


def process(slide, steps, accent=None, top=None):
    """Horizontal step flow: track line + square nodes + step labels/titles/descriptions."""
    n = len(steps); acc = accent or B.GRAPHITE
    top = top or (3.05 if any(isinstance(x, dict) and x.get('body') for x in steps) else 3.45)
    seg = BODY_W / n
    hline(slide, M, top, BODY_W, color=B.MIST, weight=1.25, name="Process track")
    fits = True
    for i, st in enumerate(steps):
        x = M + i * seg
        node = rect(slide, x, top - 0.11, 0.22, 0.22, fill=acc if i == 0 else B.WHITE, line=acc, line_w=1.5, name=f"Step {i + 1} node")
        label(slide, x, top + 0.36, seg - 0.3, f"STEP {i + 1:02d}", color=B.SLATE, size=10, name=f"Step {i + 1} label")
        title = st["title"] if isinstance(st, dict) else st
        tsize, tl, f1 = fit_size(title, seg - 0.35, 1.1, [26, 24, 22, 20, 18], line=1.2, max_lines=2)
        textbox(slide, x, top + 0.72, seg - 0.35, 1.1, title, size=tsize, color=B.BLACK, name=f"Step {i + 1} title", line=1.1)
        desc = st.get("body") if isinstance(st, dict) else None
        if desc:
            y = top + 0.72 + tl * tsize * 1.2 / 72 + 0.2
            bsize, _, f2 = fit_size(desc, seg - 0.4, BODY_BOTTOM - y - 0.2, [15, 14, 13, 12], line=1.5)
            textbox(slide, x, y, seg - 0.4, BODY_BOTTOM - y - 0.2, desc, size=bsize, color=B.SLATE, name=f"Step {i + 1} text", line=1.4)
            fits = fits and f2
        fits = fits and f1
    return fits


def table(slide, header, rows, top=BODY_TOP + 0.05, col_widths=None, pending_marker=None, name="Table"):
    """Native PowerPoint table, CIS styling: Graphite header, hairline rows, no zebra."""
    nrows, ncols = len(rows) + 1, len(header)
    row_h = min(0.62, (BODY_BOTTOM - top - 0.2) / nrows)
    gf = slide.shapes.add_table(nrows, ncols, Inches(M), Inches(top), Inches(BODY_W), Inches(row_h * nrows))
    gf.name = name
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    for attr in ("bandRow", "firstRow"): tblPr.set(attr, "0")
    # drop default table style id so our explicit fills rule
    sid = tblPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
    if sid is not None: sid.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # 'No Style, Table Grid'
    widths = col_widths or [BODY_W / ncols] * ncols
    for j, wv in enumerate(widths): tbl.columns[j].width = Inches(wv)
    for i in range(nrows):
        tbl.rows[i].height = Inches(row_h)
        for j in range(ncols):
            cell = tbl.cell(i, j)
            txt = header[j] if i == 0 else rows[i - 1][j]
            cell.text = ""
            p = cell.text_frame.paragraphs[0]; r = p.add_run(); r.text = str(txt)
            pending = pending_marker and str(txt).strip() == pending_marker
            r.font.size = Pt(14 if i == 0 else 15)
            r.font.color.rgb = rgb(B.WHITE if i == 0 else (B.ASH if pending else B.GRAPHITE))
            if i == 0: r.font.name = None
            cell.fill.solid(); cell.fill.fore_color.rgb = rgb(B.GRAPHITE if i == 0 else B.WHITE)
            cell.margin_left = cell.margin_right = Inches(0.16)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            _cell_borders(cell, B.LINE)
    return gf


def _cell_borders(cell, color):
    from lxml import etree
    A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("lnL", "lnR", "lnT", "lnB"):
        old = tcPr.find(f"{{{A}}}{tag}")
        if old is not None: tcPr.remove(old)
    xml = []
    for tag in ("lnL", "lnR", "lnT", "lnB"):
        if tag in ("lnL", "lnR"):
            xml.append(f'<a:{tag} xmlns:a="{A}" w="0"><a:noFill/></a:{tag}>')
        else:
            xml.append(f'<a:{tag} xmlns:a="{A}" w="9525"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:{tag}>')
    fill = tcPr.find(f"{{{A}}}solidFill")
    for x in xml:
        el = etree.fromstring(x)
        if fill is not None: fill.addprevious(el)
        else: tcPr.append(el)


def bar_chart(slide, categories, values, series_name, number_format='0', highlight=None, unit=""):
    """Native editable chart (embedded workbook) in the layout chart placeholder."""
    data = CategoryChartData(); data.categories = categories
    data.add_series(series_name, values)
    ph = placeholder(slide, 12)
    gf = ph.insert_chart(XL_CHART_TYPE.BAR_CLUSTERED, data)
    ch = gf.chart
    ch.has_legend = False; ch.has_title = False
    ch.font.size = Pt(13); ch.font.color.rgb = rgb(B.SLATE)
    plot = ch.plots[0]; plot.gap_width = 70
    plot.has_data_labels = True
    dl = plot.data_labels; dl.number_format = number_format + (f'" {unit}"' if unit else ""); dl.number_format_is_linked = False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END; dl.font.size = Pt(13); dl.font.color.rgb = rgb(B.GRAPHITE)
    ser = plot.series[0]
    ser.format.fill.solid(); ser.format.fill.fore_color.rgb = rgb(B.GRAPHITE)
    if highlight is not None:
        pt = ser.points[highlight]; pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(B.RED)
    va = ch.value_axis; va.visible = False; va.has_major_gridlines = False
    ca = ch.category_axis; ca.format.line.color.rgb = rgb(B.LINE); ca.tick_labels.font.size = Pt(13)
    ca.reverse_order = True
    return gf


def pending_box(slide, x, y, w, h, title, items, lang="zh-TW"):
    """Evidence gap callout: tells the presenter exactly what must be supplied (never invented)."""
    rect(slide, x, y, w, h, fill=B.PAPER, name="Pending input")
    rect(slide, x, y, 0.05, h, fill=B.TEXT_RED, name="Pending input bar")
    label(slide, x + 0.3, y + 0.26, w - 0.6, title, color=B.TEXT_RED, size=10, name="Pending input label")
    body = "\n".join("□  " + t for t in items)
    size, _, fits = fit_size(body, w - 0.6, h - 0.85, [16, 15, 14, 13, 12], line=1.6)
    textbox(slide, x + 0.3, y + 0.65, w - 0.6, h - 0.85, body.split("\n"), size=size, color=B.GRAPHITE, name="Pending input items", line=1.45)
    return fits


def agenda(slide, items, accent=None):
    """Numbered agenda; two columns when > 4 items."""
    cols = 2 if len(items) > 4 else 1
    per = (len(items) + cols - 1) // cols
    colw = (BODY_W - 0.6 * (cols - 1)) / cols
    row_h = min(0.95, (BODY_BOTTOM - BODY_TOP - 0.2) / per)
    for i, it in enumerate(items):
        c, r = divmod(i, per)
        x = M + c * (colw + 0.6); y = BODY_TOP + 0.15 + r * row_h
        textbox(slide, x, y, 0.9, row_h - 0.2, f"{i + 1:02d}", size=28, color=B.TEXT_RED, font=B.MONO, anchor=MSO_ANCHOR.MIDDLE, name=f"Agenda {i + 1} number")
        size, _, _ = fit_size(it, colw - 1.1, row_h - 0.2, [24, 22, 20, 18], max_lines=1)
        textbox(slide, x + 1.1, y, colw - 1.1, row_h - 0.2, it, size=size, color=B.BLACK, anchor=MSO_ANCHOR.MIDDLE, name=f"Agenda {i + 1} title")
        hline(slide, x, y + row_h - 0.08, colw, name=f"Agenda {i + 1} rule")


def statement(slide, text, sub=None):
    """One big message on white (Title Only layout) — for purpose/summary lines."""
    size, n, _ = fit_size(text, BODY_W - 2.0, 2.2, [40, 36, 32, 28], line=1.2)
    y = 2.3
    hline(slide, M, y - 0.35, 0.9, color=B.GRAPHITE, weight=1.5, name="Statement rule")
    textbox(slide, M, y, BODY_W - 2.0, 2.4, text, size=size, color=B.BLACK, name="Statement", line=1.15)
    if sub:
        textbox(slide, M, y + n * size * 1.2 / 72 + 0.35, BODY_W - 3, 1.5, sub, size=18, color=B.SLATE, name="Statement detail", line=1.4)
