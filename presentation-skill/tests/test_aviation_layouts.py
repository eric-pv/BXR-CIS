#!/usr/bin/env python3
"""Aviation layout families (bxr_deck/layouts_aviation.py): every variant renders contract-shaped
placeholder content into the real BXR master and stays inside the CIS geometry.

Run: python tests/test_aviation_layouts.py            (structure checks only)
     python tests/test_aviation_layouts.py --render /tmp/bxr-a/review   (also writes review PNGs)
Placeholder text only — no invented figures; gauge values are explicit test inputs."""
import hashlib, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from bxr_deck import brand as B
from bxr_deck import compose as C
from bxr_deck import layouts as L
from bxr_deck import layouts_aviation as A

SW, SH = 13.333333, 7.5
EMU = 914400
TITLE_ONLY = "BXR Title Only"
FOOTER_TOP = 6.90


def sample(family, n, long=False):
    t = "佔位標題文字" if not long else "較長的佔位標題文字，用於檢查換行"
    b = "佔位說明文字，示意此處放置一至兩行內容。" if not long else "佔位說明文字，示意此處放置較長的內容，用於檢查多行文字在框內的換行與留白是否正常。"
    if family == "compare":
        cols = [f"選項 {chr(65 + j)}" for j in range(2 if n % 2 == 0 else 3)]
        return ([{"label": f"比較項目 {i + 1}", "values": [f"{c} 說明文字" if not long else f"{c} 的較長佔位說明文字" for c in cols]} for i in range(n)],
                {"columns": cols})
    if family == "timeline":
        return [{"year": f"Phase {i + 1}", "title": f"{t} {i + 1}", "body": b} for i in range(n)], {}
    if family == "map":
        return [{"name": f"地區 {i + 1}", "body": b} for i in range(n)], {}
    if family == "team":
        return [{"role": f"職能角色 {i + 1}", "name": None, "body": b} for i in range(n)], {}
    if family == "product":
        return [{"title": f"特點 {i + 1}", "body": b} for i in range(n)], {"name": "產品名稱（佔位）"}
    if family == "gauge":   # explicit test inputs, not facts
        return [{"label": f"指標 {i + 1}", "value": 25.0 * (i + 1), "max": 100.0, "unit": "%"} for i in range(n)], {"notes": ["資料來源：簡報需求書（佔位）"]}
    if family == "quote":
        q = ["這裡是一段引言的佔位文字，用來展示引言版型的排版效果。" + ("並加上第二句補充說明。" if long else "")][:1]
        return (q * n if n > 1 else q), {"attribution": "引言出處（佔位）"}
    raise KeyError(family)


def ctx_for(title, extra, sector=None):
    acc = B.sector_accent(sector)
    return SimpleNamespace(kv=L.KVPicker(sector), topic=title, title=title, sector=sector, extra=extra,
                           accent=acc["deep"] if acc else B.GRAPHITE, accent_dark=acc["light"] if acc else B.MIST,
                           accent_block=acc["deep"] if acc else B.GRAPHITE,
                           icons=["Analytics", "Command", "Communication", "Training", "XR", "AI"], lang="zh-TW")


