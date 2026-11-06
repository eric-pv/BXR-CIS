# Aviation Slides — 乾淨的 PPTX 解壓工具

這個資料夾提供 Windows PowerShell 腳本，供 Claude Code 與公司開發人員將 Git LFS 中的 `Aviation Slides.zip` 拆出 **249 份原生 PPTX 工作檔**。

## 為什麼不是整包解開？

壓縮檔除了 249 份真正可用的 PPTX，還有 249 個同名的 macOS `._` 附屬檔，以及字體說明 PDF、macOS 的 `._` 資源附屬檔和系統檔。Claude 的核心需求是原生、可編輯的 PPTX，所以工作庫先保留 PPTX，其餘仍存在**不可覆蓋的原始 ZIP**。

## 在 Windows 執行

在 Repository 根目錄的 PowerShell：

```powershell
git lfs pull
powershell -ExecutionPolicy Bypass -File .\presentation-skill\scripts\extract-aviation.ps1
```

腳本不會自動提交或推送；會產生：

- `presentation-skill/source-library/aviation-extracted/`：分類保留原路徑的原生 PPTX。
- `presentation-skill/catalog/aviation-extracted-files.csv`：PPTX 來源名稱、原相對路徑與大小。

上傳前先檢查檔案數與 Git LFS：

```powershell
(Get-ChildItem .\presentation-skill\source-library\aviation-extracted -Recurse -Filter *.pptx -File).Count
git add presentation-skill/catalog/aviation-extracted-files.csv
git add presentation-skill/source-library/aviation-extracted
git lfs ls-files
```

**注意：不要在未確認公開散布授權的情況下，把解壓後的商用原始 PPTX 推送到目前 Public Repository。** 可以先只在本機使用；若後續要共享原檔，先改成 Private 或使用單獨的 Private 素材庫。Git LFS 有儲存與流量配額，249 份額外上傳會增加使用量。

Claude Code 未來可直接依 manifest 分析原始 PPTX，並把經核准的 BXR 版型存到另一個資料夾。不得直接修改來源版型。
