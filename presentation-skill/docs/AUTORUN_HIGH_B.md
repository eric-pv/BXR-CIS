# AUTORUN HIGH B — Content triggers for aviation families

HIGH_B=DONE
Updated: 2026-11-09 (UTC)

| Item | Status | Notes |
|---|---|---|
| B0 前置 | DONE | 分支快轉到 main 970606f（已含 PR #23 layouts_aviation.py）；fonts-noto-cjk（apt）、B612 Mono（jsDelivr google/fonts）；fontconfig 別名 Noto Sans TC/JP/SC → Noto Sans CJK TC/JP/SC。渲染輸出只放 /tmp/bxr-b/ |
| B1 planner 觸發規則 + generator 保護式匯入／退回 | DONE | 已合併 main 82b4968（#24/#25 只改 layouts.py，select 介面不變）。`planner.aviation_family()` 七條規則，既有 6 份 fixture 均不觸發；generator `build_aviation()` 先選新家族 variant，`select` 回傳 None 時依 AV_FALLBACK 退回。冒煙測試三種狀態（已登記／移除新家族／無任何 variant）QA 皆 PASS；既有 7 個測試檔全過 |
| B2 fixture + tests/test_aviation_planner.py + PR | DONE | 13 項 OK；PR https://github.com/eric-pv/BXR-CIS/pull/26 CI verify-assets 全綠後 squash merge（e3ab5fe） |
| B3 整合驗收 | DONE | 從 main e3ab5fe 重新開始。7 份 fixture（6 既有＋1 新）全部重新產出並渲染（/tmp/bxr-b/b3），QA 皆 PASS；逐份只看總覽圖：新 fixture 選到 compare.center-axis／product.visual-left／quote.panel，無溢出、重疊。唯一修正：新 fixture 封面副標題換行後第二行只剩一字（孤字），縮短 purpose 後為單行（只改 B 的 fixture，未動 layouts_aviation.py）。既有 6 份無溢出、重疊；待補頁的留白屬既有設計。PR：見下方 |

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

## Fixture 事實來源（tests/fixtures/briefs/aviation/aviation-families-cis-v32.json）
| 家族 | 內容 | 來源 |
|---|---|---|
| compare | 五個領域色 v3.1｜v3.2 色碼 | 00_Brand_Guidelines/v3.2/BXR_CIS_Changes_v3.1_to_v3.2.csv 第 01–05 列 |
| product | BXR Presentation Template v3.2：15 layouts、18 sample slides、搭配 89 頁手冊 | 00_Brand_Guidelines/v3.2/README_v3.2.txt（WHAT CHANGED／Use with） |
| quote | 領域色聲明原文 | 00_Brand_Guidelines/v3.2/README_v3.2.txt（COLOR LAYERS） |

**沒有放入 fixture 的家族（找不到 Repo 事實支撐）**
- timeline：Repo 內版本紀錄只有 v3.1、v3.2，兩者都標 2026.10，湊不出 ≥3 個有年份的事件。
- gauge：找不到「帶單位且有上限」的數值（ΔE、對比值只有門檻或單一值，沒有上限）。
- team：文件只描述 Claude／使用者權責，沒有可列成團隊的職稱清單。
- map：文件沒有國家／縣市／區域的據點或市場事實。
四個家族的觸發與退回仍由 test_aviation_planner.py 以單元測試覆蓋。

## PR
- B1/B2：https://github.com/eric-pv/BXR-CIS/pull/26（squash merged）
- B3：https://github.com/eric-pv/BXR-CIS/pull/27（squash merged）

## 測試結果（B3，本機）
test_contracts failures=0 · preflight PASS · test_master OK · test_pipeline OK（1 skip）· test_acceptance OK · test_catalog OK（1 skip）· test_aviation_layouts OK · test_pmld_layouts OK · test_aviation_planner OK（13）

## 阻擋問題
1. **無法刪除遠端分支**：`git push origin --delete claude/ecstatic-carson-x79iqg` 被代理回 HTTP 403（重試一次相同）。PR #26 合併後分支仍留在遠端；B3 依「從最新 main 建立分支」重置同名分支並以 force-with-lease 推送。請 Eric 在 GitHub 上手動刪除合併後的分支。
2. **CI 未執行新測試**：presentation-preflight.yml 不跑 test_aviation_planner.py／test_aviation_layouts.py（workflow 不在允許修改範圍）；以上結果為本機執行。
3. **Fixture 位置偏離指定路徑**：見「已做決定 1」（tests/test_pipeline.py 寫死 6 份 fixture）。
4. **事實不足的家族**：timeline／gauge／team／map 沒有 Repo 事實可做 fixture（見上表）。

## 節奏
Token 用量有限（使用者告知已用 86%）；本工作分段慢慢做，下一段排定在 2026-11-09 23:50（台北時間）之後。
