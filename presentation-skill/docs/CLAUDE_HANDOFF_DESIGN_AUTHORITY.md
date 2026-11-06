# Claude Code — 前置資料交接（不指定排版）

## 權責界線
**Claude 是 PPT 最終視覺設計者與程式實作者。** 此專案前置準備只交付素材、索引、原始資料、格式契約、品質測試、使用者確認過的美術意圖，不制定標題座標、字級大小、光效位置、圖表造型或美術排版。

已確認的視覺意圖：
1. 封面：圖像主題在左側約 1/3，右側 2/3 提供標題空間；文字應與光點形成關聯，不能只是遠離光點的孤立標題。
2. 章節過渡頁：文字必須靠近或呼應背景上的亮點，形成明顯視覺重心。實際編排由 Claude 決定。
3. 內容頁：**深藍色頂部 Banner 是標題區**；下方大面積純白留給內容。不得將主標題放到白色內容區，讓 Banner 只剩裝飾。
4. PowerPoint：Logo 由真實母片／版面配置統一管理，不逐頁貼；字體與配色從 Theme／母片繼承，並由 Claude 決定字級階層與版面細節。
5. 所有標題／日期／圖表／文字可自由修改；背景只保留畫面。不得把各頁壓成一張圖片。
6. 使用者已確認的三張 PNG 是背景素材，不是 ChatGPT 對文字位置的驗收。

## 權威資訊與路徑
- `00_Brand_Guidelines/v3.2/`：品牌規範原文，優先權最高。
- `02_Color/BXR_Colors_v3.2.json`：配色值。
- `03_Fonts/`：字型與授權說明。
- `01_Logo/`：官方 Logo 原稿。
- `07_Templates/BXR_Presentation_Template_v3.2.pptx`：官方 PowerPoint 參考母片。
- `04_Graphics/Icons/`：官方 SVG、額外 ICON、插畫。
- `presentation-skill/approved-layouts/military-tech/`：封面、章節過渡、內容頁三張背景 PNG。
- `presentation-skill/source-library/`：商業 PPTX 素材，保持唯讀。
- `presentation-skill/catalog/`：機器索引與資料 Schema。
- `presentation-skill/config/presentation-theme.json`：工程色票和意圖；**不是正式排版規格**。

## 現有腳本及限制
- `scripts/index-pptx.py`：以 XML 結構生成投影片與來源檔索引，非視覺分類。
- `scripts/select-layout.py`：基於審核欄位的初版檢索示範，尚非完整排版推薦引擎。
- `scripts/validate-pptx.py`：檢查 ZIP／OOXML 結構，不能取代 PowerPoint 的視覺驗收。
- `scripts/apply-bxr-theme.py`：套用部分 Theme／Master 預設樣式，需檢查母片繼承與色彩一致性。
- `scripts/build-military-pilot.js`：**僅技術煙霧測試**。當中的位置、尺寸、字級與內容標題放白底的設計**已被使用者否決**；禁止拿它當正式排版樣板。

## Claude 接手的工作（只有程式／美術設計實作）
- 研究母片與版面繼承的技術機制，建立可維護的真實 PPTX 主題模板。
- 產生所有可見文字／圖像的適當版型、動線與資訊層級並交付視覺審查。
- 將商業來源拆成可搜尋、可編輯、可安全重用的版型；保持來源唯讀。
- 實作自然語言 -> 大綱 -> 選版 -> PPTX -> 渲染 -> QA 的全流程。
- 必須用 PowerPoint 或相容的檢查程序測試動畫、字型替代、母片繼承、內容可編輯性。
- 先以封面、章節、內容各一頁做視覺驗收，再擴充不同用途版型。

## 交接完成標準
前置資料不得宣稱「文字已排版正確」。工程準備完成的意思是：素材可讀、來源可追溯、Schema 可用、工具可啟動、驗收條件明確。**正式版型美感與排版規格由 Claude 決定，並由使用者最後核准。**
