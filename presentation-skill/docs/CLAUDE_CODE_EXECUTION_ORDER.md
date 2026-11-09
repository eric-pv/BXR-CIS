# BXR Presentation Skill — Claude Code 完整執行任務書

**本文件是給 Claude Code 的執行指令，不是提案。** 從讀取此文件開始，請進行實際開發、測試、產出與提出 PR；不要再次要求使用者重新提供已存在於 Repo 的素材，不要把大綱或空的 Skill 說成完成。

## 0. 目標、責任與完成定義

### 使用者最終目標
以 Big x Reality（全球動力科技）企業 CIS v3.2 為基礎，讓公司員工只需說明「做什麼、給誰看、幾頁、中文／英文／日文、附哪些資料」，系統便能：
1. 整理簡報結構與內容，保留來源證據；
2. 對應適當的官方或已驗收的外購 PPTX 版型；
3. 視內容選用公司正式 ICON、插畫和三種已核准的軍事科技背景；
4. 套用真正的 PowerPoint Theme、Slide Master 和 Slide Layout；
5. 產生高品質、**原生可編輯**的 PPTX，選用的動畫僅在實際驗證後聲稱保留；
6. 渲染每頁、執行結構驗證與視覺檢查，附可追溯的 QA 報告；
7. 依使用者回饋進行重製，而非交出一份不能修改的圖片簡報。

### Claude Code 責任
**Claude 擁有正式排版設計與程式設計的決定權**，包括視覺層次、座標、字級、版面配置、圖表、動畫的技術方案。請以官方 CIS 和核准背景設計為約束，自行提出可檢視的真正 PPTX 作品。絕對不要沿用 ChatGPT 先前三頁測試簡報的標題位置；該原型已被使用者否決為正式設計參考。

### 使用者已核准、不需再問的視覺事實
- **封面**：深藍黑、粒子／線框、人物與無人機／小型無人船在左側約 **1/3**，右側留 **2/3** 的可編輯文字區。標題與場景亮點／光線必須產生視覺關聯。
- **章節過渡頁**：同系列數位線框風格，章節文字應靠近或呼應背景的閃光視覺焦點，不能只是隨機貼字。
- **內容頁**：**最上方科技 Banner 專門承載標題**；**Banner 下方維持純白、乾淨**以放圖表、表格和內文。不要把主標題放進白色內容區。
- 三張 PNG 是**背景素材**，其中不包含可用於簡報的 Logo、標題或頁碼。標題／章節號／日期由原生 PPT 物件編輯。
- Logo 不逐頁加入，必須放母片／版面配置；字型、主題色、共通段落樣式也從 Theme／母片繼承。
- 使用 HTC 頭戴裝置外型、不要擅自改成其他頭盔；不要生成未核准的 HTC/VIVE 商標或自己畫公司 Logo。背景圖已核准，優先直接使用原圖。
- 公司對外品牌名稱：**Big x Reality**；品牌主色 **#D02753**。領域配色只是局部點綴，不替代企業色。遵守 CIS 原典。
- 使用者允許 Repo 內素材用於此專案開發，但「可以使用」**不等於**已確認外購素材有公開散布及多人授權；Repo 目前是 public，請提醒，不擅自改權限。

## 1. Repo 中已經有什麼：直接使用，不重造輪子

