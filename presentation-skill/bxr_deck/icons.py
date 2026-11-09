"""Convert the official 24x24 stroke SVG icons (04_Graphics/Icons/BXR_Icon_*.svg) into native
PowerPoint freeform shapes (DrawingML custGeom). Result: crisp, recolourable, editable icons —
no PNG pasting. Supports the SVG subset used by the official set: path (M L H V C S Q A Z, abs/rel)
and circle."""
import math, re
from pathlib import Path
from lxml import etree
from . import brand as B

TOKEN = re.compile(r"[MmLlHhVvCcSsQqAaZz]|-?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?")
SVG_NS = "{http://www.w3.org/2000/svg}"


def _arc_to_beziers(x1, y1, rx, ry, phi, fa, fs, x2, y2):
    """SVG endpoint arc -> list of cubic segments (each 3 points). Standard F.6 conversion."""
    if rx == 0 or ry == 0:
        return [((x1, y1), (x2, y2), (x2, y2))]
    phi = math.radians(phi); cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1: rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = math.sqrt(max(0, num / den)) * (-1 if fa == fs else 1)
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx, cy = cp * cxp - sp * cyp + (x1 + x2) / 2, sp * cxp + cp * cyp + (y1 + y2) / 2
    ang = lambda ux, uy, vx, vy: math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not fs and dt > 0: dt -= 2 * math.pi
    if fs and dt < 0: dt += 2 * math.pi
    n = max(1, int(math.ceil(abs(dt) / (math.pi / 2))))
    seg, out = dt / n, []
    k = 4 / 3 * math.tan(seg / 4)
    pt = lambda t: (cx + rx * math.cos(t) * cp - ry * math.sin(t) * sp, cy + rx * math.cos(t) * sp + ry * math.sin(t) * cp)
    der = lambda t: (-rx * math.sin(t) * cp - ry * math.cos(t) * sp, -rx * math.sin(t) * sp + ry * math.cos(t) * cp)
    for i in range(n):
        a, b = t1 + i * seg, t1 + (i + 1) * seg
        p0, p3 = pt(a), pt(b); d0, d3 = der(a), der(b)
        out.append(((p0[0] + k * d0[0], p0[1] + k * d0[1]), (p3[0] - k * d3[0], p3[1] - k * d3[1]), p3))
    return out


