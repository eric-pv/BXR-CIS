#!/usr/bin/env python3
"""Master/Theme structure tests (gates G3/G4 at template level). Run: python tests/test_master.py"""
import hashlib, io, sys, tempfile, unittest, zipfile, importlib.util
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from lxml import etree
from pptx import Presentation
from bxr_deck import brand as B
from bxr_deck.master import build, LAYOUT_NAMES
spec = importlib.util.spec_from_file_location("v", ROOT / "scripts/validate-pptx.py"); V = importlib.util.module_from_spec(spec); spec.loader.exec_module(V)
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}

class MasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp()); cls.path = build(cls.tmp / "m.pptx", potx=True)
        cls.prs = Presentation(str(cls.path))

    def test_slide_size_16x9(self):
        self.assertEqual((self.prs.slide_width, self.prs.slide_height), (12192000, 6858000))

    def test_layout_names(self):
        self.assertEqual([l.name for l in self.prs.slide_layouts], LAYOUT_NAMES)

    def test_theme_fonts_and_colors(self):
        with zipfile.ZipFile(self.path) as z:
            t = etree.fromstring(z.read("ppt/theme/theme1.xml"))
        self.assertEqual({f.get("typeface") for f in t.iterfind(".//a:fontScheme/*/a:latin", NS)}, {B.FONT})
        self.assertEqual(t.find(".//a:clrScheme/a:accent2/a:srgbClr", NS).get("val"), B.RED)
        self.assertEqual(t.find(".//a:clrScheme/a:dk1/a:srgbClr", NS).get("val"), B.BLACK)

    def test_backgrounds_are_layout_backgrounds_from_approved_pngs(self):
        approved = {hashlib.sha256(p.read_bytes()).hexdigest() for p in B.BG.values()}
        for l in self.prs.slide_layouts:
            blip = l._element.find(".//p:cSld/p:bg//a:blip", NS)
            self.assertIsNotNone(blip, l.name)
            part = l.part.related_part(blip.get("{%s}embed" % NS["r"]))
            self.assertIn(hashlib.sha256(part.blob).hexdigest(), approved, l.name)

    def test_logo_on_every_layout_from_official_files(self):
        res = V.validate(self.path)
        self.assertEqual(res["errors"], [])
        for name in LAYOUT_NAMES:
            self.assertEqual(len(res["layout_logos"][name]), 1, name)

    def test_title_placeholders(self):
        for l in self.prs.slide_layouts:
            types = [p.placeholder_format.type for p in l.placeholders]
            self.assertTrue(any(str(t).startswith(("TITLE", "CENTER_TITLE")) for t in types), l.name)

    def test_logo_edit_propagates_and_slides_have_no_logo(self):
        """Change the logo once on the content layout; every slide of that layout must change."""
        prs = Presentation(str(self.path)); lay = prs.slide_layouts.get_by_name("BXR Title + Body")
        for i in range(3):
            s = prs.slides.add_slide(lay); s.shapes.title.text = f"T{i}"
        out = self.tmp / "deck.pptx"; prs.save(out)
        res = V.validate(out); self.assertEqual(res["errors"], [])
        self.assertTrue(all(d["pictures"] == 0 for d in res["details"]))
        # swap the layout logo image for the black variant, at the package level
        prs = Presentation(str(out)); lay = prs.slide_layouts.get_by_name("BXR Title + Body")
        pic = [s for s in lay.shapes if s.shape_type == 13][0]
        rid = pic._element.find(".//a:blip", NS).get("{%s}embed" % NS["r"])
        new_part, new_rid = lay.part.get_or_add_image_part(str(B.LOGO / "BXR_Logo_H_Black.png"))
        pic._element.find(".//a:blip", NS).set("{%s}embed" % NS["r"], new_rid)
        out2 = self.tmp / "deck2.pptx"; prs.save(out2)
        res2 = V.validate(out2)
        rows = [d for d in res2["details"] if d["layout"] == "BXR Title + Body"]
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(d["inherited_logos"] == ["BXR_Logo_H_Black.png"] for d in rows))

    def test_potx_content_type(self):
        with zipfile.ZipFile(self.path.with_suffix(".potx")) as z:
            self.assertIn(b"presentationml.template.main+xml", z.read("[Content_Types].xml"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
