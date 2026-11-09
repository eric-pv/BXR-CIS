#!/usr/bin/env python3
"""Content triggers for the aviation families (planner.aviation_family) and the generator fallback.
Run: python tests/test_aviation_planner.py   (needs python-pptx, lxml, jsonschema, pillow; no LibreOffice)"""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from bxr_deck import planner as P, generator as G, layouts as LY

BRIEFS = sorted((ROOT / "tests/fixtures/briefs").glob("*.json"))              # existing six (unchanged)
AV_BRIEFS = sorted((ROOT / "tests/fixtures/briefs/aviation").glob("aviation-families-*.json"))
BRIEF_SCHEMA = json.loads((ROOT / "contracts/presentation-brief.schema.json").read_text(encoding="utf-8"))
PLAN_SCHEMA = json.loads((ROOT / "contracts/deck-plan.schema.json").read_text(encoding="utf-8"))
AV_FAMILIES = set(G.AV_FALLBACK)
OUT = Path(tempfile.mkdtemp(prefix="bxr-av-planner-"))


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def without_aviation(fn):
    """Run fn with every aviation-family variant unregistered (what generate sees before work A merges)."""
    saved = list(LY.VARIANTS)
    LY.VARIANTS[:] = [v for v in saved if v.family not in AV_FAMILIES]
    try:
        return fn()
    finally:
        LY.VARIANTS[:] = saved


class TriggerRules(unittest.TestCase):
    A = staticmethod(P.aviation_family)

    def test_timeline(self):
        fam, items, extra = self.A("沿革", ["2019：成立", "2021：發表", "民國113年：導入"])
        self.assertEqual(fam, "timeline")
        self.assertEqual([i["year"] for i in items], ["2019", "2021", "民國113年"])
        self.assertEqual(set(items[0]), {"year", "title", "body"})
        self.assertIsNone(self.A("沿革", ["2019：成立", "發表新版"]))          # every fact needs a year; n>=3

    def test_compare(self):
        for title in ("VR vs 實機", "VR 與實機比較", "主題：VR 相較 實機", "VR versus Live"):
            with self.subTest(title=title):
                fam, items, extra = self.A(title, ["成本：低｜高", "場地：室內｜靶場"])
                self.assertEqual(fam, "compare"); self.assertEqual(len(extra["columns"]), 2)
                self.assertEqual(items[0], {"label": "成本", "values": ["低", "高"]})
        self.assertIsNone(self.A("方案比較", ["方案 A：條件", "方案 B：條件"]))   # no columns -> existing table

    def test_map(self):
        fam, items, _ = self.A("據點", ["台灣：總部", "日本：合作", "高雄市"])
        self.assertEqual(fam, "map"); self.assertEqual(items[2], {"name": "高雄市", "body": None})
        self.assertIsNone(self.A("據點", ["台灣：總部", "合作夥伴：多家"]))

    def test_team_never_invents_names(self):
        fam, items, _ = self.A("團隊", ["專案經理：統籌", "技術支援工程師：現場"])
        self.assertEqual(fam, "team"); self.assertTrue(all(i["name"] is None for i in items))
        self.assertEqual(items[0]["role"], "專案經理")

    def test_product(self):
        fam, items, extra = self.A("BXR 平台的產品特點", ["沉浸式：XR", "多人：同步"])
        self.assertEqual(fam, "product"); self.assertEqual(extra, {"name": "BXR 平台"})
        self.assertEqual(items[0], {"title": "沉浸式", "body": "XR"})

    def test_gauge_needs_unit_and_upper_bound(self):
        fam, items, extra = self.A("指標", ["完成率：80 / 100 %"])
        self.assertEqual(fam, "gauge"); self.assertEqual(extra, {"notes": []})
        self.assertEqual(items[0], {"label": "完成率", "value": 80.0, "max": 100.0, "unit": "%"})
        self.assertIsNone(self.A("指標", ["完成率：80 / 100"]))                 # no unit
        self.assertIsNone(self.A("指標", ["完成率：120 / 100 %"]))              # value above max
        self.assertNotEqual((self.A("指標", ["完成率：80 %", "時數：40 小時"]) or ("",))[0], "gauge")  # no bound

    def test_quote(self):
        fam, items, extra = self.A("x", ["「讓每次演練成真」——品牌標語"])
        self.assertEqual((fam, items, extra), ("quote", ["讓每次演練成真"], {"attribution": "品牌標語"}))
        fam, items, extra = self.A("願景", ["Turn Every Drill into Real"])
        self.assertEqual((fam, extra["attribution"]), ("quote", None))
        self.assertIsNone(self.A("概要", ["一般敘述", "另一段敘述", "第三段"]))

    def test_contract_shapes(self):
        cases = {"timeline": ("沿革", ["2019：a", "2020：b", "2021：c"]), "compare": ("A vs B", ["x：1｜2", "y：3｜4"]),
                 "map": ("x", ["日本"]), "team": ("x", ["教官：a", "負責人：b"]), "product": ("P 特色", ["a：b", "c：d"]),
                 "gauge": ("x", ["率：1 / 2 %"]), "quote": ("x", ["「q」"])}
        for fam, (title, facts) in cases.items():
            with self.subTest(family=fam):
                got, items, extra = self.A(title, facts)
                self.assertEqual(got, fam); self.assertIsInstance(items, list); self.assertIsInstance(extra, dict)
                self.assertIn(fam, P.AV_ROLE)


