# BXR Presentation Skill — 專案收尾總覽

Updated: 2026-11-09 (UTC) · main `bcb2f76` 之後

## 結論
V0.1 工程範圍全部完成並已合併：員工輸入 brief（主題、目的、內容、語言 `zh-TW`／`en`／`JP`），系統規劃頁面、依內容選擇符合 CIS v3.2 的版型，產出可在 PowerPoint 中直接編輯文字、表格、圖表與物件的 PPTX，並附帶 plan 與 QA 報告。剩下的是**使用者視覺驗收**與幾項需要使用者決定的事項（見最後一節）。

## 各階段與工作
| 工作 | 內容 | 狀態 | PR | 進度檔 |
|---|---|---|---|---|
| Phase 0–4（V0.1 主線） | 前置驗證、素材索引、BXR 母片（Logo／字型／主題色由母片管理）、生成器、驗收流程 | DONE | #18、#19、#20 | PHASE4_ACCEPTANCE.md |
| LOW | 文件與測試補強 | DONE | — | AUTORUN_LOW.md |
| MEDIUM | 來源目錄、版型登記表、版型修正、6 份審閱樣張 | DONE | #21、#22 | AUTORUN_MEDIUM.md |
| HIGH A | 航空素材萃取的 7 個版型家族、19 個 variant（compare／timeline／map／team／product／gauge／quote） | DONE | #23 | AUTORUN_HIGH_A.md |
| PMLD | 500 頁參考庫第二輪萃取 14 個 variant | DONE | #24、#25 | AUTORUN_PMLD.md |
| HIGH B | 內容觸發規則、未登記時退回既有家族、整合驗收 | DONE | #26、#27 | AUTORUN_HIGH_B.md |
| CI 補強 | 航空兩個測試加入 CI | 本 PR | — | — |

## 系統組成（presentation-skill/）
- `bxr_deck/planner.py`：brief → deck plan；不虛構數字，缺資料時列為「待補」。航空家族由 `aviation_family()` 依事實結構觸發。
- `bxr_deck/generator.py`：plan → PPTX（BXR 母片）＋ QA 報告（G1–G9 與來源檔不變性）。
- `bxr_deck/layouts.py`、`layouts_aviation.py`：版型家族與 variant（含參考來源頁碼）。
- `contracts/`：brief 與 deck plan 的 JSON Schema。
- `catalog/`：來源素材目錄與版型登記表。
- `tests/`：契約、母片、pipeline、驗收、目錄、PMLD、航空版型、航空觸發，共 8 組測試；CI（`.github/workflows/presentation-preflight.yml`）全部執行。

## 使用方式
```bash
python -m bxr_deck build --brief presentation-skill/tests/fixtures/briefs/police-xr-overview.json --output out/
```
（在 `presentation-skill/` 目錄下執行；加 `--no-render` 可跳過 LibreOffice 預覽圖。）

## 需要 Eric 決定或處理
1. **視覺驗收**：所有 QA 報告的 `visual_approval` 都是 `pending-eric`；尚未在 Windows 版 PowerPoint 實機開啟確認。審閱樣張在 `presentation-skill/review/`。
2. **航空家族事實不足**：timeline／gauge／team／map 在 Repo 內找不到可查證事實，沒有 fixture；若提供公司沿革、據點、團隊職能或有上限的指標，可補 fixture。
3. **遠端舊分支**：GitHub 上仍有 21 個已完成的 `claude/*`、`dev/*` 分支；工作環境的代理不允許刪除分支，需手動清理。
4. **授權與公開存取**：Repo 為 PUBLIC 且含第三方商業簡報素材（500 頁參考庫、Aviation Slides）。公開散布與多人使用的授權、存取控制需要確認；本專案未變更 Repo 權限。
5. **`tests/test_pipeline.py` 寫死 6 份 fixture**：新 fixture 因此放在 `tests/fixtures/briefs/aviation/`；日後可改為依實際數量檢查。
