"""Build the real PowerPoint Theme + Slide Master + Slide Layouts for the BXR military-tech series.

Design (Claude, v0.1 — pending Eric's visual approval):
  * The three approved PNGs are layout *backgrounds* (<p:bg> blipFill), so they cannot be moved or
    deleted by accident and no slide carries its own copy.
  * Cover / Closing: the horizon light streak (y = 71.8 % of the frame) is the title's baseline.
    The title is bottom-anchored and "stands" on the light; a 2 px BxR-Red Reality Line starts at the
    title's left edge and runs into the cyan glow; subtitle and meta sit under the line.
  * Section: the big BxR-Red chapter number stands on the light streak right next to the flare
    (x 66 %, y 65.5 %); the chapter title hangs below the line.
  * Content: the dark top banner (0–13.8 %) carries kicker + title; its flare (x 9.8 %) sits under
    the first characters of the title. Everything below the banner is clean white body space.
  * Logos are pictures on the layouts only (H_Reverse on dark, Symbol_White on section,
    H_Color on white content footer). Slides never get their own logo.
  * Fonts/colours come from the Theme (Noto Sans TC major/minor, CIS colour scheme); text hierarchy
    comes from master txStyles + layout lstStyles. Exact sizes below are Claude's design decisions.
Run:  python -m bxr_deck.master  [--out path] [--potx]
"""
import argparse, copy, io, zipfile
from pathlib import Path
from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml import parse_xml
from . import brand as B

EMU = 914400
SW, SH = 13.333333, 7.5
NSDECL = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def e(v):  # inches -> EMU
    return int(round(v * EMU))


# ---------------------------------------------------------------- geometry (inches) — design tokens
L_COVER = 5.60            # cover/closing text column (right ~58 % of frame, clear of artwork)
HORIZON_COVER = 5.388     # 71.84 % of 7.5 in — measured light streak
L_SEC = 7.70              # section text column, right of the diagonal panels
HORIZON_SEC = 4.913       # 65.5 %
BANNER = 1.036            # content banner bottom (13.8 %)
M = 0.62                  # content side margin
RL_H = 0.022              # Reality Line thickness (~2 px at 1920)

LAYOUT_NAMES = ["BXR Cover", "BXR Section", "BXR Title + Body", "BXR Two Content",
                "BXR Title Only", "BXR Chart + Text", "BXR Closing"]


# ---------------------------------------------------------------- XML helpers
def rpr(sz=None, color=None, font=None, spc=None, scheme=None, tag="a:defRPr", lang=None):
    attrs = []
    if lang: attrs.append(f'lang="{lang}"')
    if sz: attrs.append(f'sz="{int(sz*100)}"')
    attrs.append('b="0"')
    if spc is not None: attrs.append(f'spc="{spc}"')
    inner = ""
    if color: inner += f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
    elif scheme: inner += f'<a:solidFill><a:schemeClr val="{scheme}"/></a:solidFill>'
    if font: inner += f'<a:latin typeface="{font}"/><a:ea typeface="+mn-ea"/>'
    return f'<{tag} {" ".join(attrs)}>{inner}</{tag}>'


def lvl(n=1, sz=None, color=None, font=None, spc=None, ln=None, caps=False, algn="l", bullet=False, scheme=None):
    ln_xml = f'<a:lnSpc><a:spcPct val="{int(ln*1000)}"/></a:lnSpc>' if ln else ""
    bu = "" if bullet else "<a:buNone/>"
    r = rpr(sz, color, font, spc, scheme)
    if caps: r = r.replace("<a:defRPr ", '<a:defRPr cap="all" ', 1)
    return f'<a:lvl{n}pPr marL="0" indent="0" algn="{algn}">{ln_xml}<a:spcBef><a:spcPts val="0"/></a:spcBef>{bu}{r}</a:lvl{n}pPr>'


