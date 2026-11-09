#!/usr/bin/env python3
"""Tests for the source catalog (M1), layout registry + selector (M2) and icon catalog.

Runs without Git LFS: synthetic PPTX files are built with python-pptx; checks against the real purchased
libraries are skipped when they are LFS pointers.
    python presentation-skill/tests/test_catalog.py
"""
import csv, importlib.util, io, json, re, sys, tempfile, unittest, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent
sys.path.insert(0, str(HERE))


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / "scripts" / file)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


SC = load("build_source_catalog", "build-source-catalog.py")
SL = load("select_layout", "select-layout.py")
GEN = HERE / "catalog" / "generated"


def synthetic_pptx(text=None, chart=False, table=False, pictures=0):
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.util import Inches
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    if text:
        s.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1)).text_frame.text = text
    if chart:
        cd = CategoryChartData(); cd.categories = ["a", "b"]; cd.add_series("s", (1, 2))
        s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(2), Inches(4), Inches(3), cd)
    if table:
        s.shapes.add_table(2, 2, Inches(6), Inches(2), Inches(4), Inches(2))
    b = io.BytesIO(); prs.save(b); return b.getvalue()


class SourceCatalogScanner(unittest.TestCase):
    def test_category_ignores_file_name(self):
        rows, _, err = SC.scan_deck(synthetic_pptx(), "t", "T", "timeline agenda process 目錄.pptx", "T", 8_000_000)
        self.assertIsNone(err)
        self.assertEqual(rows[0]["category_auto"], "background")
        self.assertNotIn("timeline", rows[0]["category_basis"])

    def test_category_uses_slide_text(self):
        rows, _, _ = SC.scan_deck(synthetic_pptx("Project Timeline"), "t", "T", "plain.pptx", "T", 8_000_000)
        self.assertEqual(rows[0]["category_auto"], "timeline")

    def test_chart_table_counts_and_ids(self):
        rows, digest, _ = SC.scan_deck(synthetic_pptx("x", chart=True, table=True), "t", "AVI-007", "deck.pptx", "AVI-007", 8_000_000)
        r = rows[0]
        self.assertEqual(r["slide_id"], "AVI-007-0001")
        self.assertEqual((r["charts"], r["tables"]), (1, 1))
        self.assertEqual(r["category_auto"], "data")
        self.assertEqual(r["aspect"], "16:9")
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertRegex(r["slide_xml_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(r["status"], "source-candidate")

    def test_oversize_xml_is_recorded_unparsed(self):
        rows, _, _ = SC.scan_deck(synthetic_pptx("hello"), "t", "T", "d.pptx", "T", 100)
        self.assertEqual(rows[0]["parse_status"], "unparsed")
        self.assertIn("exceeds", rows[0]["unparsed_reason"])

    def test_bad_deck_reported_not_crashing(self):
        rows, _, err = SC.scan_deck(b"not a zip", "t", "T", "bad.pptx", "T", 8_000_000)
        self.assertEqual(rows, []); self.assertIn("BadZipFile", err)

    def test_build_end_to_end_with_aviation_zip(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); big = d / "big.pptx"; big.write_bytes(synthetic_pptx("目錄"))
            av = d / "av.zip"
            with zipfile.ZipFile(av, "w") as z:
                z.writestr("B/two.pptx", synthetic_pptx("Thank you"))
                z.writestr("A/one.pptx", synthetic_pptx(chart=True))
                z.writestr("__MACOSX/A/._one.pptx", b"junk")
            s = SC.build(str(big), str(av), d / "out")
            self.assertEqual(s["slides_total"], 3)
            rows = list(csv.DictReader((d / "out" / "source-slides.csv").open(encoding="utf-8")))
            self.assertEqual([r["slide_id"] for r in rows], ["PMLD-0001", "AVI-001-0001", "AVI-002-0001"])
            self.assertEqual(rows[1]["category_auto"], "data")       # A/one.pptx sorted first
            self.assertEqual(rows[2]["category_auto"], "closing")


class GeneratedCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(csv.DictReader((GEN / "source-slides.csv").open(encoding="utf-8")))
        cls.summary = json.loads((GEN / "summary.json").read_text(encoding="utf-8"))

    def test_counts_and_ids(self):
        self.assertEqual(len(self.rows), self.summary["slides_total"])
        self.assertEqual(self.summary["by_library"], {"500pages": 604, "aviation": 5184})
        ids = [r["slide_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        for i in ids:
            self.assertRegex(i, r"^(PMLD-\d{4}|AVI-\d{3}-\d{4})$")

    def test_unparsed_have_reasons(self):
        bad = [r for r in self.rows if r["parse_status"] != "parsed"]
        self.assertEqual(len(bad), len(self.summary["unparsed"]))
        self.assertTrue(all(r["unparsed_reason"] for r in bad))

    def test_no_text_or_thumbnails_committed(self):
        self.assertFalse(any(k in self.rows[0] for k in ("sample_text", "text", "thumbnail", "preview")))
        self.assertFalse([p for p in GEN.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif")])
        self.assertTrue(all(r["status"] == "source-candidate" for r in self.rows))

    def test_sources_match_lfs_files_when_present(self):
        src = HERE / "source-library"
        for name, digest in self.summary["sources"].items():
            p = src / name
            if not p.exists() or p.stat().st_size < 1_000_000:
                self.skipTest("source libraries are LFS pointers")
            import hashlib
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), digest)


class Registry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = SL.load_registry()

    def test_records_match_layout_schema(self):
        import jsonschema
        schema = json.loads((HERE / "catalog" / "layouts.schema.json").read_text(encoding="utf-8"))
        for r in self.reg["layouts"]:
            jsonschema.validate(r, schema)

    def test_states_and_approval_flag(self):
        self.assertEqual(self.reg["states"], ["source-candidate", "claude-reviewed", "cis-approved"])
        for r in self.reg["layouts"]:
            self.assertIn(r["status"], self.reg["states"])
            self.assertEqual(r["approved"], r["status"] == "cis-approved", r["id"])

    def test_registry_in_sync_with_variants(self):
        scanned = {v["variant"] for v in SL.scan_variants()}
        registered = {r["id"] for r in self.reg["layouts"]}
        self.assertEqual(scanned, registered, "run: python presentation-skill/scripts/select-layout.py --write-registry")
        from bxr_deck import layouts
        for v in layouts.VARIANTS:
            self.assertIn(v.name, registered)

    def test_reference_pages_exist_in_catalog(self):
        ids = {r["slide_id"] for r in csv.DictReader((GEN / "source-slides.csv").open(encoding="utf-8"))}
        for r in self.reg["layouts"]:
            for sid in r["ref_slides"]:
                self.assertIn(sid, ids, r["id"])
            if r["origin"] == "reference-distilled":
                self.assertTrue(r["ref_slides"], r["id"])

    def test_transitions(self):
        reg = json.loads(json.dumps(self.reg))
        rid = reg["layouts"][0]["id"]
        reg["layouts"][0]["status"] = "source-candidate"; reg["layouts"][0]["approved"] = False
        with self.assertRaises(ValueError):
            SL.promote(reg, rid, "cis-approved", "eric")         # cannot skip claude review
        SL.promote(reg, rid, "claude-reviewed", "claude")
        rec = SL.promote(reg, rid, "cis-approved", "eric")
        self.assertTrue(rec["approved"]); self.assertEqual(rec["approved_by"], "eric")

    def test_rebuild_keeps_human_approval(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "reg.json"
            reg = SL.build_registry(p)
            SL.promote(reg, reg["layouts"][0]["id"], "cis-approved", "eric")
            p.write_text(json.dumps(reg, ensure_ascii=False), encoding="utf-8")
            again = SL.build_registry(p)
            self.assertEqual(again["layouts"][0]["status"], "cis-approved")

    def test_suggest_never_picks_source_candidates(self):
        reg = json.loads(json.dumps(self.reg))
        for r in reg["layouts"]:
            r["status"] = "source-candidate"
        out = SL.suggest(reg, "items", 3)
        self.assertEqual(out["candidates"], []); self.assertTrue(out["fallback"])
        self.assertTrue(SL.suggest(reg, "items", 3, include_candidates=True)["candidates"])

    def test_suggest_filters_by_family_and_count(self):
        out = SL.suggest(self.reg, "process", 4)
        self.assertTrue(out["candidates"])
        for c in out["candidates"]:
            self.assertTrue(c["id"].startswith("process."))
            self.assertTrue(c["items"][0] <= 4 <= c["items"][1])
        self.assertEqual(SL.guess_family("導入流程三個步驟"), "process")
        self.assertEqual(SL.guess_count("導入流程三個步驟"), 3)
        self.assertEqual(SL.guess_count("5 steps"), 5)


class IconCatalog(unittest.TestCase):
    def test_official_svgs_catalogued_and_resolvable(self):
        rows = list(csv.DictReader((HERE / "catalog" / "icon-catalog.csv").open(encoding="utf-8-sig")))
        icons = REPO / "04_Graphics" / "Icons"
        svgs = sorted(p.name for p in icons.glob("BXR_Icon_*.svg"))
        self.assertEqual(len(svgs), 12)
        listed = {r["path"]: r for r in rows}
        for s in svgs:
            self.assertIn(s, listed)
            self.assertEqual(listed[s]["status"], "official_cis")
        for r in rows:
            self.assertTrue((icons / r["path"]).exists(), r["path"])
            self.assertTrue(r["tags"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
