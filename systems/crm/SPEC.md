# 活動管理／CRM（ExhibitIQ）— 開發規格

> 整理自《活動管理系統 — 開發規格書》的 CRM 模組。財務（費用管理）已獨立，見 [../finance/SPEC.md](../finance/SPEC.md)。
> 共用規則（架構、流程、安全、風格、SQL、RLS 原則、踩過的坑）見 [../COMMON_DEV_RULES.md](../COMMON_DEV_RULES.md)。

## 1. 概述

客戶名單 CRM：公司／聯絡人、多重身分、聯絡方式、名片 AI 辨識、聯繫紀錄、待辦事項、展覽 × 聯絡人。

**使用者**：公司內部 5 人（1 admin、3 editor、1 viewer）。

**使用情境**
- 展場現場用手機掃名片建客戶名單
- 平時業務開發、上門客戶也用同一套 CRM 記錄
- 行銷建立自己的供應商與媒體人脈網絡（禮贈品、印刷、電視台、報社…）

**外部服務**：Google Gemini API（名片辨識，在 Edge Function 內呼叫）。

## 2. 資料庫 Schema

### 2.1 基礎
```sql
profiles                -- 對應 auth.users，決定角色
  id uuid PK → auth.users(id) on delete cascade
  email, name text not null
  role text check in ('admin','editor','viewer') default 'viewer'
  department, title text

exhibitions             -- CRM 自己的展覽主檔（財務系統另有一份；是否同步為待決事項）
  id uuid PK
  name text not null unique
  country, series, note text
  year int
```
`handle_new_user()` trigger 與 `get_my_role()` 見共用規則 §8。

### 2.2 CRM 資料表
```sql
identity_weights         -- 身份權重（僅 admin 可改）
  category text PK, weight numeric not null
  -- 初始：軍人10 警察10 消防員8 政府官員9 民間企業3 學術機構3 一般民眾1 其他1

companies                -- 單位主檔（客戶、供應商、媒體、社團都放這裡）
  name_original, name_english text
  company_type text not null default '客戶'
    check in ('客戶','供應商','媒體','合作夥伴','社團組織','其他')
  industry text          -- 禮贈品/印刷/展場設計/電視台/報社…（自由填，前端給 datalist）
  website, email_domain, country
  address_original, address_english, note

contacts                 -- 人
  name_original, name_english
  country, address_original, address_english
  importance text default '未分類' check in ('A','B','C','未分類')
  customer_type text
  identity_category → identity_weights(category)
  department_relevance / enthusiasm / close_probability  int check between 1 and 5
  avatar_photo_url text
  owner_id → profiles                    -- 負責業務
  status text default '新名單'
    check in ('新名單','追蹤中','已報價','已成交','已流失')
  deal_amount numeric, deal_date date, note

contact_affiliations     -- ★ 人 ↔ 單位 多對多（一人多重身分）
  contact_id → contacts on delete cascade  not null
  company_id → companies on delete cascade          -- 允許 null（只有職稱沒單位）
  title_original, title_english
  department_original, department_english
  responsibility text    -- 例如「採購決策者」「跑國防線記者」
  is_primary boolean default false
  UNIQUE INDEX (contact_id, company_id)

contact_methods          -- 一個人多筆聯絡方式
  contact_id → contacts on delete cascade
  type text not null     -- email/mobile/office_phone/fax/website/LINE/WhatsApp/WeChat/LinkedIn/other
  value_original text not null, value_normalized text
  is_primary boolean default false

business_cards           -- 名片掃描紀錄
  contact_id → contacts on delete cascade
  exhibition_id → exhibitions
  image_path text not null
  image_hash text not null  UNIQUE        -- SHA-256，去重、避免重複呼叫 AI
  raw_ocr_text text, recognition_json jsonb, detected_languages text[]
  ai_model text
  recognition_status text default 'pending' check in ('pending','processing','done','failed')
  recognition_error text
  token_usage int, estimated_cost numeric  -- 之後做 AI 費用統計
  uploaded_by → profiles

event_contacts           -- 展覽 × 聯絡人（同一人不同展覽疊加不覆蓋）
  exhibition_id → exhibitions
  contact_id → contacts on delete cascade
  interested_products text[], onsite_notes, next_action
  scanned_by → profiles
  UNIQUE (exhibition_id, contact_id)

interactions             -- 聯繫紀錄
  contact_id → contacts on delete cascade
  exhibition_id → exhibitions
  interaction_type text, interaction_date date not null
  content, customer_needs, next_action text
  next_follow_up_date date, created_by → profiles

tasks                    -- 待辦事項
  contact_id → contacts on delete cascade
  exhibition_id → exhibitions
  title text not null, description text, due_date date
  status text default '待處理' check in ('待處理','進行中','已完成')
  assigned_to, created_by → profiles

products                 -- 感興趣產品清單（前端可增修）
  name text not null unique, sort_order int, active boolean default true
  -- 初始：SUT BOX / POLICE BOX / AI Military Training / UAV Training /
  --       USV Training / CQB Training / Firearms Training /
  --       Disaster Prevention Training / XR Training Solution / 其他

public_lead_submissions  -- 客戶自填表單暫存（表已建，畫面尚未做）
  exhibition_id, name, company, title, contact_info, needs_note, language
  status text default '待處理' check in ('待處理','已轉入名單')
  converted_contact_id → contacts on delete set null

contacts_with_score      -- view（security_invoker = true）
  select c.*, 身份權重 × 部門相關度 × (積極度+成交機率) / 2.0 as contact_score
```