| 類別 | 絕對路徑（Repo 相對） | 用法 |
|---|---|---|
| 完整企業 CIS | `00_Brand_Guidelines/v3.2/` | 最高權威，閱讀兩部分 PDF 與版本說明 |
| Logo 官方檔 | `01_Logo/` | 依 CIS 選擇適當版本，母片中統一管理 |
| 品牌色 | `02_Color/BXR_Colors_v3.2.json` | 取代自行猜測色碼 |
| 字體／授權 | `03_Fonts/` | 主字 Noto Sans TC，技術輔字 B612 Mono，遵守比例與權重規範 |
| ICON／插圖 | `04_Graphics/Icons/` | 官方 SVG 與 Additional/Illustrations 分流 |
| 角色及主視覺 | `05_Characters/`、`06_KeyVisuals/` | 依需求挑選，保留原素材 |
| 官方範本 | `07_Templates/BXR_Presentation_Template_v3.2.pptx` | 讀取真實母片、字色與格式 |
| 已核准三張背景 | `presentation-skill/approved-layouts/military-tech/` | `BXR_Military_Cover_16x9.png`、`BXR_Military_Section_16x9.png`、`BXR_Military_Content_White_16x9.png` |
| 商業母版來源 1 | `presentation-skill/source-library/500頁.pptx` | 604 slide XML；原檔維持唯讀 |
| 商業母版來源 2 | `presentation-skill/source-library/Aviation Slides.zip` | 249 份真實 PPTX，合計約 5,184 slide XML；原檔維持唯讀 |
| ICON 目錄 | `presentation-skill/catalog/icon-catalog.csv` | 搜尋用途與標籤 |
| 版型紀錄 Schema | `presentation-skill/catalog/layouts.schema.json` | 目前只是舊版初稿，升級時保持相容／附遷移程序 |
| 前置色票設定 | `presentation-skill/config/presentation-theme.json` | 只是工程 Token／既有設計意圖，**不是 Claude 排版規格** |
| 使用者輸入 Schema | `presentation-skill/contracts/presentation-brief.schema.json` | 必須支援的輸入型別 |
| 投影片規劃 Schema | `presentation-skill/contracts/deck-plan.schema.json` | 應輸出的每頁資訊 |
| 已有測試需求 | `presentation-skill/tests/fixtures/briefs/` | 四種完整示例 |
| Schema 範例／測試 | `presentation-skill/tests/fixtures/expected-plan-police.json`、`presentation-skill/tests/test_contracts.py` | 資料契約測試 |
| 背景完整性校驗 | `presentation-skill/approved-layouts/military-tech/assets.sha256` | 必須通過 |
| 既有 Skill | `presentation-skill/skills/bxr-presentation/SKILL.md` | 延續修訂，不重建另一套 Skill |
| 之前交接文件 | `presentation-skill/docs/CLAUDE_HANDOFF_DESIGN_AUTHORITY.md`、`CLAUDE_V01_BUILD_CHECKLIST.md` | 工作界線、驗收清單 |
| GitHub CI | `.github/workflows/build-presentation-catalog.yml`、`.github/workflows/presentation-preflight.yml` | 索引再生及初步自動驗證 |

### 已有腳本（先測試，再決定重用或修正）
- `scripts/preflight.py`：檢查素材檔案、校驗碼、ICON 索引、需求測試資料；`--require-lfs` 會檢查 LFS。
- `scripts/index-pptx.py`：從大檔 PPTX 與 Aviation ZIP 建立**結構索引**，不等於視覺版型批准。
- `scripts/extract-aviation.ps1`：安全解壓真實 PPTX，過濾 macOS 垃圾檔。
- `scripts/select-layout.py`：僅示範粗略關鍵詞選版，**不可誤當正式智慧排版引擎**。
- `scripts/build-military-pilot.js`：3 頁 PPTX 技術煙霧測試；**它的美術排版不是核准版本**，內容頁標題錯放在白底，請修正設計時另行製作。
- `scripts/apply-bxr-theme.py`：部分 OOXML Theme／母片字體改寫；需檢查真正繼承與顯示是否正確。
- `scripts/validate-pptx.py`：OOXML 結構檢查，不能取代 PowerPoint 開檔、可編輯性、動畫及視覺 QA。

## 2. 工作方法：嚴格依階段執行，交付真的能用的東西

### Phase 0 — 進場、驗證與開發環境（先做，不花時間重畫架構）
1. 在 `main` 同步最新提交，建立 `dev/claude-v01-<feature>` 工作分支，不直接改 main；有多個獨立工作模組時分 PR。
2. 讀 `CLAUDE.md` 與上述文件、CIS v3.2、官方 PPTX，盤點 Python／Node／PowerPoint 或 LibreOffice、Git LFS 是否存在。
3. 執行：
   ```powershell
   git lfs pull
   python -m pip install "jsonschema>=4.18,<5"
   python presentation-skill/scripts/preflight.py --repo . --require-lfs
   python presentation-skill/tests/test_contracts.py
   ```
4. 測試現有 `index-pptx.py`、`select-layout.py`、`apply-bxr-theme.py`、`build-military-pilot.js`、`validate-pptx.py` 的實際運作。**有 bug 就改，不要只說理論上可行**。使用正式官方 Logo 的正確檔案，不能用假的、未核准的代用品。
5. GitHub Repo 目前是 public，商業來源可讀但有授權風險：不要複製商業檔進新的公開路徑；如使用者欲轉 private，可提出變更要求，但不得擅自處理。
6. 記錄 `tests/reports/preflight-*.json`、失敗案例、環境相容性及已知限制。失敗不代表所有後續工作都停止，可並行處理不受阻的任務。

