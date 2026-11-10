---
name: bxr-company-deck
description: 產生符合 Big x Reality CIS v3.2 的可編輯 PPTX 簡報。當使用者說「做一份公司簡報」、「做一份簡報」、「幫我做簡報／PPT」或要求產生 Big x Reality 簡報時使用。
---

# 做一份公司簡報（Big x Reality）

使用 `presentation-skill/bxr_deck` 產生器，輸出可在 PowerPoint 直接編輯的 PPTX。

## 1. 準備環境（每個新對話第一次使用時）
```bash
python3 -c "import pptx, jsonschema, lxml, PIL" 2>/dev/null || python3 -m pip install -q 'jsonschema>=4.18,<5' python-pptx lxml pillow
```
字型只影響預覽圖；沒有 Noto Sans CJK 時仍可產生 PPTX（雲端環境的設定腳本會預先安裝）。

## 2. 決定內容
- 使用者只說「做一份公司簡報」、沒有提供內容 → 直接用本資料夾的 `company-profile.json`（公司簡介，內容全部出自 CIS v3.2 手冊 P.03–04、P.52，每段附來源）。
- 使用者有指定主題、對象、語言、頁數或資料 → 依此寫 brief（格式見 `presentation-skill/contracts/presentation-brief.schema.json`），或把大綱轉成 brief：
  `python -m bxr_deck brief --text outline.txt --id <id> --output <id>.json --audience external --slides N`
- 規則：**不得虛構**產品參數、客戶、效益數字；沒有資料就讓系統標示「待補」。語言只用 `zh-TW`、`en`、`JP`。企業簡報 `sector` 用 `corporate`（不持槍主視覺）。

## 3. 產生與檢查（在 `presentation-skill/` 執行）
```bash
python -m bxr_deck build --brief <brief.json> --output /tmp/bxr-out/<id>
```
- 結束碼 0 = QA PASS；1 = QA 未過（看 `<id>.qa.json` 的 gates）；2 = brief 格式錯誤。
- 有 LibreOffice 時會在 `preview/` 產生每頁 PNG：看總覽，確認沒有溢出、重疊或孤字，再交付。
- 輸出放在 Repo 以外（例如 `/tmp/bxr-out/` 或 scratchpad），不要提交到 Repo。

## 4. 交付
用 SendUserFile 把 PPTX 傳給使用者，並簡短說明頁數、各段內容、哪些地方標示「待補」需要補資料。

## 不可做
- 不逐頁插入 Logo（Logo 由母片管理）、不改 CIS 色彩、不把頁面壓成圖片。
- 不修改 `07_Templates/`、`00_Brand_Guidelines/` 與 `source-library/`。
