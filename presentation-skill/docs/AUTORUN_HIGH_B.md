# AUTORUN HIGH B — Content triggers for aviation families

HIGH_B=IN-PROGRESS
Updated: 2026-11-09 (UTC)

| Item | Status | Notes |
|---|---|---|
| B0 前置 | DONE | 分支快轉到 main 970606f（已含 PR #23 layouts_aviation.py）；fonts-noto-cjk（apt）、B612 Mono（jsDelivr google/fonts）；fontconfig 別名 Noto Sans TC/JP/SC → Noto Sans CJK TC/JP/SC。渲染輸出只放 /tmp/bxr-b/ |
| B1 planner 觸發規則 + generator 保護式匯入／退回 | DONE | 已合併 main 82b4968（#24/#25 只改 layouts.py，select 介面不變）。`planner.aviation_family()` 七條規則，既有 6 份 fixture 均不觸發；generator `build_aviation()` 先選新家族 variant，`select` 回傳 None 時依 AV_FALLBACK 退回。冒煙測試三種狀態（已登記／移除新家族／無任何 variant）QA 皆 PASS；既有 7 個測試檔全過 |
| B2 fixture + tests/test_aviation_planner.py + PR | TODO | |
| B3 整合驗收 | TODO | main 已含 layouts_aviation.py（PR #23），B3 不需等待 A |

## 已做決定（保守、符合 CIS v3.2）
1. **Fixture 位置**：`tests/test_pipeline.py` 會抓取 `tests/fixtures/briefs/*.json` 並寫死 `assertEqual(len(RESULTS), 6)`；`BRIEFS[0]` 也會因排序改變。該檔不在允許修改範圍，因此新 fixture 放在子目錄 `tests/fixtures/briefs/aviation/aviation-families-*.json`（檔名格式不變），由 `tests/test_aviation_planner.py` 自行驗證 brief/plan schema 並跑完整 pipeline（--no-render）的 QA gate。
2. **CI 覆蓋**：`presentation-preflight.yml` 不執行 test_aviation_layouts.py／test_aviation_planner.py；workflow 不在允許修改範圍，本地執行結果記錄於此，建議日後加入 CI。
3. **07_Templates/*.pptx 顯示已修改**：Git LFS 老問題，不提交、不修改、不還原。

## 觸發規則（planner.aviation_family，依序判斷；每條都要求「全部」可呈現事實符合，且該組沒有待補事實）
1. gauge：n=1–4，每項 `標籤：值 / 上限 單位`（也接受「上限」「max」「満点」）；必須有單位且 0<值≤上限 → items={label,value,max,unit}
2. timeline：n=3–8，每項以年份開頭（19xx/20xx、`民國NNN年`、`1NN年`）→ {year,title,body}
3. compare：標題含 vs／versus／對比／比較／相較／対比，且能從標題切出 ≥2 欄（例：`VR vs 實機`）；每項 `列名：值1｜值2`，值數＝欄數 → extra.columns
4. quote：n=1–2，每項以引號包住（「」『』“”""，可接 `——出處`），或標題含 宣言／使命／願景／理念／mission／vision／ミッション／ビジョン → extra.attribution
5. product：標題為 `<名稱>（的）產品特點／特色／功能特點／主要功能／features／特長／特徴`，n=2–6 → extra.name
6. team：n=2–6，每項標籤 ≤16 字且含職稱詞（經理、工程師、教官、負責人、manager、engineer、担当…）→ name 一律 None（不推測人名）
7. map：n≤6，每項標籤是國家／縣市／區域詞（可帶 地區／市場／據點 等後綴）

退回對應（generator.AV_FALLBACK）：compare→原生表格；timeline→process 家族（無則 compose.process）；map／team／product→items 家族（無則 cards／bullets）；gauge→data 家族（kpi 版型，否則原生長條圖）；quote→text 家族（無則 statement）。
generator 另將 `Gauge N min|max` 加入 G7 豁免名單：gauge.dials 會畫刻度起點 0（刻度標籤，非數據主張；上限值本身來自 brief）。

## 節奏
Token 用量有限（使用者告知已用 86%）；本工作分段慢慢做，下一段排定在 2026-11-09 23:50（台北時間）之後。
