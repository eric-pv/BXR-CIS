# BXR Presentation Skill — V0.1 使用說明

自然語言／JSON brief → deck plan → **可在 PowerPoint 中直接編輯的 PPTX**（文字、表格、圖表皆為原生物件），
套用 CIS v3.2 的 Theme、Slide Master 與版面配置。Logo 只由母片／版面配置繼承，不逐頁插入。

## 1. 安裝

需求：Python **3.11+**、Git LFS。

```bash
python -m pip install python-pptx jsonschema lxml pillow
```

```bash
git lfs install
```

```bash
git lfs pull
```

- `git lfs pull` 會下載官方範本、母片 `.pptx/.potx` 與 source-library。沒有 LFS 檔時仍可產出簡報：
  generator 會偵測到 LFS pointer，改用程式即時重建母片（不覆寫追蹤中的範本）。
- **LibreOffice（選裝）**：只用於產生 PNG/PDF 預覽（`soffice` + `pdftoppm`）。不裝就加 `--no-render`。

## 2. Windows 字型安裝

簡報使用 Theme 字型；本機未安裝時 PowerPoint 會以替代字型顯示，版面量測會失準。以下皆為 SIL Open Font License (OFL)，可自由安裝與散布：

| 字型 | 用途 | 下載 |
|------|------|------|
| Noto Sans TC | 主要字型（zh-TW／en，CIS 約 90%） | https://fonts.google.com/noto/specimen/Noto+Sans+TC |
| Noto Sans JP | JP 簡報的東亞字型（Theme `ea`） | https://fonts.google.com/noto/specimen/Noto+Sans+JP |
| B612 Mono | 技術感輔助字（CIS ≤10%） | https://fonts.google.com/specimen/B612+Mono |

下載 ZIP 解壓後，選取所有 `.ttf/.otf` → 右鍵「為所有使用者安裝」，再重新啟動 PowerPoint。

## 3. CLI

在 `presentation-skill/` 目錄下執行：

```bash
python -m bxr_deck build --brief tests/fixtures/briefs/police-xr-overview.json --output out/ --no-render
```

- `--previous-plan out/<id>.plan.json`：修訂 brief 時沿用先前的版型選擇（slide id 以內容為鍵）。
- 結束碼：`0` QA PASS、`1` QA FAIL、`2` brief 不符合 schema（例如 `slides=0`、`language=ja`）。

把大綱文字轉成 brief（語言標記一律用 `zh-TW`、`en`、`JP`）：

```bash
python -m bxr_deck brief --text outline.txt --id my-deck --output my-deck.json --audience internal --slides 10
```

重建母片（`templates/BXR_Military_Master_v0.1.pptx`，加 `--potx` 另存範本）：

```bash
python -m bxr_deck master --potx
```

## 4. 輸出檔

| 檔案 | 說明 |
|------|------|
| `<id>.pptx` | 可編輯簡報；標題為 placeholder、表格為原生 `a:tbl`、圖表內嵌 Excel 資料表 |
| `<id>.plan.json` | 逐頁計畫，符合 `contracts/deck-plan.schema.json`；含 `unverified_claims` |
| `<id>.qa.json` | QA 報告：G1–G9 閘門、source-library 不變性、警告、`visual_approval: pending-eric` |
| `preview/` | （有 LibreOffice 且未加 `--no-render`）逐頁 PNG 與 contact sheet，僅供檢視，不會放進簡報 |
| `<id>.pdf` | brief 的 `output.pdf=true` 且有渲染時產生 |

投影片上出現的數字必須出自 brief（G7）；缺少的資料會以「待補資料／PENDING INPUT」標示，不會虛構。

## 5. 測試

```bash
python tests/test_contracts.py
```

```bash
python tests/test_master.py
```

```bash
python tests/test_pipeline.py
```

`test_pipeline.py` 以 `--no-render` 跑完 6 份 fixture，不需要 LibreOffice；source-library SHA256 檢查在沒有 LFS 檔時會 skip。

## 6. 限制

- 容器／CI 中**沒有 Microsoft PowerPoint**：結構檢查（ZIP/XML/rels/content types、Logo 繼承）已自動化，
  但「PowerPoint 開啟不需修復」與最終視覺仍需在 Windows PowerPoint 上人工確認。
- LibreOffice 預覽與 PowerPoint 的字距、換行可能略有差異。
- **動畫未驗證**：generator 不加入動畫，QA 中 `animation_verified=false`。
- 版型視覺仍待 Eric 驗收（`visual_approval: pending-eric`）；購買版型僅為參考來源，授權與公開散布需另行確認。
