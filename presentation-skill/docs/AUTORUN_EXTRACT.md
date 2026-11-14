# AUTORUN EXTRACT — 素材庫補萃取（500頁.pptx ／ Aviation Slides.zip）

EXTRACT=IN-PROGRESS
Updated: 2026-11-15 01:xx（台北）

## 範圍與計算方式
- 素材庫共 5,788 頁：500頁.pptx 604 頁；Aviation Slides 249 份簡報、5,184 頁（catalog/generated/source-slides.csv）。
- 開工前已有 50 個 variant，引用 116 頁（500頁 61 頁、Aviation 55 頁）。
- 逐頁萃取不實際（大量頁面是同一設計的配色／排列變化），因此以「**設計類型**」為單位：每批挑選素材庫中尚未有 BXR 對應的設計類型，各重建一個 variant，ref 記錄代表頁。
- Aviation 的資料夾名稱只是字母分組（如「Pyramid Slides」內是 N–P 開頭的簡報），設計類型以簡報檔名判斷。

## 批次紀錄
| 批次 | 狀態 | 新增 variant（ref） | PR |
|---|---|---|---|
| 1 | DONE（待 CI／合併） | items.pyramid（AVI-206）、process.funnel（AVI-094）、items.matrix（AVI-144）、process.cycle（AVI-079/080）、items.pillars（AVI-182）、items.concentric（AVI-208/065）、process.phases（AVI-001）、items.venn（AVI-239/240）、process.chevrons（AVI-003）、items.number-rings（AVI-166/170） | 見下 |

全部不需圖片；以 CIS v3.2 原生圖形重建，一頁一個紅色焦點；未取用購買檔的像素、文字或標誌。
新增測試 `tests/test_extract_layouts.py`（已加入 CI）：每個 variant 在所有支援項目數下文字齊全、無圖片、不超出內容區、可被選版器選到。
選版分數：3 個項目時讓既有版型優先（新 variant 分數 -0.5，仍可被選到）；4 個以上時金字塔／支柱加分。

## 尚未萃取的設計類型（依簡報檔名，下一批起處理）
- Aviation：Puzzle（AVI-204/205）、Product Roadmap（AVI-194）、Product Life Cycle（AVI-192/193）、Target Market（AVI-213/214）、Fishbone、Flow Chart、Harvey Ball、Hierarchy、KPI Dashboards（AVI-135/136，需數值）、Numbers 其他樣式（AVI-167/171）、Business Model Canvas、AIDA（AVI-005）、SWOT／PESTEL、Tables（Table Slides）、Agile、Org Chart 其他樣式、3D Infographics 等；地圖類（World/Africa/North America/Oceania）依 Eric 範圍決定只做世界與台灣，另行處理。
- 500頁.pptx：image-grid 類 345 頁多為圖片版型（需圖片，優先度低）；data 52 頁、infographic 49 頁、team 48 頁中尚未萃取的頁面待逐批比對。
- 剩餘量以設計類型估計約 25–30 種，預計還需 2–3 個時段。