def ph(sid, name, kind, idx, x, y, w, h, lst, prompt, anchor="t", autofit="norm", sz_hint=None, inset=0.0):
    t = f' type="{kind}"' if kind else ""
    i = f' idx="{idx}"' if idx is not None else ""
    fit = {"norm": "<a:normAutofit/>", "none": "<a:noAutofit/>", "shape": "<a:spAutoFit/>"}[autofit]
    ins = e(inset)
    paras = "".join(f'<a:p><a:r><a:rPr lang="zh-TW" dirty="0"/><a:t>{line}</a:t></a:r></a:p>' for line in prompt.split("\n"))
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph{t}{i}/></p:nvPr></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm></p:spPr>'
            f'<p:txBody><a:bodyPr vert="horz" wrap="square" lIns="{ins}" tIns="{ins}" rIns="{ins}" bIns="{ins}" anchor="{anchor}" anchorCtr="0">{fit}</a:bodyPr>'
            f'<a:lstStyle>{lst}</a:lstStyle>{paras}</p:txBody></p:sp>')


def pic(sid, name, rid, x, y, w, h, descr="Big x Reality official logo"):
    return (f'<p:pic><p:nvPicPr><p:cNvPr id="{sid}" name="{name}" descr="{descr}"/>'
            f'<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr userDrawn="1"/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


def rect(sid, name, x, y, w, h, color):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr/><p:nvPr userDrawn="1"/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')


def textbox(sid, name, x, y, w, h, runs_xml, algn="l", anchor="ctr"):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}"><a:noAutofit/></a:bodyPr><a:lstStyle/>'
            f'<a:p><a:pPr algn="{algn}"/>{runs_xml}</a:p></p:txBody></p:sp>')


def bg_xml(rid, img_path):
    """Full-bleed background with an exact 16:9 crop (no stretching of the approved art)."""
    w, h = Image.open(img_path).size
    r, target = w / h, SW / SH
    src = ""
    if abs(r - target) > 1e-6:
        if r > target:
            c = int(round((1 - target / r) / 2 * 100000)); src = f'<a:srcRect l="{c}" r="{c}"/>'
        else:
            c = int(round((1 - r / target) / 2 * 100000)); src = f'<a:srcRect t="{c}" b="{c}"/>'
    return (f'<p:bg><p:bgPr><a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="{rid}"/>{src}'
            f'<a:stretch><a:fillRect/></a:stretch></a:blipFill><a:effectLst/></p:bgPr></p:bg>')


