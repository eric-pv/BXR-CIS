# AUTORUN — 500頁（PMLD）版型補完

PMLD=IN-PROGRESS
最後更新：2026-11-09T12:00Z
分支：claude/affectionate-wright-80u02w（系統指定）
合併：本工作未獲自行合併授權 → PR 以 draft 交 Eric 合併。

## 範圍（避開平行工作）
- 平行工作 A：`bxr_deck/layouts_aviation.py`、`tests/test_aviation_layouts.py`（Aviation 新家族：compare/timeline/map/team/product/gauge/quote）。
- 平行工作 B：`bxr_deck/planner.py`、`bxr_deck/generator.py`、`tests/fixtures/briefs/aviation-families-*.json`、`tests/test_aviation_planner.py`。
- 本工作只改：`bxr_deck/layouts.py`（只新增 variant，不改既有版型）、`catalog/layout-registry.json`（以 `select-layout.py --write-registry` 重建）、新檔 `tests/test_pmld_layouts.py`、本進度檔。
- 只補 generator 已會派送的既有家族（agenda / items / process / text / data），不需要改 generator。500頁中的團隊／時間軸／比較頁與 A 的家族重疊，等 A 合併後再補。
- 不重產 `review/phase3`（避免與 B3 的二進位檔衝突）；渲染驗收輸出只放 /tmp。

| 項目 | 狀態 | 備註 |
|---|---|---|
| 前置（LFS 500頁、字型） | DONE | 500頁 sha256 b7dab6f4… 與 catalog 相符；Noto Sans CJK（apt）；B612 Mono（@fontsource/b612-mono 5.2.5 → ttf）；fontconfig 別名 Noto Sans TC/JP → Noto Sans CJK TC/JP |
| P1 渲染 604 頁 → 縮圖 → 編號總覽圖（/tmp/bxr-pmld） | DONE | LibreOffice 單檔一次轉完 604/604 頁（約 5 分鐘，峰值記憶體約 6 GB，0 失敗）；pdftoppm 640 px 縮圖 3.5 分鐘；21 張編號總覽圖（每張 30 頁，標註 PMLD 編號與 category_auto）；全部只在 /tmp，未提交 |
| P2 新 variant（layouts.py） | IN-PROGRESS | |
| P3 registry 重建 + tests/test_pmld_layouts.py | TODO | |
| P4 樣張與 fixture 渲染目視驗收、全部測試、draft PR | TODO | |

## 已知問題
- `07_Templates/BXR_Presentation_Template_v3.1.pptx`、`v3.2.pptx` 在工作樹顯示為已修改（以一般 blob 提交，但 `.gitattributes` 設 `*.pptx` 為 LFS）。不提交、不修改、不還原。
- 給 A／B 的提醒：`scripts/select-layout.py` 以 `f"PMLD-{p:04d}"` 處理 `ref`，只接受整數頁碼；工作 A 的 `ref` 是字串 `"AVI-<deck>-<page>"`，A 合併後 `--write-registry` 會失敗，`test_registry_in_sync_with_variants` 也會失敗。需在 A 或 B 的 PR 中讓 select-layout 接受字串 ref。

## 使用者決定：地圖參考範圍（2026-11-09，Eric）
公司不做中國業務，中國地圖不保留；台灣與世界地圖保留。供工作 A（地圖家族）採用：
- 可參考：世界地圖 PMLD-0458、0459、0460、0461、0462、0463；台灣輪廓 PMLD-0501、0518、0569、0603（只取輪廓形狀；0501「中國・台灣」、0569「台灣省」等來源標籤一律不採用）。
- 排除：其餘中國全國／省市地圖頁（PMLD-0464–0500、0502–0517、0519–0568、0570–0602、0604）。
- Aviation 地圖也比照：只用世界與台灣地圖。
