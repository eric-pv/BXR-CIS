#!/usr/bin/env python3
"""Phase 2 visual-acceptance deck: builds the real master, then one slide per master layout plus
representative content compositions, renders PNG previews and a contact sheet.
Content is taken from tests/fixtures/briefs/police-xr-overview.json (no invented facts); the chart
uses the CIS v3.2 'Readability by Medium' minimum body sizes (P.61) — real, citable numbers.
Usage: python scripts/build-master-review.py [--out review/phase2]"""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pptx import Presentation
from bxr_deck import brand as B, compose as C
from bxr_deck.master import build
from bxr_deck.render import render

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(B.SKILL / "review" / "phase2")); a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    build(B.MASTER_PPTX, potx=True)
    brief = json.loads((B.SKILL / "tests/fixtures/briefs/police-xr-overview.json").read_text(encoding="utf-8"))
    acc = B.sector_accent(brief["sector"])
    prs = Presentation(str(B.MASTER_PPTX)); L = {l.name: l for l in prs.slide_layouts}
    P = C.placeholder
    s = prs.slides.add_slide(L["BXR Cover"]); s.shapes.title.text = brief["topic"]
    P(s, 1).text = brief["purpose"]; P(s, 10).text = "2026.11 · GOVERNMENT BRIEFING · BIG X REALITY"
    s = prs.slides.add_slide(L["BXR Section"]); P(s, 10).text = "02"; s.shapes.title.text = "訓練流程"; P(s, 11).text = "TRAINING WORKFLOW"
    c0, c1, c2 = brief["content"]
    s = prs.slides.add_slide(L["BXR Title + Body"]); P(s, 10).text = "01 · 方案概要"; s.shapes.title.text = c0["title"]
    C.bullets(s, c0["facts"])
    s = prs.slides.add_slide(L["BXR Title Only"]); P(s, 10).text = "02 · 訓練流程"; s.shapes.title.text = c1["title"]
    C.process(s, [{"title": f} for f in c1["facts"]], accent=acc["deep"])
    s = prs.slides.add_slide(L["BXR Title Only"]); P(s, 10).text = "03 · 導入評估"; s.shapes.title.text = c2["title"]
    C.cards(s, [{"title": "設備條件", "body": c2["facts"][0], "icon": "XR"},
                {"title": "情境內容", "body": "以提供的產品資料為準", "icon": "Simulation"},
                {"title": "成效呈現", "body": "不編造績效數字；以實際演練紀錄呈現", "icon": "Analytics"}],
            top=C.BODY_TOP + 0.05, height=3.1, accent=acc["deep"])
    C.pending_box(s, C.M, 4.85, C.BODY_W, 1.6, "PENDING INPUT · 待補資料", ["客戶場地與設備清單", "經確認的產品規格資料"])
    s = prs.slides.add_slide(L["BXR Title Only"]); P(s, 10).text = "03 · 評估項目"; s.shapes.title.text = "導入評估表（待填）"
    C.table(s, ["評估項目", "目前狀態", "資料來源", "負責單位"],
            [["設備條件", "待補", "待補", "待補"], ["場地條件", "待補", "待補", "待補"], ["情境需求", "待補", "待補", "待補"]],
            col_widths=[3.4, 2.9, 2.9, C.BODY_W - 9.2], pending_marker="待補")
    s = prs.slides.add_slide(L["BXR Chart + Text"]); P(s, 10).text = "CIS v3.2 · P.61"; s.shapes.title.text = "不同觀看情境的內文最小字級"
    C.bar_chart(s, ["會議室投影", "桌面螢幕／PDF", "手機閱讀", "印刷（A4 講義）"], [20, 16, 28, 11], "內文最小字級 (pt)", unit="pt", highlight=0)
    C.set_text(P(s, 2), ["投影會洗淡顏色：內頁用白底，不用 Light 300。", "資料來源：BXR CIS v3.2 Readability by Medium。"], size=16)
    s = prs.slides.add_slide(L["BXR Closing"]); s.shapes.title.text = "Turn Every Drill into Real"
    P(s, 10).text = "全球動力科技股份有限公司 · bigxreality.com"; P(s, 11).text = "BIG X REALITY"
    dst = out / "BXR_Master_Review_v0.1.pptx"; prs.save(dst)
    print(dst); print(render(dst, out / "preview"))

if __name__ == "__main__": main()