def layout_xml(name, typ, bg, shapes, show_master=True):
    sm = "" if show_master else ' showMasterSp="0"'
    return (f'<p:sldLayout {NSDECL} type="{typ}" preserve="1"{sm}><p:cSld name="{name}">{bg}<p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            f'{"".join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def logo_size(path, h):
    w0, h0 = Image.open(path).size
    return h * w0 / h0, h


# ---------------------------------------------------------------- theme
def theme_xml(base_blob, east_asian=B.FONT):
    root = etree.fromstring(base_blob)
    ns = {"a": A}
    root.set("name", "Big x Reality CIS v3.2")
    cs = root.find(".//a:clrScheme", ns); cs.set("name", "BXR CIS v3.2")
    colors = {"dk1": B.BLACK, "lt1": B.WHITE, "dk2": B.GRAPHITE, "lt2": B.PAPER,
              # CIS chart rule: main series Graphite on light; red = single focus; teal = XR data on light
              "accent1": B.GRAPHITE, "accent2": B.RED, "accent3": B.SLATE, "accent4": B.ASH,
              "accent5": B.SIGNAL_TEAL, "accent6": B.MIST, "hlink": B.TEXT_RED, "folHlink": B.SLATE}
    for node in cs:
        tag = etree.QName(node).localname
        if tag in colors:
            for c in list(node): node.remove(c)
            etree.SubElement(node, f"{{{A}}}srgbClr", val=colors[tag])
    fs = root.find(".//a:fontScheme", ns); fs.set("name", "BXR Noto Sans")
    for fam in ("majorFont", "minorFont"):
        el = fs.find(f"a:{fam}", ns)
        for c in list(el): el.remove(c)
        etree.SubElement(el, f"{{{A}}}latin", typeface=B.FONT)
        etree.SubElement(el, f"{{{A}}}ea", typeface=east_asian)
        etree.SubElement(el, f"{{{A}}}cs", typeface=B.FONT)
        for script, face in (("Hant", B.FONT), ("Jpan", B.FONT_JP), ("Hans", B.FONT)):
            etree.SubElement(el, f"{{{A}}}font", script=script, typeface=face)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def set_east_asian_font(prs, face):
    """Switch theme East-Asian face (e.g. Noto Sans JP for JP decks) without touching slides."""
    tp = prs.slide_masters[0].part.part_related_by(RT.THEME)
    root = etree.fromstring(tp.blob)
    for ea in root.iterfind(".//a:fontScheme/*/a:ea", {"a": A}):
        ea.set("typeface", face)
    tp._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


# ---------------------------------------------------------------- master
def master_xml(layout_rids):
    body_lvls = (
        f'<a:lvl1pPr marL="{e(0.24)}" indent="{-e(0.24)}" algn="l"><a:lnSpc><a:spcPct val="120000"/></a:lnSpc>'
        f'<a:spcBef><a:spcPts val="900"/></a:spcBef><a:buClr><a:srgbClr val="{B.SLATE}"/></a:buClr><a:buSzPct val="70000"/>'
        f'<a:buFont typeface="Arial"/><a:buChar char="&#9632;"/>{rpr(18, scheme="tx2")}</a:lvl1pPr>'
        f'<a:lvl2pPr marL="{e(0.52)}" indent="{-e(0.24)}" algn="l"><a:lnSpc><a:spcPct val="120000"/></a:lnSpc>'
        f'<a:spcBef><a:spcPts val="400"/></a:spcBef><a:buClr><a:srgbClr val="{B.ASH}"/></a:buClr>'
        f'<a:buFont typeface="Arial"/><a:buChar char="&#8211;"/>{rpr(16, color=B.SLATE)}</a:lvl2pPr>'
        f'<a:lvl3pPr marL="{e(0.80)}" indent="{-e(0.22)}" algn="l"><a:lnSpc><a:spcPct val="120000"/></a:lnSpc>'
        f'<a:spcBef><a:spcPts val="300"/></a:spcBef><a:buFont typeface="Arial"/><a:buChar char="&#8211;"/>{rpr(14, color=B.SLATE)}</a:lvl3pPr>')
    for n in range(4, 10):
        body_lvls += f'<a:lvl{n}pPr marL="{e(0.80)}" indent="0"><a:buNone/>{rpr(14, color=B.SLATE)}</a:lvl{n}pPr>'
    title_rpr = rpr(30, color=B.WHITE).replace("<a:defRPr", '<a:defRPr kern="1200"')
    title_lvl = f'<a:lvl1pPr algn="l"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc><a:spcBef><a:spcPts val="0"/></a:spcBef><a:buNone/>{title_rpr}</a:lvl1pPr>'
    ids = "".join(f'<p:sldLayoutId id="{2147483649 + i}" r:id="{rid}"/>' for i, rid in enumerate(layout_rids))
    return (f'<p:sldMaster {NSDECL}><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + ph(2, "Title Placeholder 1", "title", None, M, 0.42, 8.6, 0.52, "", "按一下以編輯母片標題樣式", anchor="t")
            + ph(3, "Text Placeholder 2", "body", 1, M, 1.50, SW - 2 * M, 5.10, "", "按一下以編輯母片文字樣式\n第二層\n第三層")
            + '</p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
            'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            f'<p:sldLayoutIdLst>{ids}</p:sldLayoutIdLst>'
            f'<p:txStyles><p:titleStyle>{title_lvl}</p:titleStyle><p:bodyStyle>{body_lvls}</p:bodyStyle>'
            f'<p:otherStyle><a:lvl1pPr>{rpr(14, scheme="tx1")}</a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>')


# ---------------------------------------------------------------- layouts
def build_layouts(parts):
    """parts: list of SlideLayoutPart (>=7). Returns XML strings in LAYOUT_NAMES order."""
    def img(part, path):
        _, rid = part.get_or_add_image_part(str(path)); return rid

    kicker_dark = lambda color=B.SIM_CYAN, sz=9: lvl(1, sz, color, B.MONO, spc=180, caps=True)
    out = []

    # 1 Cover ---------------------------------------------------------------
    p = parts[0]; bg = img(p, B.BG["cover"]); lg = img(p, B.LOGO / "BXR_Logo_H_Reverse.png")
    lw, lh = logo_size(B.LOGO / "BXR_Logo_H_Reverse.png", 0.46)
    out.append(layout_xml("BXR Cover", "title", bg_xml(bg, B.BG["cover"]), [
        pic(2, "Logo (master-managed)", lg, SW - 0.70 - lw, 0.58, lw, lh),   # top-right (Eric 2026-11-09)
        ph(3, "Title", "ctrTitle", None, L_COVER, 2.10, SW - L_COVER - 0.70, HORIZON_COVER - 0.20 - 2.10,
           lvl(1, 40, B.WHITE, ln=104), "簡報標題\nPresentation title", anchor="b"),
        rect(4, "Reality Line", L_COVER, HORIZON_COVER - RL_H / 2, 0.90, RL_H, B.RED),
        ph(5, "Subtitle", "subTitle", 1, L_COVER, HORIZON_COVER + 0.19, SW - L_COVER - 0.70, 0.62,
           lvl(1, 16, B.MIST, ln=115), "副標題｜簡報目的與對象"),
        ph(6, "Meta", "body", 10, L_COVER, HORIZON_COVER + 0.86, SW - L_COVER - 0.70, 0.40,
           lvl(1, 14, B.WHITE), "2026.11 · ORGANIZATION · PRESENTER", autofit="none"),
    ], show_master=False))

    # 2 Section -------------------------------------------------------------
    p = parts[1]; bg = img(p, B.BG["section"]); lg = img(p, B.LOGO / "BXR_Symbol_White.png")
    sw_, sh_ = logo_size(B.LOGO / "BXR_Symbol_White.png", 0.44)
    out.append(layout_xml("BXR Section", "secHead", bg_xml(bg, B.BG["section"]), [
        pic(2, "Symbol (master-managed)", lg, SW - 0.70 - sw_, 0.58, sw_, sh_),
        ph(3, "Chapter Number", "body", 10, L_SEC, 2.20, 4.9, HORIZON_SEC - 0.10 - 2.20,
           lvl(1, 96, B.RED, ln=85), "01", anchor="b", autofit="none"),
        rect(4, "Reality Line", L_SEC, HORIZON_SEC - RL_H / 2, 0.80, RL_H, B.RED),
        ph(5, "Section Title", "title", None, L_SEC, HORIZON_SEC + 0.22, SW - L_SEC - 0.62, 1.05,
           lvl(1, 30, B.WHITE, ln=108), "章節名稱"),
    ], show_master=False))

    # content footer shared by layouts 3–6
    def footer(part, start_id):
        lg = img(part, B.LOGO / "BXR_Logo_H_Color.png")
        cw, ch = logo_size(B.LOGO / "BXR_Logo_H_Color.png", 0.28)
        num = (f'<a:fld id="{{B5A1D1E2-0000-4000-8000-00000000000{start_id % 10}}}" type="slidenum">'
               f'{rpr(9, B.GRAPHITE, B.MONO, tag="a:rPr", lang="en-US")}<a:t>‹#›</a:t></a:fld>')
        return [textbox(start_id, "Page Number", M, 6.93, 0.40, 0.26, num),
                rect(start_id + 1, "Reality Line", M + 0.45, 7.06 - RL_H / 2, 0.42, RL_H, B.RED),
                pic(start_id + 3, "Logo (master-managed)", lg, SW - M - cw, 6.92, cw, ch)]

    def banner(title_w=8.6):
        return [ph(3, "Title", "title", None, M, 0.14, title_w, 0.76, lvl(1, 30, B.WHITE), "內容頁標題（位於上方 Banner）", anchor="ctr")]

    content_bg = lambda part: bg_xml(img(part, B.BG["content"]), B.BG["content"])
    body_w = SW - 2 * M
    p = parts[2]; out.append(layout_xml("BXR Title + Body", "obj", content_bg(p), banner() + [
        ph(4, "Body", "body", 1, M, 1.50, body_w, 5.10, "", "內文重點\n第二層說明")] + footer(p, 10)))
    p = parts[3]; colw = (body_w - 0.40) / 2
    out.append(layout_xml("BXR Two Content", "twoObj", content_bg(p), banner() + [
        ph(4, "Left", "body", 1, M, 1.50, colw, 5.10, "", "左欄內容"),
        ph(5, "Right", "body", 2, M + colw + 0.40, 1.50, colw, 5.10, "", "右欄內容")] + footer(p, 10)))
    p = parts[4]; out.append(layout_xml("BXR Title Only", "titleOnly", content_bg(p), banner() + footer(p, 10)))
    p = parts[5]; out.append(layout_xml("BXR Chart + Text", "chart", content_bg(p), banner() + [
        ph(4, "Chart", "chart", 12, M, 1.50, 7.70, 5.10, "", "插入圖表"),
        ph(5, "Takeaway", "body", 2, M + 8.10, 1.50, body_w - 8.10, 5.10, "", "圖表重點說明")] + footer(p, 10)))

    # 7 Closing ---------------------------------------------------------------
    p = parts[6]; bg = img(p, B.BG["cover"]); lg = img(p, B.LOGO / "BXR_Logo_H_Reverse.png")
    lw, lh = logo_size(B.LOGO / "BXR_Logo_H_Reverse.png", 0.62)
    out.append(layout_xml("BXR Closing", "cust", bg_xml(bg, B.BG["cover"]), [
        pic(2, "Logo (master-managed)", lg, L_COVER, 0.62, lw, lh),
        ph(3, "Closing Line", "title", None, L_COVER, 2.60, SW - L_COVER - 0.70, HORIZON_COVER - 0.20 - 2.60,
           lvl(1, 36, B.WHITE, ln=104), "Turn every drill into real.", anchor="b"),
        rect(4, "Reality Line", L_COVER, HORIZON_COVER - RL_H / 2, 0.90, RL_H, B.RED),
        ph(5, "Closing Text", "body", 10, L_COVER, HORIZON_COVER + 0.19, SW - L_COVER - 0.70, 0.62,
           lvl(1, 14, B.MIST, ln=120), "全球動力科技股份有限公司 · bigxreality.com"),
    ], show_master=False))
    return out


def build(out_path=B.MASTER_PPTX, potx=False):
    prs = Presentation()
    prs.slide_width, prs.slide_height = e(SW), e(SH)
    master = prs.slide_masters[0]
    mpart = master.part
    tpart = mpart.part_related_by(RT.THEME)
    tpart._blob = theme_xml(tpart.blob)

    lparts = [l.part for l in master.slide_layouts]
    rid_of = {}
    for rid, rel in mpart.rels.items():
        if rel.reltype == RT.SLIDE_LAYOUT:
            rid_of[rel.target_part] = rid
    keep, drop = lparts[:len(LAYOUT_NAMES)], lparts[len(LAYOUT_NAMES):]
    for part, xml in zip(keep, build_layouts(keep)):
        part._element = parse_xml(xml.encode("utf-8"))
    mpart._element = parse_xml(master_xml([rid_of[p] for p in keep]).encode("utf-8"))
    for p in drop:
        mpart.drop_rel(rid_of[p])
    out_path = Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.core_properties.title = "Big x Reality — Military-Tech Master v0.1"
    prs.core_properties.author = "Big x Reality"
    prs.core_properties.comments = "Design: Claude (v0.1, pending visual approval). Generated by bxr_deck.master"
    prs.save(out_path)
    if potx:
        to_potx(out_path, out_path.with_suffix(".potx"))
    return out_path


def to_potx(src, dst):
    with zipfile.ZipFile(src) as z, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for item in z.infolist():
            data = z.read(item.filename)
            if item.filename == "[Content_Types].xml":
                data = data.replace(b"presentationml.presentation.main+xml", b"presentationml.template.main+xml")
            out.writestr(item, data)
    return dst


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(B.MASTER_PPTX))
    ap.add_argument("--potx", action="store_true")
    a = ap.parse_args()
    print(build(a.out, a.potx))
