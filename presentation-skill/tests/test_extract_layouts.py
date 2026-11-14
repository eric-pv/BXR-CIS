#!/usr/bin/env python3
"""Aviation library extraction batches (docs/AUTORUN_EXTRACT.md): every new variant renders every item's text,
stays inside the slide, uses no pictures, and is reachable through layouts.select.
Run: python tests/test_extract_layouts.py"""
import sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from pptx import Presentation
from pptx.util import Emu
from bxr_deck import brand as B, generator as G, layouts as L
from bxr_deck.master import build as build_master
import tempfile, zipfile

BATCH1 = ["items.pyramid", "process.funnel", "items.matrix", "process.cycle", "items.pillars", "items.concentric",
          "process.phases", "items.venn", "process.chevrons", "items.number-rings"]
V = {v.name: v for v in L.VARIANTS}
FACTS = [("真實 Realism", "情境、裝備與壓力都要接近真實，訓練才有意義"), ("精準 Precision", "每一次演練都能量測、記錄與復盤"),
         ("備戰 Readiness", "系統可部署、可擴充，隨時投入單位的訓練節奏"), ("夥伴 Partnership", "與單位共同設計訓練"),
         ("任務導向", "一切以任務成果為目標"), ("可量測", "每次演練都留下紀錄")]
MASTER = B.MASTER_PPTX if zipfile.is_zipfile(B.MASTER_PPTX) else build_master(Path(tempfile.mkdtemp()) / "m.pptx")


def render(v, n):
    prs = Presentation(str(MASTER)); s = prs.slides.add_slide([l for l in prs.slide_layouts if l.name == "BXR Title Only"][0])
    ctx = G.Ctx({"topic": "t", "language": "zh-TW", "sector": "corporate"}, B.SIM_CYAN, B.GRAPHITE, L.KVPicker("corporate"))
    ctx.extra = {"caption": None}
    items = [f"{a} — {b}" for a, b in FACTS[:n]] if v.family == "process" else [{"title": a, "body": b, "icon": "Training"} for a, b in FACTS[:n]]
    v.render(s, items, ctx)
    return prs, s


class Batch1(unittest.TestCase):
    def test_registered_image_free(self):
        for name in BATCH1:
            with self.subTest(variant=name):
                self.assertIn(name, V); self.assertFalse(V[name].needs_image)
                self.assertTrue(all(isinstance(r, str) and r.startswith("AVI-") for r in V[name].ref))

    def test_text_present_and_inside_slide(self):
        for name in BATCH1:
            v = V[name]
            for n in range(v.nmin, v.nmax + 1):
                prs, s = render(v, n)
                with self.subTest(variant=name, n=n):
                    text = "\n".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame)
                    for a, b in FACTS[:n]:
                        self.assertIn(a, text); self.assertIn(b, text)
                    self.assertFalse([sh for sh in s.shapes if sh.shape_type == 13], "no pictures")
                    W, H = prs.slide_width, prs.slide_height
                    for sh in s.shapes:
                        if sh.rotation: continue
                        self.assertGreaterEqual(sh.left, 0, sh.name); self.assertGreaterEqual(sh.top, 0, sh.name)
                        self.assertLessEqual(sh.left + sh.width, W + Emu(10), sh.name)
                        self.assertLessEqual(sh.top + sh.height, Emu(int(6.92 * 914400)), sh.name)   # above the footer

    def test_reachable(self):
        seen = set()
        for fam, n, seq in (("items", 3, False), ("items", 4, False), ("items", 5, False), ("items", 2, False),
                            ("process", 3, True), ("process", 4, True), ("process", 5, True), ("process", 6, True), ("process", 2, True)):
            used = []
            for _ in range(30):
                L.KVPicker("corporate")
                v = L.select(fam, [a for a, _ in FACTS[:n]], used, sequence=seq)
                if v is None: break
                used.append(v.name); seen.add(v.name)
        L._ACTIVE[0] = None
        self.assertTrue(set(BATCH1) <= seen, sorted(set(BATCH1) - seen))


if __name__ == "__main__":
    unittest.main(verbosity=1)
