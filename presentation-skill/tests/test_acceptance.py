#!/usr/bin/env python3
"""Phase 4 acceptance tests that can run without PowerPoint or LibreOffice.
Run: python tests/test_acceptance.py
Covers: revision flow (Phase 3 #7), natural-language outline -> brief -> deck (Phase 3 #1),
deterministic output for fixtures (Phase 3 #8), 10-15 slide deck size (V0.1 definition)."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from jsonschema import Draft202012Validator
from bxr_deck.generator import generate, load_brief
from bxr_deck.master import build as build_master
from bxr_deck.nl import brief_from_text

BRIEFS = ROOT / "tests/fixtures/briefs"
OUT = Path(tempfile.mkdtemp(prefix="bxr-accept-"))
MASTER = None
PLAN_SCHEMA = json.loads((ROOT / "contracts/deck-plan.schema.json").read_text(encoding="utf-8"))


def setUpModule():
    global MASTER
    MASTER = build_master(OUT / "master.pptx")      # templates/*.pptx may be LFS pointers in CI


def _brief(name):
    return json.loads((BRIEFS / f"{name}.json").read_text(encoding="utf-8"))


def _build(brief, tag, previous=None):
    return generate(brief, OUT / tag, previous_plan=previous, render=False, master=MASTER)


class RevisionFlow(unittest.TestCase):
    """Editing one content group must not change layout variants of other slides."""

    def check(self, name):
        brief = _brief(name)
        _, plan1, qa1 = _build(brief, f"{name}-v1")
        prev = OUT / f"{name}-v1" / f"{brief['id']}.plan.json"
        variants = {s["slide_id"]: s["layout_source"].get("variant") for s in plan1["slides"]}
        self.assertTrue(any(variants.values()), "plan must record content variants")
        for gi in range(len(brief["content"])):
            with self.subTest(fixture=name, edited_group=gi):
                b2 = copy.deepcopy(brief); b2["content"][gi]["facts"].append("Revision test item")
                _, plan2, qa2 = _build(b2, f"{name}-v2-{gi}", previous=prev)
                self.assertEqual(qa2["status"], "PASS")
                self.assertEqual(list(Draft202012Validator(PLAN_SCHEMA).iter_errors(plan2)), [])
                for s in plan2["slides"]:
                    sid = s["slide_id"]
                    if sid in variants and variants[sid] and f"c{gi}" not in sid:
                        self.assertEqual(s["layout_source"].get("variant"), variants[sid], sid)

    def test_cross_sector_english(self):
        self.check("cross-sector-english")

    def test_bxr_presentation_system(self):
        self.check("bxr-presentation-system")

    def test_unchanged_brief_keeps_everything(self):
        brief = _brief("police-xr-overview")
        _, p1, _ = _build(brief, "same-v1")
        _, p2, _ = _build(brief, "same-v2", previous=OUT / "same-v1" / f"{brief['id']}.plan.json")
        self.assertEqual([(s["slide_id"], s["layout_source"]) for s in p1["slides"]],
                         [(s["slide_id"], s["layout_source"]) for s in p2["slides"]])


class NaturalLanguage(unittest.TestCase):
    OUTLINES = {
        "zh-TW": "警用 XR 訓練導入說明\n目的：說明導入步驟與待確認事項\n12頁\n# 訓練流程\n- 需求訪談\n- 情境設計\n- 試行訓練\n- 成效檢討\n# 設備\n- 頭戴式顯示器\n- 追蹤系統\n",
        "en": "XR training rollout\nPurpose: explain rollout steps and open items\n10 slides\n# Rollout process\n- Needs interview\n- Scenario design\n- Pilot training\n- Review\n# Equipment\n- Headset\n- Tracking\n",
        "JP": "XR訓練の導入について\n目的：導入手順と確認事項の説明\n10枚\n# 導入プロセス\n- ヒアリング\n- シナリオ設計\n- 試行訓練\n- 振り返り\n",
    }

    def test_outline_to_valid_brief_and_deck(self):
        for lang, text in self.OUTLINES.items():
            with self.subTest(lang=lang):
                brief = brief_from_text(text, f"nl-{lang.lower()}")
                self.assertEqual(brief["language"], lang)
                load_brief(brief)                                   # schema-valid
                facts = [f for g in brief["content"] for f in g["facts"]]
                self.assertTrue(all(f in text for f in facts), "facts copied verbatim")
                _, plan, qa = _build(brief, f"nl-{lang}")
                self.assertEqual(qa["status"], "PASS", [k for k, g in qa["gates"].items() if not g["pass"]])


class Deterministic(unittest.TestCase):
    def test_same_brief_same_plan(self):
        brief = _brief("data-comparison")
        _, p1, _ = _build(brief, "det-1"); _, p2, _ = _build(brief, "det-2")
        self.assertEqual(json.dumps(p1, sort_keys=True), json.dumps(p2, sort_keys=True))


class DeckSize(unittest.TestCase):
    def test_at_least_one_10_to_15_slide_deck(self):
        sizes = {}
        for name in ("police-xr-overview", "bxr-presentation-system", "cross-sector-english"):
            _, _, qa = _build(_brief(name), f"size-{name}")
            sizes[name] = qa["slide_count"]
        self.assertTrue(any(10 <= n <= 15 for n in sizes.values()), sizes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
