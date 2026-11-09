# AUTORUN HIGH B — Content triggers for aviation families

HIGH_B=IN-PROGRESS
Updated: 2026-11-09 (UTC)

| Item | Status | Notes |
|---|---|---|
| B0 前置 | DONE | 分支快轉到 main 970606f（已含 PR #23 layouts_aviation.py）；fonts-noto-cjk（apt）、B612 Mono（jsDelivr google/fonts）；fontconfig 別名 Noto Sans TC/JP/SC → Noto Sans CJK TC/JP/SC。渲染輸出只放 /tmp/bxr-b/ |
| B1 planner 觸發規則 + generator 保護式匯入／退回 | TODO | |
| B2 fixture + tests/test_aviation_planner.py + PR | TODO | |
| B3 整合驗收 | TODO | main 已含 layouts_aviation.py（PR #23），B3 不需等待 A |

## 已做決定（保守、符合 CIS v3.2）
1. **Fixture 位置**：`tests/test_pipeline.py` 會抓取 `tests/fixtures/briefs/*.json` 並寫死 `assertEqual(len(RESULTS), 6)`；`BRIEFS[0]` 也會因排序改變。該檔不在允許修改範圍，因此新 fixture 放在子目錄 `tests/fixtures/briefs/aviation/aviation-families-*.json`（檔名格式不變），由 `tests/test_aviation_planner.py` 自行驗證 brief/plan schema 並跑完整 pipeline（--no-render）的 QA gate。
2. **CI 覆蓋**：`presentation-preflight.yml` 不執行 test_aviation_layouts.py／test_aviation_planner.py；workflow 不在允許修改範圍，本地執行結果記錄於此，建議日後加入 CI。
3. **07_Templates/*.pptx 顯示已修改**：Git LFS 老問題，不提交、不修改、不還原。

## 節奏
Token 用量有限（使用者告知已用 86%）；本工作分段慢慢做，下一段排定在 2026-11-09 23:50（台北時間）之後。