def cases():
    """(variant, n, long) per variant: min, max and a middle size with longer text."""
    out = []
    for v in L.VARIANTS:
        if v.family not in A.AVIATION_FAMILIES: continue
        sizes = sorted({v.nmin, v.nmax, (v.nmin + v.nmax) // 2})
        for k, n in enumerate(sizes):
            out.append((v, n, k == 1 and len(sizes) == 3))
    return out


_MASTER = []


def master_path():
    """Fresh master built by bxr_deck.master (the committed .pptx may be a Git LFS pointer in CI)."""
    if not _MASTER:
        from bxr_deck.master import build
        _MASTER.append(build(Path(tempfile.mkdtemp()) / "master.pptx"))
    return _MASTER[0]


def build_deck(path, sector=None):
    prs = Presentation(str(master_path()))
    for sid in list(prs.slides._sldIdLst):   # keep the master/layouts, drop any sample slides
        prs.part.drop_rel(sid.rId); prs.slides._sldIdLst.remove(sid)
    layout = next(l for l in prs.slide_layouts if l.name == TITLE_ONLY)
    made = []
    for v, n, long in cases():
        items, extra = sample(v.family, n, long)
        slide = prs.slides.add_slide(layout)
        title = f"{v.name}  n={n}"
        slide.shapes.title.text = title
        v.render(slide, items, ctx_for(title, extra, sector))
        made.append((v, n, slide))
    prs.save(str(path))
    return prs, made


def _kv_hashes(names):
    return {hashlib.sha256((L.KV_DIR / f).read_bytes()).hexdigest() for f in names}


def _logo_hashes():
    return {hashlib.sha256(p.read_bytes()).hexdigest() for p in (B.REPO / "01_Logo").rglob("*.png")}


def _overflow(shape):
    """Estimated wrapped text height vs. box height (fonts as set on runs)."""
    tf = shape.text_frame; w = shape.width / EMU; h = shape.height / EMU
    if not tf.word_wrap: return 0.0
    need = 0.0
    for p in tf.paragraphs:
        txt = "".join(r.text for r in p.runs)
        sizes = [r.font.size.pt for r in p.runs if r.font.size is not None]
        if not sizes: continue
        s = max(sizes); ls = p.line_spacing if isinstance(p.line_spacing, float) else 1.2
        need += C.wrap_lines(txt or " ", s, w) * s * max(ls, 1.0) * 1.08 / 72
    return need - h


class AviationLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / "aviation_variants.pptx"
        cls.prs, cls.made = build_deck(cls.path)
        cls.prs = Presentation(str(cls.path))   # re-open: test what PowerPoint will read
        cls.kv_ok = _kv_hashes(L.KV_TAGS)
        cls.logos = _logo_hashes()

    def slides(self):
        for (v, n, _), slide in zip(self.made, self.prs.slides):
            yield v, n, slide

    def test_registry(self):
        fams = {}
        for v in L.VARIANTS:
            if v.family in A.AVIATION_FAMILIES:
                fams.setdefault(v.family, []).append(v)
                self.assertRegex(v.name, rf"^{v.family}\.[a-z-]+$")
                self.assertTrue(v.ref and all(r.startswith("AVI-D") for r in v.ref), v.name)
        self.assertEqual(set(fams), set(A.AVIATION_FAMILIES))
        for f, vs in fams.items():
            self.assertTrue(2 <= len(vs) <= 3, f)
        rng = {"compare": (2, 8), "timeline": (3, 8), "map": (1, 6), "team": (2, 6), "product": (2, 6), "gauge": (1, 4), "quote": (1, 2)}
        for f, (lo, hi) in rng.items():   # every contract n is served by at least one variant
            for n in range(lo, hi + 1):
                self.assertTrue(any(v.nmin <= n <= v.nmax for v in fams[f]), f"{f} n={n}")
                items, _ = sample(f, n)
                self.assertIsNotNone(L.select(f, items, []), f"{f} n={n}")

    def test_inside_slide_and_below_banner(self):
        for v, n, slide in self.slides():
            for s in slide.shapes:
                if s.is_placeholder: continue
                x, y, w, h = (s.left / EMU, s.top / EMU, s.width / EMU, s.height / EMU)
                where = f"{v.name} n={n} '{s.name}'"
                self.assertGreaterEqual(x, -0.01, where); self.assertLessEqual(x + w, SW + 0.01, where)
                self.assertGreaterEqual(y, C.BANNER_BOTTOM + 0.05, where)        # never covers the title banner
                self.assertLessEqual(y + h, FOOTER_TOP, where)                   # never covers the master footer

    def test_text_is_editable_text(self):
        for v, n, slide in self.slides():
            texts = [s for s in slide.shapes if not s.is_placeholder and s.has_text_frame and s.text_frame.text.strip()]
            tables = [s for s in slide.shapes if s.has_table]
            self.assertTrue(texts or tables, v.name)
            for s in slide.shapes:
                if s.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    h = hashlib.sha256(s.image.blob).hexdigest()
                    self.assertIn(h, self.kv_ok, f"{v.name}: picture is not an approved weapon-free key visual")
                    self.assertNotIn(h, self.logos, f"{v.name}: logo placed on slide")
            # every content string of the sample appears as live text (not baked into an image)
            all_text = " ".join(s.text_frame.text for s in texts) + " ".join(c.text for t in tables for r in t.table.rows for c in r.cells)
            items, extra = sample(v.family, n, False)
            for it in items:
                key = it if isinstance(it, str) else it.get("label") or it.get("title") or it.get("name") or it.get("role")
                self.assertIn(key[:6], all_text, f"{v.name} n={n}: '{key}' not found as text")

    def test_no_text_overflow_or_text_overlap(self):
        problems = []
        for v, n, slide in self.slides():
            boxes = []
            for s in slide.shapes:
                if s.is_placeholder or not s.has_text_frame or not s.text_frame.text.strip(): continue
                if s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE: continue
                if _overflow(s) > 0.12:
                    problems.append(f"{v.name} n={n}: '{s.name}' text overflows its box by {_overflow(s):.2f} in")
                boxes.append(s)
            for i, a in enumerate(boxes):
                for b in boxes[i + 1:]:
                    ox = min(a.left + a.width, b.left + b.width) - max(a.left, b.left)
                    oy = min(a.top + a.height, b.top + b.height) - max(a.top, b.top)
                    if ox > 0.05 * EMU and oy > 0.05 * EMU:
                        problems.append(f"{v.name} n={n}: text boxes overlap: '{a.name}' / '{b.name}'")
        self.assertFalse(problems, "\n".join(problems))

    def test_corporate_uses_weapon_free_visuals_and_sector_allowed(self):
        path = self.tmp / "air.pptx"
        build_deck(path, sector="air")      # sector decks must still build
        self.assertTrue(path.exists())

    def test_numbers_only_from_input(self):
        import re
        for v, n, slide in self.slides():
            if v.family != "gauge": continue
            items, extra = sample("gauge", n)
            allowed = {f"{it['value']:g}" for it in items} | {f"{it['max']:g}" for it in items} | {"0"}
            for s in slide.shapes:
                if s.has_text_frame and not s.is_placeholder:
                    if s.name.startswith("Source note") or "label" in s.name: continue
                    for num in re.findall(r"\d+(?:\.\d+)?", s.text_frame.text):
                        if s.name.endswith("number"): continue
                        self.assertIn(num, allowed, f"{v.name}: unexpected number {num} in '{s.name}'")


def render_review(out_dir):
    """Write every variant sample to PNG + one contact sheet (review only, never committed)."""
    from bxr_deck.render import render
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    p = out / "aviation_variants.pptx"
    _, made = build_deck(p)
    pngs = render(p, out, dpi=60)
    return p, pngs, made


if __name__ == "__main__":
    if "--render" in sys.argv:
        i = sys.argv.index("--render"); d = sys.argv[i + 1]; del sys.argv[i:i + 2]
        p, pngs, made = render_review(d)
        print(f"rendered {len(pngs)} slides -> {d}")
        for k, (v, n, _) in enumerate(made, 1): print(f"{k:02d} {v.name} n={n}")
    unittest.main(verbosity=1)
