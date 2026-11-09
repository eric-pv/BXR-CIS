# AUTORUN HIGH A — Aviation layout families

HIGH_A=DONE
Updated: 2026-11-09 (UTC)
（A1–A4 全部完成：Eric 同意修改 select-layout.py／registry 後 CI 全綠，Codex review 指出的 body 遺失問題已修正，squash merge 到 main。）

| Item | Status | Notes |
|---|---|---|
| A0 前置（LFS、字型） | DONE | `git lfs pull` 取得 Aviation Slides.zip；fonts-noto-cjk（apt）；B612 Mono（jsDelivr google/fonts）；fontconfig 別名 Noto Sans TC/JP/SC → Noto Sans CJK TC/JP/SC |
| A1 解壓與縮圖 | DONE | 安全解壓到 /tmp/bxr-a/src（略過 __MACOSX、`._*`，檢查路徑穿越與 symlink）：500 檔，249 份 PPTX，編號 D001–D249（依路徑排序，與 catalog 的 AVI-<deck> 編號一致）。分批渲染，每批 20 份：已完成到第 249 份。LibreOffice 轉檔 249/249 成功（每份 timeout 180s、失敗重試 1 次）。D248 的 pdftoppm 縮圖第一次逾時（300s），重試（900s）後成功。共 5,164 頁。總覽圖在 /tmp/bxr-a/sheets（未提交） |
| A2 layouts_aviation.py | DONE | 7 家族、19 個 variant（下表） |
| A3 tests/test_aviation_layouts.py + 樣張 | DONE | 6 項測試通過；55 張樣張渲染到 /tmp/bxr-a/review。看總覽圖後做了一輪修正：B612 Mono 字寬估算、少項目時垂直置中與限制行高、gauge 中心數字避開弧線、年份不換行 |
| A4 合併 main、測試、PR、merge | DONE | 已合併 origin/main；Eric 同意後修正 select-layout.py 並重新產生 registry（36 layouts）；修正 Codex P2（dense 版型不再省略 body，測試新增 body／compare value 檢查）；CI verify-assets 全綠；PR https://github.com/eric-pv/BXR-CIS/pull/23 squash merge |

## 新增版型
| variant | family | n | ref |
|---|---|---|---|
| `compare.table` | compare | 2–8 | AVI-064-0018, AVI-064-0019, AVI-063-0014 |
| `compare.split-panels` | compare | 2–6 | AVI-064-0012, AVI-063-0008, AVI-064-0007 |
| `compare.center-axis` | compare | 2–6 | AVI-064-0017, AVI-064-0011, AVI-064-0014 |
| `timeline.horizontal` | timeline | 3–8 | AVI-224-0005, AVI-224-0017, AVI-155-0010 |
| `timeline.alternating` | timeline | 4–8 | AVI-224-0013, AVI-224-0015, AVI-155-0013 |
| `timeline.vertical-visual` | timeline | 3–6 | AVI-224-0014, AVI-224-0020, AVI-155-0008 |
| `map.visual-markers` | map | 1–6 | AVI-019-0004, AVI-249-0008, AVI-019-0012 |
| `map.region-cards` | map | 1–6 | AVI-019-0017, AVI-019-0011, AVI-019-0007 |
| `team.cards` | team | 2–6 | AVI-215-0015, AVI-215-0020, AVI-215-0003 |
| `team.lead-tree` | team | 3–6 | AVI-215-0019, AVI-215-0004, AVI-215-0006 |
| `team.side-visual` | team | 2–6 | AVI-215-0013, AVI-215-0005, AVI-215-0016 |
| `product.visual-left` | product | 2–6 | AVI-161-0001, AVI-161-0012, AVI-161-0020 |
| `product.visual-top` | product | 2–4 | AVI-161-0010, AVI-161-0018, AVI-161-0011 |
| `product.spotlight` | product | 2–6 | AVI-161-0004, AVI-161-0016, AVI-081-0009 |
| `gauge.dials` | gauge | 1–4 | AVI-135-0017, AVI-135-0014, AVI-135-0018 |
| `gauge.rings` | gauge | 1–4 | AVI-135-0003, AVI-081-0007, AVI-063-0018 |
| `gauge.bars` | gauge | 1–4 | AVI-064-0007, AVI-063-0012, AVI-064-0003 |
| `quote.panel` | quote | 1–2 | AVI-242-0010, AVI-242-0006 |
| `quote.visual-side` | quote | 1–2 | AVI-242-0015, AVI-242-0017, AVI-242-0011 |

ref 使用 catalog/generated/source-slides.csv 的 slide_id（`AVI-<deck>-<page>`，例如 AVI-064-0018 = deck 064 第 18 頁）。55 個 ref 全部存在於 catalog 中。

