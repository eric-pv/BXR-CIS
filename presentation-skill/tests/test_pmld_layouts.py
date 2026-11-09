#!/usr/bin/env python3
"""Second-pass layouts distilled from the 500-page reference library (PMLD).
Checks registration, reference-page policy, geometry, fit, editability and key-visual rules for every
variant added in the PMLD second pass, at every allowed item count, with short and long text.
Run: python tests/test_pmld_layouts.py   (needs python-pptx, lxml, pillow; no LibreOffice)"""
import csv, hashlib, json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from pptx import Presentation
from pptx.util import Inches
from bxr_deck import layouts as L, compose as C, brand as B

NEW = ["agenda.arc-nodes", "agenda.number-strip", "agenda.tiles",
       "items.pill-list", "items.slant-panels", "items.overlap-cards", "items.zigzag", "items.quad-center", "items.capsules",
       "process.loop", "process.staircase", "process.numbered-panels",
       "text.framed-visual", "text.thumb-list"]
SHORT = ["需求整理", "簡報規劃", "套用母片", "產出簡報", "品質檢查", "繁體中文", "English", "日本語"]
LONG = ["簡報需符合 CIS v3.2 的字型、色彩與 Logo 規範", "所有文字、表格與圖表必須能在 PowerPoint 中直接修改",
        "Logo 由母片統一管理，不在每一頁重複放置", "未經確認的數據一律標示待補，不自行編造"]
EMU = 914400
# Eric 2026-11-09: certificate / partner-logo walls and China maps are not reference material.
EXCLUDED_PAGES = set(range(297, 367)) | set(range(464, 501)) | set(range(502, 518)) | set(range(519, 569)) | set(range(570, 603)) | {604}
KV_HASHES = {hashlib.sha256(p.read_bytes()).hexdigest(): p.name for p in L.KV_DIR.glob("*.jpg")}
CORP_KV = {hashlib.sha256((L.KV_DIR / f).read_bytes()).hexdigest() for f in L.KV_TAGS}


class Ctx:
    def __init__(self):
        self.kv = L.KVPicker("corporate"); self.topic = "BXR 簡報系統"; self.title = "測試"
        self.accent = B.GRAPHITE; self.accent_dark = B.SIM_CYAN; self.accent_block = B.GRAPHITE
        self.extra = {"caption": None}; self.icons = ["Simulation", "Training", "Analytics", "Command"]


def _slide():
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(C.SW), Inches(C.SH)
    return prs.slides.add_slide(prs.slide_layouts[6])


def _items(v, n, long):
    src = LONG if long else SHORT
    txt = [src[i % len(src)] for i in range(n)]
    return [{"title": t, "icon": "Simulation"} for t in txt] if v.family == "items" else txt


def _cases():
    for name in NEW:
        v = next(x for x in L.VARIANTS if x.name == name)
        for n in range(v.nmin, v.nmax + 1):
            for long in (False, True):
                yield v, n, long


def _render(v, n, long):
    s = _slide(); ctx = Ctx(); v.render(s, _items(v, n, long), ctx); L._ACTIVE[0] = None
    return s, ctx


class Registration(unittest.TestCase):
    def test_all_new_variants_registered_after_existing(self):
        names = [v.name for v in L.VARIANTS]
        for n in NEW:
            self.assertIn(n, names)
        first_new = min(names.index(n) for n in NEW)
        self.assertEqual(names[:first_new].count("text.bullets"), 1, "new variants must follow the first-pass ones (tie-break order)")

    def test_registry_records(self):
        reg = json.loads((ROOT / "catalog/layout-registry.json").read_text(encoding="utf-8"))
        recs = {r["id"]: r for r in reg["layouts"]}
        for n in NEW:
            with self.subTest(variant=n):
                r = recs[n]
                self.assertEqual(r["origin"], "reference-distilled")
                self.assertFalse(r["approved"])                       # only Eric can approve
                self.assertNotEqual(r["status"], "cis-approved")
                self.assertTrue(all(s.startswith("PMLD-") for s in r["ref_slides"]))

    def test_reference_pages_exist_and_respect_policy(self):
        with open(ROOT / "catalog/generated/source-slides.csv", encoding="utf-8") as f:
            rows = {r["slide_id"]: r for r in csv.DictReader(f)}
        for n in NEW:
            v = next(x for x in L.VARIANTS if x.name == n)
            self.assertTrue(v.ref, n)
            for p in v.ref:
                with self.subTest(variant=n, page=p):
                    self.assertIsInstance(p, int)
                    self.assertIn(f"PMLD-{p:04d}", rows)
                    self.assertNotIn(p, EXCLUDED_PAGES)


