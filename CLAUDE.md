# CLAUDE.md — Big x Reality Presentation Skill

> **Claude Code 的入口指令。** 本專案已完成大量素材與前置工程。**請直接執行開發，不要重新提案或要求使用者重新敘述已決定事項。**

## 首先閱讀（依順序）
1. [完整執行任務書](presentation-skill/docs/CLAUDE_CODE_EXECUTION_ORDER.md) — **本次工作的主指令**
2. [設計權責與使用者已確認的視覺要求](presentation-skill/docs/CLAUDE_HANDOFF_DESIGN_AUTHORITY.md)
3. [V0.1 工程契約與測試閘門](presentation-skill/docs/CLAUDE_V01_BUILD_CHECKLIST.md)
4. [Skill 主要規範](presentation-skill/skills/bxr-presentation/SKILL.md)
5. [CIS v3.2 官方規範](00_Brand_Guidelines/v3.2/) 與 [官方範本](07_Templates/BXR_Presentation_Template_v3.2.pptx)

## 終極目標
員工用自然語言提供主題、目的、內容與語言，系統能選擇、調整符合 CIS 的高品質版型，產出**可以在 PowerPoint 裡真正修改文字、表格、圖表、物件的 PPTX**。**Claude Code 負責正式美術排版、母片及程式**；既有 ChatGPT 試作品僅作技術參考，**不能照抄它的排版**。

## 必須遵守
- **內容頁上方深藍 Banner 是標題區**；下方維持乾淨白底供內容使用。
- 封面／章節頁：標題應與閃亮光點形成視覺重心；封面左側主視覺約 1/3，右側約 2/3 可放文字。**座標、字級和排版由 Claude 自行設計並交使用者驗收。**
- Logo 只能來自 `01_Logo/` 官方檔，透過真實 PowerPoint 母片／版面配置統一管理；不逐頁插 Logo。字型、主題色與共通文字樣式同樣用 Theme／母片管理。
- 遵循 CIS v3.2，不要把品牌紅改成軍警領域色，也不要直接把任何範例 PPTX 影像扁平化。
- 來源 PPTX／ZIP 唯讀。購買版型是候選材料，不等於已通過 BXR 視覺驗收。保持合法必要的授權標記。
- **目前 Repo 為 PUBLIC**，其中含第三方商業簡報素材。不要再上傳新的受限素材，並通知使用者需要確認公開散布／多人使用的授權與存取控制；不要擅自變更 Repo 權限。
- 所有程式開發在獨立 `dev/*` 分支，用 PR 交由使用者合併；**不要自行合併 `main`**。
- 不得虛構產品參數、客戶、效益數字或分析結果。使用 `zh-TW`、`en`、`JP`（不要使用 `ja` 作為本專案對外語言標記）。
- 程式必須有可執行測試與可下載成果，不要只寫架構文件。

## 立即執行
閱讀主指令後，先跑 `python presentation-skill/scripts/preflight.py --repo .` 和 `python presentation-skill/tests/test_contracts.py`（先安裝 jsonschema），檢查 Git LFS 與素材，接著按主指令的 Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 交付。遇到封鎖因素就記錄明確證據，繼續完成其餘不被阻擋的工作。
