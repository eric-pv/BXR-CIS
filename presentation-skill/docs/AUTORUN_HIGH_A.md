# AUTORUN HIGH A — Aviation layout families

HIGH_A=IN-PROGRESS
Updated: 2026-11-09 (UTC)

| Item | Status | Notes |
|---|---|---|
| A0 前置（LFS、字型） | DONE | git lfs pull Aviation Slides.zip；fonts-noto-cjk（apt）；B612 Mono（jsDelivr google/fonts）；fontconfig 別名 Noto Sans TC/JP/SC → Noto Sans CJK TC/JP/SC |
| A1 解壓與縮圖 | IN-PROGRESS | 249 份 PPTX（編號 D001–D249，依路徑排序）；渲染進度：已完成到第 180 份 |
| A2 layouts_aviation.py | TODO | |
| A3 tests/test_aviation_layouts.py + 樣張 | TODO | |
| A4 合併 main、測試、PR、merge | TODO | |

## 已知問題
- `07_Templates/*.pptx` 顯示為已修改：Git LFS 設定的老問題。依指示不提交、不修改、不還原。