class Geometry(unittest.TestCase):
    def test_inside_slide_and_below_banner(self):
        for v, n, long in _cases():
            s, _ = _render(v, n, long)
            for sh in s.shapes:
                with self.subTest(variant=v.name, n=n, long=long, shape=sh.name):
                    x, y = sh.left / EMU, sh.top / EMU
                    w, h = sh.width / EMU, sh.height / EMU
                    self.assertGreaterEqual(x, -0.01); self.assertGreaterEqual(y, C.BANNER_BOTTOM - 0.01)
                    self.assertLessEqual(x + w, C.SW + 0.01); self.assertLessEqual(y + h, 6.86)

    def test_text_fits_by_measurement(self):
        for v, n, long in _cases():
            s, _ = _render(v, n, long)
            for sh in s.shapes:
                if not sh.has_text_frame or not sh.text_frame.text.strip():
                    continue
                runs = [r for p in sh.text_frame.paragraphs for r in p.runs]
                size = runs[0].font.size.pt
                lines = sum(C.wrap_lines(p.text, size, sh.width / EMU * L._SAFE) for p in sh.text_frame.paragraphs if p.text)
                spacing = sh.text_frame.paragraphs[0].line_spacing or 1.2
                with self.subTest(variant=v.name, n=n, long=long, shape=sh.name):
                    self.assertLessEqual(lines * size * spacing / 72, sh.height / EMU + 0.12, sh.text_frame.text)
                    self.assertGreaterEqual(size, 9 if "label" in sh.name else 12 if "number" in sh.name else 14)   # 9 pt = CIS mono label style


class Editability(unittest.TestCase):
    def test_text_is_native_and_pictures_are_approved_key_visuals(self):
        for v, n, long in _cases():
            s, ctx = _render(v, n, long)
            pics = [sh for sh in s.shapes if sh.shape_type == 13]
            texts = [sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
            with self.subTest(variant=v.name, n=n, long=long):
                self.assertGreaterEqual(len(texts), n, "every item needs an editable text box")
                self.assertEqual(len(pics), v.images(n), "picture count must match the key-visual budget")
                self.assertEqual(ctx.kv.overflow, 0)
                for p in pics:
                    h = hashlib.sha256(p.image.blob).hexdigest()
                    self.assertIn(h, KV_HASHES, "only approved key visuals (no logos, no purchased pixels)")
                    self.assertIn(h, CORP_KV, "corporate decks must use weapon-free key visuals")
                    self.assertNotIn("logo", p.name.lower())

    def test_every_item_text_present(self):
        for v, n, long in _cases():
            s, _ = _render(v, n, long)
            alltext = "\n".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame)
            for it in _items(v, n, long):
                t = it["title"] if isinstance(it, dict) else it
                with self.subTest(variant=v.name, n=n, long=long, item=t):
                    self.assertIn(t, alltext)


class Selection(unittest.TestCase):
    def test_new_variants_reachable_by_selector(self):
        seen = set()
        for fam, n, seq in (("agenda", 3, False), ("agenda", 7, False), ("items", 3, False), ("items", 4, False),
                            ("items", 2, False), ("process", 4, True), ("process", 6, True), ("text", 2, False), ("text", 1, False)):
            used = []
            for _ in range(12):
                L.KVPicker("corporate")
                v = L.select(fam, SHORT[:n] if fam != "text" else LONG[:n], used, sequence=seq)
                if v is None: break
                used.append(v.name); seen.add(v.name)
        L._ACTIVE[0] = None
        self.assertTrue(set(NEW) <= seen, sorted(set(NEW) - seen))

    def test_quad_center_only_for_four(self):
        L.KVPicker("corporate")
        used = [v.name for v in L.VARIANTS if v.family == "items" and v.name != "items.quad-center"] * 3
        self.assertEqual(L.select("items", SHORT[:4], used).name, "items.quad-center")
        self.assertNotEqual(getattr(L.select("items", SHORT[:3], used), "name", None), "items.quad-center")
        L._ACTIVE[0] = None


if __name__ == "__main__":
    unittest.main(verbosity=1)