### 2.3 Storage
| bucket | 用途 | 公開 |
|---|---|---|
| `photos` | 名片圖片、客戶頭像 | 否 |

```
photos/contacts/{聯絡人id}/avatar.webp
photos/business_cards/{活動名稱}/{單位名稱}/{姓名}_{公司名}_{短雜湊8碼}.webp
```

## 3. 權限（RLS）例外
一般表依共用規則 §8。例外：
| 表 | 規則 |
|---|---|
| `identity_weights` | select 所有登入者；寫入僅 admin |
| `public_lead_submissions` | insert **to public**（免登入）；select/update 僅 admin/editor |

前端：`admin` 才看得到「使用者管理」「身份權重設定」「產品管理」。

## 4. 業務規則

### 4.1 聯絡人價值分數
```
分數 = 身份權重 × 部門相關度 × (積極度 + 成交機率感覺) ÷ 2
```
- 用 **view 即時計算**，不存固定值 → 權重表改了立即反映。
- 三個評分欄位任一為空 → 分數顯示「—」。

### 4.2 名片辨識（Gemini，Edge Function `card-ocr`）
- **API 金鑰絕不進前端**；只有 admin/editor 能呼叫（會產生費用）。
- 用 `responseSchema` 強制結構化 JSON 輸出。
- **多語系原則**：`*_original` 一律填名片上印刷的原文、不翻譯；只有名片上真的有英文才填 `*_english`，不自行生成翻譯。
- 同一張名片（SHA-256 相同）重複掃描 → 沿用既有結果，不重複呼叫 API。
- **先辨識再上傳**：辨識完才知道姓名與公司，檔案才能用看得懂的路徑歸檔。
- 辨識到的公司找不到 → **自動建立公司**（忽略大小寫與前後空白比對）。
- 使用者之後改了姓名／公司／來源展覽 → 存檔時把 Storage 檔案搬到正確路徑。
- Gemini 回 `429` 且 `limit: 0` 不是用完額度，而是該 model 在專案沒有免費額度 → 準備候選 model 清單依序 fallback（遇 429/404 換下一個），另支援 `GEMINI_MODEL` secret 指定。
- 名片檔名不可用純 SHA-256（Storage 會全是亂碼）。

### 4.3 多語系與 RTL
- 姓名、公司、部門、職稱、地址都是「原文 + 英文」兩欄。
- 原文欄位加 `class="rtl-aware"`，偵測到希伯來文／阿拉伯文自動加 `dir="rtl"`：
```js
var RTL_REGEX = /[֐-׿؀-ۿݐ-ݿࢠ-ࣿיִ-﷿ﹰ-﻿]/;
```
- **一定用 `\uXXXX` escape，不直接貼 Unicode 字元。**

### 4.4 一人多重身分
同一人可同時是 A 公司總經理、B 公司總裁、C 公司共同創辦人、扶輪社社長。
- 每段身分各自有職稱、部門、負責項目 → `contact_affiliations`。
- `is_primary` 那段顯示在名單列表，其餘以「＋N」表示。
- **社團（扶輪社、獅子會）是 `company_type='社團組織'` 的單位，不要塞備註**（否則無法反查「我們認識哪些扶輪社的人」）。
- 依公司類型篩選 → **任一段身分符合就算符合**。
- 公司成員清單顯示的職稱，是這個人**在那個單位**的職稱。

## 5. 前端畫面
```
登入後
└─ 🏠 總覽：聯絡人總數／本月新增／已成交／待處理待辦
   └─ 名片辨識／公司管理／聯絡人／產品管理／身份權重
   └─ 使用者管理（admin）
```
客戶自填表單（免登入）之後要做成**獨立公開頁面**，不與內部工具同頁。

## 6. 部署
共用步驟見 [../COMMON_DEV_RULES.md](../COMMON_DEV_RULES.md) §10。CRM 專屬：
1. Storage 建 `photos` bucket（Public 關閉）。
2. 部署 Edge Function `card-ocr`，設定 secret `GEMINI_API_KEY`（申請：https://aistudio.google.com/apikey，選 Create API key in new project）；可選 `GEMINI_MODEL`。

## 7. 尚未完成（下一階段）
| 項目 | 說明 |
|---|---|
| **展場即時錄音** | 2027 行銷策略規劃：業務在展場邊接待邊錄音，接待不中斷、每位客戶都有紀錄，展後再統一分析與辨識；保留名片辨識。資料結構與儲存方式待設計（需先說明設計方向） |
| **離線掃描佇列** | 展場沒網路時先存 IndexedDB，有網路再同步；SHA-256 去重、失敗重試上限 |
| **重複聯絡人偵測** | 同一人被不同人各建一筆 |
| **客戶自填表單** | 公開頁面、免登入、中英雙語，寫進 `public_lead_submissions`（表與 RLS 已就緒） |
| **草稿暫存** | 表單填到一半先存本機 |
| **CRM 匯出** | 名單匯出 |
| **分析儀表板擴充** | CRM ROI 比較，用 `event_contacts` + `contacts_with_score` |
| **AI 費用控管** | `token_usage` / `estimated_cost` 已預留，尚未做統計與用量上限 |
| **展覽主檔與財務系統的對應** | 財務已獨立，兩邊展覽清單是否同步、如何對應（名稱或匯出匯入）待決 |