**Phase 0 完成門檻**：預檢／Schema 測試能重跑，必要素材與版本被確認，兩套來源素材有唯讀證據；沒有「只有文件、沒執行測試」的報告。

### Phase 1 — 素材檢索資料庫（工程資料，不取代美術判斷）
1. 以既有索引器為起點，建立 604 頁大檔及 249 份 Aviation PPTX 的逐頁穩定 ID、來源／頁碼、檔案 hash、投影片角色候選、文字與圖片數、群組、圖表、動畫 XML、頁面比例、可編輯元素型態。
2. 為候選頁生成預覽縮圖及 contact sheets；縮圖只能用來評估選版，不能當正式輸出投影片。考慮批次／快取／逾時重試，別每次全量解壓；遇到特大 XML 要留下 `unparsed` 原因而不是默默漏掉。之前記錄 **29 頁 XML 過大**。
3. 標記來源版型尚未批准。只有經過 Claude 視覺審查和使用者確認，才能改成 `cis_approved`；不可以把「掃描成功」等同「可直接套用」。
4. 正確記錄來源第三方 Logo、水印、授權要求。不要剝除必須保留的署名。
5. 對接 ICON CSV，建立標籤搜尋、來源路徑與可能色系；12 個官方 SVG 優先於未統一風格的額外 PNG。
6. 建立明確的**素材路徑 → 候選版型 → 已驗收版型**狀態流程。

**交付**：可查詢的 `catalog/` 資料、縮圖或預覽生成程式、來源異常報告、選版索引 API／函式及測試。若網頁展示工程中可用，可留到 Phase 4。

### Phase 2 — 正式母片／三頁美術驗收（Claude 全權設計）
1. 仔細檢查官方 v3.2 PPTX 的真正 Slide Master、Layouts、Theme fonts／color map、Logo 版本與標題樣式，**以實際素材為準**。
2. Claude 自行設計含三種指定 PNG 的正式母片／版面：封面、章節過渡、白底內容頁。
3. 必須使視覺焦點成立：封面與過渡頁標題呼應光點；**內容頁標題就在上方 Banner**；白底留給內容。
4. Logo 使用官方檔，放在 Slide Master／Layout，而不是逐頁新增。PowerPoint 原生可編輯文字與佔位符；Theme／母片管理共通字型、字色、品牌主色、文字階層；Claude 決定具體大小。
5. 不可把繁雜投影片先整張截成圖再放入簡報當成「可編輯」；表格、文字、圖表、流程必須可分別調整。
6. 對比光點可讀性／Banner 標題空間，提供**真實 PPTX + 每頁 PNG 預覽 + 對照表**給使用者驗收；這是重要的人類視覺審核點，不需要重問設計方向。
7. 不要把 `build-military-pilot.js` 中原始的文字座標與字級當成設計規格。

**交付**：`*.pptx`（必要時另交 `*.potx`）、三頁渲染預覽、母片結構測試、供使用者驗收之 PR。若使用者未批准版型，保留為 draft，不聲稱正式可用。

### Phase 3 — V0.1 生成器（以能產出一份好簡報為優先）
1. 依 `contracts/presentation-brief.schema.json` 接收需求，可由自然語言產生符合 Schema 的 brief；支援 `zh-TW`、`en`、`JP`。
2. 產出符合 `contracts/deck-plan.schema.json` 的每頁計畫。每頁需有主旨、使用的事實來源、角色、選版來源、可編輯元素與 QA 標記。
3. 自動整理大綱、處理內容重複與過密、選擇適當的版型；必要時可合理新增內容頁，但不得編造資訊。若缺少足以支撐某頁的證據，標明待補而非假造。
4. 第一版先支持 **10～20 頁**簡報及不同頁型組合；可先使用官方 PPTX、三張核准背景、少量經 Claude／使用者審查的複雜版型。**不需要把 5,788 頁都轉換完成才能上線原型。**
5. PPTX 原生物件：標題、段落、表格、圖表和可編輯圖形。圖表使用可編輯資料來源；圖片維持合適的比例／裁切。必要的動畫保留只在經原生 PowerPoint 驗證後承諾。
6. 輸出：
   - `output/<brief-id>.pptx`
   - `output/<brief-id>.plan.json`
   - `output/<brief-id>.qa.json`
   - `output/preview/*.png`（每頁預覽）
   - 使用者要求時 `output/<brief-id>.pdf`
