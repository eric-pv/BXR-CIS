# 內部系統（活動管理 CRM ／ 財務系統）

> 來源：Eric 提供的《活動管理系統 — 開發規格書》（Google Apps Script → Supabase 的完整開發歷程）。
> 2026-11-13 依 Eric 指示納入本專案，並將**財務（費用管理）獨立成單獨的系統**，不再與 CRM 綁在同一個應用程式。
> 公司：GPT Taiwan（bigxreality）

| 系統 | 規格 | 內容 | 與簡報的關係 |
|---|---|---|---|
| **活動管理／CRM（ExhibitIQ）** | [crm/SPEC.md](crm/SPEC.md) | 公司／聯絡人、一人多重身分、聯絡方式、名片 AI 辨識、聯繫紀錄、待辦、展覽 × 聯絡人、展場即時錄音（規劃中） | 2027 行銷策略「商機轉換」章節的 ExhibitIQ 與 CRM |
| **財務系統（費用管理）** | [finance/SPEC.md](finance/SPEC.md) | 展覽預算、費用單據＋品項、付款對象、附件、台銀匯率、預算執行率、請款單／差旅報告單匯出 | 獨立系統，不屬於 CRM |
| 共用開發規則 | [COMMON_DEV_RULES.md](COMMON_DEV_RULES.md) | 技術架構、批次開發流程、安全規則、程式風格、SQL migration、驗證、踩過的坑 | 兩個系統都必須遵守 |

## 為什麼財務要獨立

- 日常動線不同：費用是出差／參展後登打與請款；CRM 是展場掃名片與業務追蹤。
- 權限與敏感度不同：財務資料（金額、銀行帳號、付款對象）不應與業務名單共用同一套存取範圍。
- CRM 之後要開放「客戶自填表單」給展場訪客（免登入），不能與內部財務工具放在同一個應用程式。

兩個系統各自有：獨立的 `index.html` 前端、獨立的 Supabase 專案（資料庫、Auth、Storage、Edge Functions）、獨立的 SQL migration 編號與部署步驟。
兩邊都會有「展覽」主檔；是否要同步（例如以展覽名稱對應）屬於**待決事項**，見各規格的「尚未完成」。

## 安全提醒（本 Repo 為 PUBLIC）

- 只能 commit `sb_publishable_...`；`sb_secret_...`、DB 密碼、Gemini API 金鑰一律走 Supabase secrets，絕不進 Repo、不寫進任何文件。
- 本資料夾只有規格文件，沒有任何金鑰或個人資料。