class ExistingFixturesUnchanged(unittest.TestCase):
    def test_no_trigger_and_identical_plans(self):
        self.assertEqual(len(BRIEFS), 6)
        orig = P.aviation_family
        for b in BRIEFS:
            with self.subTest(brief=b.stem):
                brief = load(b)
                new = P.plan(brief)[0]
                P.aviation_family = lambda *a: None
                try:
                    old = P.plan(brief)[0]
                finally:
                    P.aviation_family = orig
                self.assertFalse([s.slide_id for s in new if s.kind == "aviation"])
                self.assertEqual([(s.slide_id, s.kind, s.layout, s.data) for s in new],
                                 [(s.slide_id, s.kind, s.layout, s.data) for s in old])


class NewFixtures(unittest.TestCase):
    def test_fixtures_exist_and_validate(self):
        self.assertTrue(AV_BRIEFS)
        for b in AV_BRIEFS:
            with self.subTest(brief=b.name):
                brief = load(b)
                self.assertEqual(list(Draft202012Validator(BRIEF_SCHEMA).iter_errors(brief)), [])
                self.assertEqual(brief["source_policy"], "provided-only")
                for g in brief["content"]:      # every fact group cites a repo path that exists
                    self.assertTrue(g.get("source_refs"), g["title"])
                    for ref in g["source_refs"]:
                        self.assertTrue((ROOT.parent / ref.split("#")[0].split(" (")[0]).exists(), ref)

    def test_generate_registered(self):
        for b in AV_BRIEFS:
            with self.subTest(brief=b.name):
                pptx, plan, qa = G.generate(b, OUT / "reg" / b.stem, render=False)
                self.assertEqual(list(Draft202012Validator(PLAN_SCHEMA).iter_errors(plan)), [])
                self.assertEqual(qa["status"], "PASS", [k for k, g in qa["gates"].items() if not g["pass"]])
                av = {k: v for k, v in qa["content_variants"].items() if k.split("-c")[0] in AV_FAMILIES}
                self.assertTrue(av)
                for sid, name in av.items():
                    self.assertEqual(name.split(".")[0], sid.split("-c")[0])

    def test_generate_fallback_when_unregistered(self):
        for b in AV_BRIEFS:
            with self.subTest(brief=b.name):
                pptx, plan, qa = without_aviation(lambda: G.generate(b, OUT / "fb" / b.stem, render=False))
                self.assertEqual(qa["status"], "PASS", [k for k, g in qa["gates"].items() if not g["pass"]])
                self.assertFalse([v for v in qa["content_variants"].values() if v.split(".")[0] in AV_FAMILIES])
                from pptx import Presentation
                notes = [s.notes_slide.notes_text_frame.text for s in Presentation(str(pptx)).slides if s.has_notes_slide]
                self.assertTrue(any("Fallback: no registered" in n for n in notes))

    def test_generate_without_module(self):
        """Guarded import: generator works when bxr_deck.layouts_aviation cannot be imported at all."""
        code = ("import sys; sys.path.insert(0, %r); sys.modules['bxr_deck.layouts_aviation'] = None\n"
                "from bxr_deck import generator as G\n"
                "assert G.layouts_aviation is None\n"
                "_, _, qa = G.generate(%r, %r, render=False)\n"
                "assert qa['status'] == 'PASS', qa['gates']\n"
                "assert not any(v.split('.')[0] in G.AV_FALLBACK for v in qa['content_variants'].values())\n"
                ) % (str(ROOT), str(AV_BRIEFS[0]), str(OUT / "nomod"))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])


if __name__ == "__main__":
    unittest.main(verbosity=1)