7. 需要具備改稿流程：修改 brief 或一頁內容後，可重新產生，不破壞其他已經核准的頁型選擇，保留來源記錄。
8. 提供一個明確可執行的入口，例如 `python ... --brief ... --output ...` 或 Node CLI；若本機執行需要外部 AI Token／付費 API，將設定寫入 README，**不要硬寫金鑰**。未接 API 的測試模式仍應能使用 fixtures 產出決定性結果。

**交付**：CLI 或工作流程、實際 PPTX 檔、計畫／QA JSON、全部測試的結果、說明如何在 Windows PowerPoint 上開啟。

### Phase 4 — 真正驗收／整合交付
必須實際執行以下測試，未通過就追修：
1. **資料契約**：所有四份 brief fixture 和預期 plan 通過 JSON Schema；錯誤輸入會被拒絕。
2. **結構**：生成的 PPTX 可開啟、ZIP／OOXML 有效、投影片與版面數正確，檔案不會要求修復。
3. **母片**：修改 Master／Layout Logo 時，共用該版面的頁面一起更新；沒有每頁重複插入 Logo。主題色與字體從 Theme／母片繼承。
4. **可編輯性**：每個要求可編輯的元素實際在 PowerPoint 中可選取、改字、改表格／數據，不只有圖片。
5. **視覺**：逐頁渲染檢查溢出、遮擋、標題焦點、留白、字體替代、Banner 標題位置、跨頁風格與資訊層次。**視覺品質由 Claude 設計及使用者核准**；程式化 QA 不能取代目視。
6. **內容正確性**：拒絕虛構規格、客戶、ROI、實測效益；保留每頁來源及未知資訊狀態。
7. **語言**：繁體中文、英文及 `JP` 對應語系測試，確認字形、換行與替代字型。
8. **動畫**：保留原版動畫的頁面實際播放測試；未驗證明確標成未驗證。
9. **來源安全**：原始 PPTX／ZIP 沒被改動、沒有把帳密／API Key／商業素材再貼進公開網頁或 log。
10. **可重現**：新環境 `git clone` + 安裝依賴 + LFS + 執行命令，就能重現至少一組符合預期的簡報與 QA 報告。

**V0.1 完成定義**：至少一份 10～15 頁的實際簡報能正常開啟、具有真正母片、文字與主要圖表可編輯、封面／過渡／內容頁排版經使用者確認，所有預檢通過，並有再生指令與清楚的限制說明。若使用者尚未驗收美術，請標為「待驗收」，不冒稱正式發布。

## 3. 必須遵守的 GitHub 工作流程
- 所有功能各自建立 `dev/*` 分支與 PR。若分工並行，先定義檔案擁有權，避免改動同一原始商業素材。
- 每個 PR 需寫明修改內容、實際執行的測試命令及結果、哪些案例未測、輸出預覽位置、風險。
- 任何改動不可破壞原有官方 v3.2 檔案。來源與核准版型分目錄；不得把新的付費素材無差別提交公開 Repo。
- 如果先前測試腳本有缺陷，以程式測試結果為準，修復後再交，不可把早先 ChatGPT 的敘述視為已驗證證據。
- 不要自動合併 PR，交由 Eric 人工合併，保持歷史可追蹤。

## 4. 分工與阻擋因素
- **Claude Code**：美術／母片設計、開發、調整、視覺渲染／測試、撰寫 PR。
- **ChatGPT**：既有前置素材、規格／測試案例／資料契約補齊、PR 檢查及協助使用者驗收；不是正式美術設計師。
- **Eric**：核准正式版型與 V0.1 成品、確認使用情境、授權及 Repo 權限、決定 PR 合併。
- 真正受阻時，具體記錄無法執行的指令、錯誤輸出與所需外部授權／環境；不要用籠統「需要更多資訊」停止所有開發。

## 5. 你現在的第一個動作

**不要回覆一大篇計畫；直接開始。**

1. 讀本文件與 `CLAUDE.md`。
2. 建立第一個實作分支，跑 Phase 0 的命令。
3. 提交最小可行的正式母片／三頁渲染及程式測試（分支與 PR）。
4. 根據實際問題修程式，接著擴充到第一份 10～15 頁完整簡報。
5. 彙報的格式只需：**已完成、可驗證連結／檔案、測試結果、待 Eric 驗收、阻擋問題、下個開發 PR**。

> 核心原則：**由 Claude 決定排版，由可執行測試判斷工程，由 Eric 判斷最終視覺是否合格。**
