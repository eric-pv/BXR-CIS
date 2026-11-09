# Phase 4 驗收清單（V0.1）

依 `CLAUDE_CODE_EXECUTION_ORDER.md` §Phase 4。**自動**＝CI 每次 PR 都會跑；**Eric**＝需要人在 Windows PowerPoint 上確認。

| # | 項目 | 狀態 | 如何驗證 |
|---|------|------|----------|
| 1 | 資料契約：fixture 通過 schema、錯誤輸入被拒絕 | 自動 ✅ | `test_contracts.py`、`test_pipeline.py`（slides=0、language=ja 被拒） |
| 2 | 結構：ZIP／OOXML 有效、版面數正確 | 自動 ✅ | `test_pipeline.py`、`scripts/validate-pptx.py` |
| 2 | PowerPoint 開啟時**不要求修復** | **Eric** | 容器裡沒有 PowerPoint，見下方步驟 1 |
| 3 | 母片：Logo 只在版面配置、改一次全部更新；主題色與字型由 Theme 繼承 | 自動 ✅ | `test_master.py`（Logo 換檔後所有頁同步）、`test_pipeline.py` |
| 4 | 可編輯性：標題 placeholder、原生表格、圖表內嵌資料 | 自動 ✅ | `test_pipeline.py` |
| 4 | 在 PowerPoint 中實際點選、改字、改表格／圖表資料 | **Eric** | 步驟 2 |
| 5 | 視覺：溢出、遮擋、標題焦點、Banner 標題位置、留白 | 部分自動；**Eric 核准** | 文字量測（G6）自動；最終美感由 Eric 決定（`visual_approval: pending-eric`） |
| 6 | 內容正確性：數字只能出自 brief，缺資料標「待補」 | 自動 ✅ | G7 閘門 + `test_pipeline.py` 獨立檢查表格與圖表數值 |
| 7 | 語言：zh-TW／en／JP | 自動 ✅（字型檔需人工） | JP theme `ea` = Noto Sans JP；三語自然語言大綱 → 簡報（`test_acceptance.py`）。字形顯示需安裝字型後目視 |
| 8 | 動畫 | 未驗證 | generator 不加動畫，QA 標 `animation_verified=false` |
| 9 | 來源安全：source-library 未被改動 | 自動 ✅（有 LFS 時） | `test_pipeline.py` SHA256 前後比對 |
| 10 | 可重現：clone + 安裝 + LFS + 指令即可重現 | 自動 ✅ | CI 即全新環境；同一 brief 兩次產出 plan 完全相同（`test_acceptance.py`） |
| — | 改稿流程：改一段內容，其他頁版型不變 | 自動 ✅ | `test_acceptance.py` RevisionFlow（逐段修改，所有 fixture） |
| — | 至少一份 10～15 頁簡報 | 自動 ✅ | `test_acceptance.py` DeckSize |

## Eric 需要做的（約 10 分鐘）

先依 `README_V01.md` §2 安裝 Noto Sans TC／JP、B612 Mono。

驗收檔在 `presentation-skill/review/phase4/`（6 份，用目前程式以 `--no-render` 產生，QA 全部 PASS；每份旁邊有 `.plan.json`、`.qa.json`）。

1. **開啟測試**：用 PowerPoint 逐一開啟 `review/phase4/` 內 6 個 `.pptx`。
   - 沒有出現「PowerPoint 發現內容有問題…要修復嗎？」→ 通過。
2. **編輯測試**：表格用 `police-xr-overview.pptx`，圖表用 `bxr-presentation-system.pptx`：
   - 點任一頁標題改字；
   - 雙擊表格改一格；
   - 圖表按右鍵「編輯資料」改一個數字，圖表跟著變；
   - 「檢視 → 投影片母片」把 Logo 換位置，關閉母片後確認所有內容頁一起變。
3. **視覺**：看封面、章節頁、內容頁是否可以接受；不滿意的頁面直接告訴 Claude 頁碼與原因。

回報格式：「1 通過／不通過、2 通過／不通過（哪一步）、3 哪幾頁要改」。
