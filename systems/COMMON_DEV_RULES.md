# 共用開發規則（CRM 與活動花費紀錄都適用）

> 整理自《活動管理系統 — 開發規格書》§2、§3、§5、§8、§9。兩個系統是獨立的應用程式，但遵守同一套規則。

## 1. 技術架構

```
前端：單一 index.html（純 HTML/CSS/JS，無 build step）
      └─ GitHub Pages 發布
後端：Supabase
      ├─ Postgres（含 Row Level Security）
      ├─ Auth（Email + 密碼）
      ├─ Storage（私有 bucket）
      └─ Edge Functions（Deno）
```

外部依賴全部走 CDN，不裝 npm：`@supabase/supabase-js@2`（ESM via jsDelivr）、Chart.js（儀表板）。
系統各自的外部服務（Gemini、台銀匯率）寫在各自的規格。

### 為什麼不是 Google Apps Script
專案原本是 Google Sheet + Apps Script，因為以下問題整個換掉：`/dev` 與 `/exec` 網址容易搞混；CORS 要用 `text/plain` 繞過預檢請求；改權限後要重新部署「版本」才生效；「執行身分：使用者本人」會要求每個人都有 Sheet 的 Drive 權限（正解是「執行身分：我」，但整體模型仍太反直覺）。

### 為什麼是單一 HTML 檔
沒有 build step，GitHub Pages 直接發布；非技術同事也能理解「換掉這個檔案就是更新網站」。代價是檔案很大（3000+ 行），靠清楚的區塊註解維持可讀性。

## 2. 開發流程

1. **一次只做一批**，做完就 commit、開 PR、停下來回報，等使用者確認再繼續；不要一次全部做完才 commit。
2. 每個 PR 說明要包含：這批做了什麼、這批沒做（留到後面）、**需要人工操作**（要跑哪個 SQL、要設哪個 secret）。
3. 使用者說「merge 了」才繼續下一批（若使用者另有自動合併授權，依其指示）。
4. 大改動（例如資料結構重設計）先說明設計方向，確認後才動手。

## 3. 安全規則（絕對不能違反）

- `sb_publishable_...`（舊稱 anon key）→ 可以放在前端程式碼、可以 commit。
- `sb_secret_...`（等同 service role key）→ **絕對不可以**放進前端或 commit。使用者若誤貼 secret key：拒絕使用、請對方重新產生金鑰、改要 publishable key。
- DB 密碼、API 金鑰一律走環境變數／Supabase secrets。
- `.env` 必須在 `.gitignore`，永遠不 commit、不寫進任何文件。

## 4. 程式風格（index.html）

```js
// ✅ 這個專案的風格
var state = { exhibitions: [], contacts: [] };
function renderTable(){ ... }
state.contacts.filter(function(c){ return c.id === id; });
async function loadState(){ ... }          // async/await 可以用

// ❌ 不要用
const/let（頂層 Supabase 設定除外）、箭頭函式、class、JSX
```

- 所有邏輯包在一個 IIFE 裡，避免污染全域。
- **註解用繁體中文，寫「為什麼」不是「做什麼」**。好：`// 先 drop view 再建，因為 create or replace view 不允許改變欄位順序`；壞：`// 建立 view`。
- 函式宣告會 hoist，順序照邏輯分組即可。
- 區塊之間用 `// ---------------- 區塊名稱 ----------------` 分隔。

## 5. SQL migration 規則

- 檔名編號遞增：`01_`、`02_`…，放在各系統的 `supabase/sql/`（兩個系統各自編號）。
- **一律可重複執行**：`create table if not exists`；`alter table ... add column if not exists`；`drop policy if exists` 再 `create policy`；`insert ... on conflict do nothing`。
- 破壞性變更要在檔案開頭用註解明確標示，PR 也要寫。
- 每個檔案都能單獨執行，不依賴「上一個檔案剛跑完」的暫時狀態。

## 6. 交付前驗證（每次改完 index.html）

```bash
# 1. 抽出 <script type="module"> 內容做語法檢查
python3 -c "
import re
c = open('index.html', encoding='utf-8').read()
m = re.search(r'<script type=\"module\">(.*?)</script>', c, re.S)
open('/tmp/chk.mjs','w',encoding='utf-8').write(m.group(1))
" && node --check /tmp/chk.mjs

# 2. 交叉比對 getElementById 參照的 id 是否都存在於 HTML
#    （動態 innerHTML 產生的 id 是預期中的漏網之魚，要人工確認）
```

