# Phase 2 — 正式母片視覺驗收（v0.1，待 Eric 驗收）

**檔案**
- 母片：`templates/BXR_Military_Master_v0.1.pptx`（`.potx` 範本同目錄）
- 驗收簡報：`review/phase2/BXR_Master_Review_v0.1.pptx`（8 頁，每個版面配置至少一頁）
- 預覽：`review/phase2/preview/*.png`、總覽 `BXR_Master_Review_v0.1_contact.png`、PDF
- 重新產生：`python presentation-skill/scripts/build-master-review.py`

## 設計決策對照表

| 需求（使用者已確認） | 本設計做法 | 可在哪裡修改 |
|---|---|---|
| 封面左 1/3 圖像、右 2/3 文字 | 文字欄從 5.60 in（42%）開始，完全避開左側斜切畫面 | Slide Master › BXR Cover |
| 封面標題與光點呼應 | 地平線光帶（畫面高 71.8%）當作標題基線：標題靠下對齊，「站」在光線上；長標題會往上長，不會壓到光線。2 px 品牌紅 Reality Line 從標題左緣起，延伸進青色光暈。副標與日期放在光線下方 | 同上 |
| 章節頁文字靠近光點 | 大型品牌紅章節號（96 pt）站在光帶上，緊鄰光點（66%, 65.5%）；英文標籤與章節標題接在光線下方 | BXR Section |
| 內容頁標題在上方 Banner | 標題（24 pt 白）＋技術標籤（B612 Mono 9 pt）都在 Banner 內；Banner 光點正好落在標題開頭下方；Banner 以下全白 | BXR Title + Body / Two Content / Title Only / Chart + Text |
| Logo 由母片管理 | 封面／結尾：H_Reverse（CIS：深色底首選）；章節：Symbol_White；內容頁：頁尾右側 H_Color。投影片上沒有任何 Logo 物件 | 各版面配置 |
| 字型／色彩由 Theme 管理 | Theme：Noto Sans TC（主／副），CIS 色票（accent1 Graphite、accent2 BxR Red…）；技術標籤 B612 Mono | Theme |
| 背景不可變形 | 背景放在版面配置的 `<p:bg>`（不能被誤拖動），並以 srcRect 精準裁切成 16:9，不拉伸 | — |

## 字級階層（Claude 決定，依 CIS Type Scale 與「會議室投影」可讀性）
封面標題 40 pt · 結尾 36 pt · 章節號 96 pt · 章節標題 30 pt · 內容標題 24 pt · 內文 18→16→14 pt（依內容量自動選字級，最小 16 pt）· 卡片標題 22–16 pt · 技術標籤 B612 Mono 9–10 pt 全大寫 · 頁尾 8–9 pt。全部使用 Regular（CIS：不用 Bold；投影不用 Light 300）。

## 紅色使用（CIS：品牌紅是唯一焦點）
Reality Line（每頁一條）、章節號、Logo。條列符號、流程節點、卡片色條用 Graphite 或領域色（例如警察藍 #2E5C9A）。數字標題用 Text Red #A51C40。

## 已知限制
- 預覽用 LibreOffice 渲染。Windows PowerPoint 的換行與字距可能略有差異，請在 PowerPoint 開啟確認。
- 需安裝 Noto Sans TC 與 B612 Mono（OFL 授權，免費）。未安裝時 PowerPoint 會改用替代字型。
- 背景 PNG 解析度是 1671×941，全高清投影會略軟。若有更高解析度的原檔可直接替換。
