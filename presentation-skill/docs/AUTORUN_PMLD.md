# AUTORUN — 500頁（PMLD）版型補完

PMLD=IN-PROGRESS
最後更新：2026-11-09T13:10Z
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
| P2 新 variant（layouts.py） | DONE | 14 個新 variant（見下表），3 輪「渲染 → 目視 → 修正」：共用字級（同頁同字級、單行優先但不小於換行字級 4 pt 以上、量測保留 12% 安全餘量）、窄格縮小內距、卡片／標籤高度依實際行數 |
| P3 registry 重建 + tests/test_pmld_layouts.py | DONE | registry 17 → 31 筆（只新增，舊紀錄不變，新紀錄 claude-reviewed、approved=false）；新測試 9 項（登記、參考頁政策、版面邊界、文字量測、可編輯性、主視覺預算與不持槍、選版可達）；CI workflow 加一步 |
| P4 樣張與 fixture 渲染目視驗收、全部測試、draft PR | IN-PROGRESS | |

## 已知問題
- `07_Templates/BXR_Presentation_Template_v3.1.pptx`、`v3.2.pptx` 在工作樹顯示為已修改（以一般 blob 提交，但 `.gitattributes` 設 `*.pptx` 為 LFS）。不提交、不修改、不還原。
- 給 A／B 的提醒：`scripts/select-layout.py` 以 `f"PMLD-{p:04d}"` 處理 `ref`，只接受整數頁碼；工作 A 的 `ref` 是字串 `"AVI-<deck>-<page>"`，A 合併後 `--write-registry` 會失敗，`test_registry_in_sync_with_variants` 也會失敗。需在 A 或 B 的 PR 中讓 select-layout 接受字串 ref。

## 使用者決定：地圖參考範圍（2026-11-09，Eric）
公司不做中國業務，中國地圖不保留；台灣與世界地圖保留。供工作 A（地圖家族）採用：
- 可參考：世界地圖 PMLD-0458、0459、0460、0461、0462、0463；台灣輪廓 PMLD-0501、0518、0569、0603（只取輪廓形狀；0501「中國・台灣」、0569「台灣省」等來源標籤一律不採用）。
- 排除：其餘中國全國／省市地圖頁（PMLD-0464–0500、0502–0517、0519–0568、0570–0602、0604）。
- Aviation 地圖也比照：只用世界與台灣地圖。

## 新增版型（P2）
| variant | 家族 | 項目數 | 參考頁（PMLD） | 說明 |
|---|---|---|---|---|
| agenda.arc-nodes | agenda | 2–6 | 19, 41 | D 形主視覺＋沿弧線的圖示節點與分隔線 |
| agenda.number-strip | agenda | 3–7 | 28, 24, 18 | 寬幅主視覺＋下緣重疊的編號格列 |
| agenda.tiles | agenda | 3–6 | 25 | Paper 底＋錯落編號卡片＋虛線路徑（不用圖片） |
| items.pill-list | items | 2–5 | 41, 47 | 圓角主視覺＋深色膠囊條與白色圖示圓 |
| items.slant-panels | items | 3–4 | 92, 96, 97 | 每項一片斜切主視覺＋同斜率標籤 |
| items.overlap-cards | items | 3–4 | 62, 44 | 主視覺帶＋下緣重疊的白色圖示卡片 |
| items.zigzag | items | 2–3 | 65, 71, 72 | 圖文左右交錯、深色文字區塊重疊 |
| items.quad-center | items | 4 | 177, 178 | 田字格四區＋中央圓形主視覺 |
| items.capsules | items | 3–4 | 411, 415, 419 | 錯落膠囊形主視覺＋下方標題 |
| process.loop | process | 3–6 | 239 | 環形循環節點＋方向箭頭＋中央圓形主視覺 |
| process.staircase | process | 3–5 | 438, 439, 444 | 逐階上升的欄位＋平行上升箭頭（不用圖片） |
| process.numbered-panels | process | 3–5 | 100, 156, 201 | 每步一張主視覺＋大號等寬數字說明條 |
| text.framed-visual | text | 1–3 | 49, 63 | 偏移相框主視覺＋主陳述與編號次陳述，垂直置中 |
| text.thumb-list | text | 2–4 | 127, 104 | 陳述列＋編號塊＋列尾縮圖 |

未採用（與理由）：人物／團隊、時間軸、地圖、產品樣機頁 → 屬平行工作 A 的家族；證書與獎盃（PMLD-0297–0366）→ 沒有 BXR 事實可放、容易誘導虛構；合作夥伴 Logo 牆（0356–0366）→ 第三方商標、暗示虛構客戶；販售者 QR code／版權頁（0003、0004）→ 來源商標。數據頁的甜甜圈／圓餅（0045、0135、0282 等）→ generator 的數據頁不經過 variant，需改 generator（平行工作 B 的檔案），列為後續。
