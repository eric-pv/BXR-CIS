#!/usr/bin/env python3
"""End-to-end pipeline tests (brief -> plan -> PPTX -> QA) without rendering.
Run: python tests/test_pipeline.py   (needs python-pptx, lxml, jsonschema, pillow; no LibreOffice)"""
import contextlib, hashlib, io, json, re, sys, tempfile, unittest, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from lxml import etree
from pptx import Presentation
from bxr_deck import brand as B
from bxr_deck.__main__ import main as cli
from bxr_deck.generator import V, NUM_RE, GENERATED_NAMES, load_brief, BriefError

BRIEFS = sorted((ROOT / "tests/fixtures/briefs").glob("*.json"))
PLAN_SCHEMA = json.loads((ROOT / "contracts/deck-plan.schema.json").read_text(encoding="utf-8"))
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
OUT = Path(tempfile.mkdtemp(prefix="bxr-pipeline-"))


def _src_hashes():
    out = {}
    for p in sorted((ROOT / "source-library").glob("*")):
        if p.suffix.lower() in (".pptx", ".zip") and p.stat().st_size > 1_000_000:  # skip LFS pointers
            out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def setUpModule():
    global SRC_BEFORE, RESULTS
    SRC_BEFORE = _src_hashes(); RESULTS = {}
    for b in BRIEFS:
        out = OUT / b.stem
        with contextlib.redirect_stdout(io.StringIO()):
            rc = cli(["build", "--brief", str(b), "--output", str(out), "--no-render"])
        bid = json.loads(b.read_text(encoding="utf-8"))["id"]
        RESULTS[b.stem] = {"rc": rc, "brief": json.loads(b.read_text(encoding="utf-8")), "pptx": out / f"{bid}.pptx",
                           "plan": out / f"{bid}.plan.json", "qa": out / f"{bid}.qa.json"}


class PipelineTests(unittest.TestCase):
    def each(self):
        self.assertEqual(len(RESULTS), 6)
        for name, r in RESULTS.items():
            with self.subTest(fixture=name):
                yield name, r

    def test_build_plan_schema_and_qa_pass(self):
        for name, r in self.each():
            self.assertEqual(r["rc"], 0)
            self.assertTrue(r["pptx"].exists() and zipfile.is_zipfile(r["pptx"]))
            plan = json.loads(r["plan"].read_text(encoding="utf-8"))
            self.assertEqual([e.message for e in Draft202012Validator(PLAN_SCHEMA).iter_errors(plan)], [])
            qa = json.loads(r["qa"].read_text(encoding="utf-8"))
            self.assertEqual(qa["status"], "PASS", [k for k, g in qa["gates"].items() if not g["pass"]])

    def test_invalid_briefs_rejected(self):
        base = json.loads(BRIEFS[0].read_text(encoding="utf-8"))
        for field, value in (("slides", 0), ("language", "ja")):
            with self.subTest(**{field: value}):
                bad = dict(base, **{field: value})
                with self.assertRaises(BriefError):
                    load_brief(bad)
                p = OUT / f"bad-{field}.json"; p.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(cli(["build", "--brief", str(p), "--output", str(OUT / "bad"), "--no-render"]), 2)

    def test_no_logo_on_slides_and_all_inherit(self):
        for name, r in self.each():
            res = V.validate(r["pptx"])
            self.assertEqual(res["errors"], [])
            self.assertFalse(any("logo" in e.lower() for e in res["errors"]))
            logo_hashes = {hashlib.sha256(p.read_bytes()).hexdigest() for p in B.LOGO.glob("*.png")}
            prs = Presentation(str(r["pptx"]))
            for i, s in enumerate(prs.slides, 1):
                for rel in s.part.rels.values():
                    if "image" in rel.reltype:
                        self.assertNotIn(hashlib.sha256(rel.target_part.blob).hexdigest(), logo_hashes, f"slide {i}")
            self.assertEqual(len(res["details"]), len(prs.slides))
            for d in res["details"]:
                self.assertTrue(d["inherited_logos"], d)

    def test_titles_tables_charts_native(self):
        for name, r in self.each():
            prs = Presentation(str(r["pptx"]))
            for i, s in enumerate(prs.slides, 1):
                t = s.shapes.title
                self.assertIsNotNone(t, f"slide {i}"); self.assertTrue(t.is_placeholder and t.text.strip())
                for sh in s.shapes:
                    if sh.has_table:
                        self.assertIsNotNone(sh._element.find(".//a:tbl", NS))
                    if sh.has_chart:
                        part = sh.chart.part
                        self.assertIsNotNone(part.chart_workbook.xlsx_part, f"slide {i}: chart without embedded data")
                        self.assertIsNotNone(etree.fromstring(part.blob).find(".//c:externalData", NS))

    def test_numbers_come_from_brief(self):
        for name, r in self.each():
            qa = json.loads(r["qa"].read_text(encoding="utf-8"))
            self.assertTrue(qa["gates"]["G7_evidence"]["pass"], qa["gates"]["G7_evidence"]["detail"])
            # independent check on table/chart data: every number must appear in the brief
            allowed = set(NUM_RE.findall(json.dumps(r["brief"], ensure_ascii=False)))
            prs = Presentation(str(r["pptx"]))
            for s in prs.slides:
                for sh in s.shapes:
                    if sh.has_chart:
                        for pl in sh.chart.plots:
                            for ser in pl.series:
                                for v in ser.values:
                                    self.assertTrue({f"{v:g}", str(v)} & allowed, f"{name}: chart value {v}")
                    if sh.has_table and not GENERATED_NAMES.search(sh.name or ""):
                        for row in sh.table.rows:
                            for c in row.cells:
                                for n in NUM_RE.findall(c.text):
                                    self.assertIn(n, allowed, f"{name}: table number {n}")

    def test_jp_theme_east_asian_font(self):
        jp = [r for r in RESULTS.values() if r["brief"]["language"] == "JP"]
        self.assertTrue(jp)
        for r in jp:
            with zipfile.ZipFile(r["pptx"]) as z:
                themes = [n for n in z.namelist() if re.match(r"ppt/theme/theme\d+\.xml$", n)]
                faces = set()
                for n in themes:
                    root = etree.fromstring(z.read(n))
                    faces |= {e.get("typeface") for e in root.iterfind(".//a:fontScheme/*/a:ea", NS)}
            self.assertIn(B.FONT_JP, faces)
            self.assertEqual(B.FONT_JP, "Noto Sans JP")

    def test_source_library_unchanged(self):
        if not SRC_BEFORE:
            self.skipTest("source-library files are Git LFS pointers (run `git lfs pull`)")
        self.assertEqual(_src_hashes(), SRC_BEFORE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
