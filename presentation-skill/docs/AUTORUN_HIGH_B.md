# AUTORUN — HIGH B（內容觸發與整合）

HIGH_B=IN-PROGRESS
最後更新：2026-11-09T11:40Z
分支：claude/affectionate-wright-80u02w（系統指定）

| 項目 | 狀態 | 備註 |
|---|---|---|
| B1 planner 觸發規則 + generator 保護式匯入／退回 | IN-PROGRESS | |
| B2 fixture + tests/test_aviation_planner.py + PR | TODO | |
| B3 整合驗收（需 main 已含 layouts_aviation.py） | TODO | |
| B4 收尾 | TODO | |

## 已知問題
- `07_Templates/BXR_Presentation_Template_v3.1.pptx`、`v3.2.pptx` 在工作樹顯示為已修改：這兩個檔案以一般 blob 提交，但 `.gitattributes` 把 `*.pptx` 設為 LFS，clean filter 造成假性差異。檔案內容與提交版本同大小（849,784／2,756,488 bytes）。依指示不提交、不修改、不還原。

## 基準
- 開工前（main @ 1362d7d）既有測試：test_contracts、test_master、test_pipeline、test_acceptance、test_catalog 全數通過。
- 既有 6 份 fixture 的 planner 選版快照：/tmp/bxr-b/baseline_kinds.json（不提交）。新規則不得改變這些結果。