## 7. Git / PR

- 前一個 PR merge 後，從最新 `origin/main` 重開分支，再 cherry-pick 未合併的 commit。
- commit message 用繁體中文：第一行簡述，空行後說明「為什麼這樣改」。

## 8. 權限設計（RLS）共通原則

- 角色：`admin`、`editor`、`viewer`（各系統的 `profiles.role`）。
- 一般業務表：`select` 所有登入者 `using (true)`；`insert / update / delete` 限 `get_my_role() in ('admin','editor')`。
- `profiles`：select 所有登入者；update/delete 僅 admin。
- Storage objects：select 所有登入者；寫入 admin/editor。
- 前端：`viewer` 隱藏所有表單與新增／編輯／刪除按鈕；`admin` 才看得到使用者管理等設定。**前端隱藏只是體驗，真正擋住寫入的是 RLS。**
- **⚠️ View 一定要加 `with (security_invoker = true)`**，否則 view 用建立者權限執行，繞過查詢者的 RLS。

```sql
create or replace function get_my_role() returns text as $$
  select role from public.profiles where id = auth.uid();
$$ language sql stable security definer set search_path = public;
```

自動建 profile 的 trigger：`handle_new_user()`（security definer），在 `auth.users` insert 後自動在 `profiles` 建一筆 `role='viewer'`。

## 9. 踩過的坑（務必先讀）

### SQL / Postgres
| 症狀 | 原因 | 解法 |
|---|---|---|
| `42P16: cannot change name of view column` | 底層 table 加欄位後 `select c.*` 展開順序變了，`create or replace view` 不允許改變既有欄位位置或名稱 | **先 `drop view` 再建** |
| `cannot drop column ... because other objects depend on it` | view 依賴那個欄位 | 先 drop view → 改欄位 → 重建 view |
| 明明執行成功，欄位卻沒出現 | **Supabase SQL Editor 把整個分頁當成一個 transaction**，任一行報錯就整批回滾 | **每次開乾淨的新分頁，一次只貼一個 migration** |
| `Could not find the table 'public.xxx' in the schema cache` | PostgREST schema 快取沒跟上 | `NOTIFY pgrst, 'reload schema';` 等 5–10 秒 |
| Table Editor 側邊欄看不到新表 | 後台前端快取 | 用 `information_schema.tables` 確認；Ctrl+Shift+R |

### 前端 / PWA
| 症狀 | 原因 | 解法 |
|---|---|---|
| 更新後使用者還是看到舊版 | Service Worker 用 cache-first | 改成 network-first |
| 改成 network-first 還是舊版 | `fetch()` 仍被瀏覽器 HTTP 快取攔下（與 SW Cache API 是兩層） | `new Request(req, { cache: 'no-store' })` |
| 表單填到一半下拉選單被清空 | `fillSelect()` 重建 options 沒保留選取值 | 重建前記 `sel.value`，重建後還原 |
| 展開列排版跑掉 | `colspan` 與表頭欄位數不一致 | 改欄位時同步改 `colspan` |

### Edge Functions
| 症狀 | 原因 | 解法 |
|---|---|---|
| 在後台貼上部署失敗 | 網頁版編輯器只有一個 `index.ts`，`import '../_shared/cors.ts'` 找不到 | 想用後台部署就寫成**單一檔案**，CORS 設定內嵌 |

### 工具使用
- 用 `Edit` 工具改含 Unicode 字元的行容易比對失敗 → 用 Python 依行號整行取代。
- Python `re.sub()` 替換字串裡 `\u` 會被當跳脫字元 → 用 raw string 或整行取代。
- RTL 等 Unicode 範圍一律寫 `\uXXXX` escape，不直接貼字元。

## 10. 部署共通步驟

1. 建立 Supabase 專案，複製 **Project URL** 與 **publishable key** 填進該系統的 `index.html`。
2. SQL Editor 依序執行該系統的 migration（**一次一個乾淨分頁**）。
3. Authentication → Users 手動建立帳號（自動建 profiles，預設 viewer），再執行設定角色的 SQL。
4. Storage bucket **Public 保持關閉**。
5. 部署該系統的 Edge Functions 並設定 secrets（後台部署時 Function name 欄位在右下角，Secrets 在左側選單）。
6. GitHub Pages：Settings → Pages → Deploy from branch → `main` / `(root)`（或該系統所在資料夾）。