## 測試結果（合併 main 後，本機）
- test_contracts.py：failures=0
- preflight.py：PASS
- test_master.py：8 OK
- test_pipeline.py：8 OK
- test_acceptance.py：6 OK
- test_aviation_layouts.py：6 OK（新）
- test_catalog.py：套用修正前 FAILED；Eric 同意後套用 select-layout.py 修正並重新產生 registry（36 layouts），23 OK（1 skip）

註：CI workflow（presentation-preflight.yml）沒有執行 test_aviation_layouts.py；workflow 不在允許修改範圍，建議日後加入。

## 阻擋問題
1. **（已解決：Eric 同意後已提交修正）** test_catalog.py 與允許修改範圍衝突。 main（#22）新增的 `scripts/select-layout.py` 會掃描 `bxr_deck.layouts_aviation`，但 `record()` 用 `f"PMLD-{p:04d}"` 格式化 ref，遇到 `AVI-...` 字串 ref 就丟出 ValueError；另外 `catalog/layout-registry.json` 必須與 variant 同步。兩者都不在本任務允許修改的檔案內（只能改 layouts_aviation.py、test_aviation_layouts.py 與本進度檔），所以 CI 不會全綠，依授權條件**不 merge**。
   修正方式：在本機套用下列 patch，再執行 `python presentation-skill/scripts/select-layout.py --write-registry`（registry 會變成 36 個 layout），之後 test_catalog.py 23 項通過（1 skip）。此修正未提交，留給 Eric 或後續任務決定。
```diff
diff --git a/presentation-skill/scripts/select-layout.py b/presentation-skill/scripts/select-layout.py
index bdf889e..b6ed8b2 100644
--- a/presentation-skill/scripts/select-layout.py
+++ b/presentation-skill/scripts/select-layout.py
@@ -27,6 +27,7 @@ TRANSITIONS = {"source-candidate": ["claude-reviewed"], "claude-reviewed": ["cis
 SELECTABLE = ("claude-reviewed", "cis-approved")
 VARIANT_MODULES = ["bxr_deck.layouts", "bxr_deck.layouts_aviation"]   # the second is scanned only if present
 REF_SOURCE = "presentation-skill/source-library/500頁.pptx"
+AVI_SOURCE = "presentation-skill/source-library/Aviation Slides.zip"
 
 FAMILY_WORDS = {
     "agenda": ["agenda", "contents", "outline", "目錄", "大綱", "議程", "アジェンダ", "目次"],
@@ -56,11 +57,12 @@ def scan_variants():
 
 def record(v, previous=None):
     ref = v["ref"]
+    avi = bool(ref) and isinstance(ref[0], str)          # aviation refs are catalog slide_ids ("AVI-064-0018")
     rec = {
         # --- fields required by catalog/layouts.schema.json (kept compatible)
         "id": v["variant"],
-        "source_file": REF_SOURCE if ref else "presentation-skill/bxr_deck/compose.py",
-        "source_slide": ref[0] if ref else 1,
+        "source_file": (AVI_SOURCE if avi else REF_SOURCE) if ref else "presentation-skill/bxr_deck/compose.py",
+        "source_slide": (int(ref[0].rsplit("-", 1)[1]) if avi else ref[0]) if ref else 1,
         "category": v["family"],
         "tags": [v["family"], v["prefers"]] if v["prefers"] else [v["family"]],
         "editable": True,
@@ -75,7 +77,7 @@ def record(v, previous=None):
         "status": "claude-reviewed",
         "origin": "reference-distilled" if ref else "native",
         "ref_pages": ref,
-        "ref_slides": [f"PMLD-{p:04d}" for p in ref],
+        "ref_slides": [p if isinstance(p, str) else f"PMLD-{p:04d}" for p in ref],
         "items_min": v["nmin"],
         "items_max": v["nmax"],
         "needs_image": v["needs_image"],
```
2. `07_Templates/*.pptx` 顯示為已修改：這是 Git LFS 設定的老問題。依指示不提交、不修改、不還原；Eric 已說明它們只是參考，skill 由 `bxr_deck/master.py` 自行產生母片，不依賴這兩個檔案。
3. Repo 為 PUBLIC 且含第三方商業素材：公開散布與多人使用的授權需 Eric 確認；本任務沒有提交任何新的商業素材、縮圖或解壓檔。

## 設計判斷（保守、依 CIS v3.2）
- map：不重用任何商業地圖向量或像素，改用核准的地形／城市主視覺，加上可拖曳的編號標記（名稱為 "Region N marker (move to location)"）和對應圖例。
- team：不用人像，以 BXR 官方 icon 表示職能；name=None 時只顯示角色，不虛構人名。
- 紅色只用在單一焦點（產品名稱標記、引言重點線、最後一個里程碑），其餘使用 Black／Graphite／Paper 與 sector accent。
- gauge 只顯示 brief 提供的 value／max，max ≤ 0 時比例視為 0。
