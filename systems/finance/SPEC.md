# 財務系統（費用管理）— 開發規格

> 整理自《活動管理系統 — 開發規格書》的費用管理模組。依 Eric 2026-11-13 指示，**財務獨立成單獨的系統**：
> 獨立的 `index.html`、獨立的 Supabase 專案（資料庫、Auth、Storage、Edge Functions）、獨立的 migration 與部署，不依賴 CRM。
> 共用規則（架構、流程、安全、風格、SQL、RLS 原則、踩過的坑）見 [../COMMON_DEV_RULES.md](../COMMON_DEV_RULES.md)。

## 1. 概述

展覽預算、費用單據＋品項、付款對象、附件、台銀匯率、預算執行率；匯出請款單與差旅報告單。

**使用者**：公司內部 5 人（1 admin、3 editor、1 viewer）。帳號在財務系統的 Supabase 專案另外建立。

**使用情境**：出差／參展後登打費用，之後匯出請款單與差旅報告單。

**外部服務**：台灣銀行牌告匯率 CSV（在 Edge Function `bot-rate` 內抓）。

## 2. 資料庫 Schema

### 2.1 基礎
```sql
profiles                -- 對應 auth.users，決定角色
  id uuid PK → auth.users(id) on delete cascade
  email, name text not null
  role text check in ('admin','editor','viewer') default 'viewer'
  department, title text          -- 匯出請款單時帶出申請人職稱

exhibitions             -- 財務自己的展覽主檔（含預算）
  id uuid PK
  name text not null unique
  budget numeric default 0
  country, series, note text
  year int
```
`handle_new_user()` trigger 與 `get_my_role()` 見共用規則 §8。

### 2.2 費用資料表
```sql
payees                   -- 付款對象主檔
  name text not null
  bank_short_name, bank_code, branch, check_no
  bank_account, account_holder, swift_code, note

expense_documents        -- 單據（一張發票/收據一筆）
  exhibition_id → exhibitions
  date date not null
  category text not null
  expense_type text check in ('個人','公用')
  applicant_id → profiles  not null      -- 申請人／代墊人
  vendor, route_from, route_to text
  currency text default 'TWD'
  rate numeric default 1                 -- 匯率，可手動覆寫
  payment_method, invoice_no text
  payee_id → payees, payment_terms, expected_payment_date   -- 只有「公用」才用
  note, created_by, created_at

expense_items            -- 品項（一張單據可以有多筆）
  document_id → expense_documents on delete cascade
  item text not null
  amount numeric not null
  tax_rate numeric not null default 0                        -- %
  tax_amount numeric GENERATED ALWAYS AS (round(amount*tax_rate/100,2)) STORED
  attachments text[] default '{}'        -- 附件掛在「品項」上，不是單據
  sort_order int default 0

expense_items_expanded   -- view（security_invoker = true）
  -- 把單據欄位攤平到每個品項，報表/匯出/儀表板都查這個
```

### 2.3 Storage
| bucket | 用途 | 公開 |
|---|---|---|
| `attachments` | 費用品項的收據／發票 | 否 |

```
attachments/{單據id}/{品項id}/{timestamp}_{序號}_{檔名}
```

## 3. 權限（RLS）
依共用規則 §8（select 所有登入者；寫入 admin/editor；profiles 僅 admin 可改）。
財務資料含銀行帳號，**`payees` 是否要再收緊為僅 admin/editor 可讀**，列為待決事項。

## 4. 業務規則

### 4.1 費用分類（決定匯出哪種單據）
| 類型 | 類別 | 匯出 |
|---|---|---|
| **個人費用** | 機票、交通、住宿、餐費、交際費 | 差旅報告單 |
| **公用費用** | 攤位費、裝潢、設計、印刷、設備租借、運輸、保險、行銷宣傳、贈品、雜支、**人員** | 請款單 |

- 「**人員**」刻意歸在**公用**：現場請的翻譯、showgirl 等臨時人力，成本屬於這場展覽，不是代墊員工的個人費用。
- 「起訖地點」只在 **機票／交通／運輸** 顯示。
- 付款對象／付款條件／預計付款日只在 **公用** 顯示。

### 4.2 匯率（Edge Function `bot-rate`）
- 來源：`https://rate.bot.com.tw/xrt/flcsv/0/{YYYY-MM-DD}`
- **用欄位位置解析，不是文字標籤**（中英文版標籤不同但位置固定）：
  `cols[2]=現金買入, cols[3]=即期買入, cols[12]=現金賣出, cols[13]=即期賣出`
- 查無資料（假日）自動往前找最近 7 天。
- **預設帶入「現金賣出」**（財務核算用）。
- 匯率欄位**永遠可以手動覆寫**。
- 支援幣別（台銀有牌告的 19 種）：`USD HKD GBP AUD CAD SGD CHF JPY ZAR SEK NZD THB PHP IDR EUR KRW VND MYR CNY`；其他幣別手動輸入匯率。

### 4.3 品項與附件
- 編輯單據時品項**不可「刪除再新增」**：Storage 路徑用品項 id 組成，id 變了附件連結就失效。
  正解：新列先用 `crypto.randomUUID()` 產生穩定 id，改用 `upsert()`，只刪真的被移除的列。

## 5. 前端畫面
```
登入後
└─ 🏠 總覽：展覽數／總預算／總支出／總差異
   ├─ 圖表：各展覽預算 vs 支出、費用類別佔比、展覽執行率
   └─ 子分頁：費用明細 ／ 展覽總覽
   └─ 使用者管理（admin）
```

### 費用表單（兩層）
```
單據（header）：展覽/日期/類別/申請人/廠商/幣別/匯率/付款方式/發票號碼/付款對象…
└─ 品項（可多筆）：品名摘要 | 外幣金額(標籤隨幣別變) | 台幣金額(自動) |
                    稅率% | 稅額(自動) | 附件(每筆各自上傳)
   └─ 下方顯示：外幣合計、台幣合計   ← 合計要在品項「下面」才看得懂
```

## 6. 部署
共用步驟見 [../COMMON_DEV_RULES.md](../COMMON_DEV_RULES.md) §10。財務專屬：
1. 建立**獨立的** Supabase 專案（不與 CRM 共用）。
2. Storage 建 `attachments` bucket（Public 關閉）。
3. 部署 Edge Function `bot-rate`（台銀匯率）。

## 7. 尚未完成（下一階段）
| 項目 | 說明 |
|---|---|
| **從原系統拆分** | 原本與 CRM 在同一個 `index.html` 與同一個 Supabase 專案；需拆出獨立前端、建立獨立專案並搬移費用相關資料表、資料與 Storage 附件 |
| **請款單／差旅報告單匯出** | Excel 匯出，申請人職稱從 `profiles.title` 帶出 |
| **bot-rate Edge Function** | 從頭到尾沒有成功部署過，台銀匯率查詢在線上是壞的 |
| **草稿暫存** | 表單填到一半先存本機 |
| **payees 讀取權限** | 是否收緊為僅 admin/editor 可讀（含銀行帳號） |
| **展覽主檔與 CRM 的對應** | 兩邊展覽清單是否同步、如何對應待決 |