def parse_path(d):
    """Return list of subpaths; each = list of ops ('M',pt) ('L',pt) ('C',p1,p2,p3) ('Z',)."""
    toks = TOKEN.findall(d); i = 0; cmd = None
    cur = start = (0.0, 0.0); last_c = None; subs = []; ops = None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if re.fullmatch(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                if ops is not None: ops.append(("Z",))
                cur = start; last_c = None; continue
        rel = cmd.islower(); c = cmd.upper()
        ox, oy = cur if rel else (0, 0)
        if c == "M":
            x, y = num() + ox, num() + oy
            ops = [("M", (x, y))]; subs.append(ops); cur = start = (x, y); cmd = "l" if rel else "L"; last_c = None
        elif c == "L":
            cur = (num() + ox, num() + oy); ops.append(("L", cur)); last_c = None
        elif c == "H":
            cur = (num() + (cur[0] if rel else 0), cur[1]); ops.append(("L", cur)); last_c = None
        elif c == "V":
            cur = (cur[0], num() + (cur[1] if rel else 0)); ops.append(("L", cur)); last_c = None
        elif c == "C":
            p1 = (num() + ox, num() + oy); p2 = (num() + ox, num() + oy); p3 = (num() + ox, num() + oy)
            ops.append(("C", p1, p2, p3)); cur = p3; last_c = p2
        elif c == "S":
            p1 = (2 * cur[0] - last_c[0], 2 * cur[1] - last_c[1]) if last_c else cur
            p2 = (num() + ox, num() + oy); p3 = (num() + ox, num() + oy)
            ops.append(("C", p1, p2, p3)); cur = p3; last_c = p2
        elif c == "Q":
            q = (num() + ox, num() + oy); p3 = (num() + ox, num() + oy)
            p1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
            p2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
            ops.append(("C", p1, p2, p3)); cur = p3; last_c = None
        elif c == "A":
            rx, ry, phi, fa, fs = num(), num(), num(), num(), num()
            x, y = num() + ox, num() + oy
            for seg in _arc_to_beziers(cur[0], cur[1], rx, ry, phi, int(fa), int(fs), x, y):
                ops.append(("C",) + seg)
            cur = (x, y); last_c = None
        else:
            raise ValueError("unsupported path command " + cmd)
    return subs


def circle_path(cx, cy, r):
    k = 0.5522847498 * r
    return [[("M", (cx + r, cy)), ("C", (cx + r, cy + k), (cx + k, cy + r), (cx, cy + r)),
             ("C", (cx - k, cy + r), (cx - r, cy + k), (cx - r, cy)),
             ("C", (cx - r, cy - k), (cx - k, cy - r), (cx, cy - r)),
             ("C", (cx + k, cy - r), (cx + r, cy - k), (cx + r, cy)), ("Z",)]]


def load_icon(name):
    """Return list of (subpaths, stroke_width_units, filled) for BXR_Icon_<name>.svg."""
    path = B.ICONS / f"BXR_Icon_{name}.svg"
    root = etree.parse(str(path)).getroot()
    base_w = float(root.get("stroke-width", 2))
    parts = []
    for el in root.iter():
        tag = etree.QName(el).localname
        sw = float(el.get("stroke-width", base_w))
        filled = el.get("fill") not in (None, "none")
        if tag == "path":
            parts.append((parse_path(el.get("d")), sw, filled))
        elif tag == "circle":
            parts.append((circle_path(float(el.get("cx")), float(el.get("cy")), float(el.get("r"))), sw, filled))
    return parts


def available():
    return sorted(p.stem.replace("BXR_Icon_", "") for p in B.ICONS.glob("BXR_Icon_*.svg"))


def icon_xml(name, x_emu, y_emu, size_emu, color, shape_id, stroke_scale=1.0):
    """Group of freeform shapes (one per stroke width) sized size x size EMU."""
    unit = size_emu / 24.0
    shapes = []
    for k, (subs, sw, filled) in enumerate(load_icon(name)):
        W = 24000  # path coordinate space (1/1000 of SVG unit)
        def P(pt): return f'<a:pt x="{int(round(pt[0] * 1000))}" y="{int(round(pt[1] * 1000))}"/>'
        cmds = []
        for sub in subs:
            for op in sub:
                if op[0] == "M": cmds.append(f"<a:moveTo>{P(op[1])}</a:moveTo>")
                elif op[0] == "L": cmds.append(f"<a:lnTo>{P(op[1])}</a:lnTo>")
                elif op[0] == "C": cmds.append(f"<a:cubicBezTo>{P(op[1])}{P(op[2])}{P(op[3])}</a:cubicBezTo>")
                elif op[0] == "Z": cmds.append("<a:close/>")
        fill = f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>' if filled else "<a:noFill/>"
        path_fill = "" if filled else ' fill="none"'
        lw = int(round(sw * unit * stroke_scale))
        shapes.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id + 1 + k}" name="{name} stroke {k + 1}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x_emu}" y="{y_emu}"/><a:ext cx="{size_emu}" cy="{size_emu}"/></a:xfrm>'
            f'<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
            f'<a:pathLst><a:path w="{W}" h="{W}"{path_fill}>{"".join(cmds)}</a:path></a:pathLst></a:custGeom>'
            f'{fill}<a:ln w="{lw}" cap="sq"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:miter lim="800000"/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody></p:sp>')
    return (f'<p:grpSp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            f'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<p:nvGrpSpPr><p:cNvPr id="{shape_id}" name="Icon {name}" descr="BXR official icon: {name}"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            f'<p:grpSpPr><a:xfrm><a:off x="{x_emu}" y="{y_emu}"/><a:ext cx="{size_emu}" cy="{size_emu}"/>'
            f'<a:chOff x="{x_emu}" y="{y_emu}"/><a:chExt cx="{size_emu}" cy="{size_emu}"/></a:xfrm></p:grpSpPr>'
            f'{"".join(shapes)}</p:grpSp>')


def add_icon(slide, name, x, y, size, color):
    """x,y,size in EMU. Appends native icon group to slide shape tree, returns the element."""
    from pptx.oxml import parse_xml
    tree = slide.shapes._spTree
    sid = max([int(i) for i in tree.xpath("//p:cNvPr/@id")] + [1]) + 1
    el = parse_xml(icon_xml(name, int(x), int(y), int(size), color, sid))
    tree.append(el)
    return el
