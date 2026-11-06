#requires -Version 5.1
<#
.SYNOPSIS
  Extract only editable PPTX files from Aviation Slides.zip.
.DESCRIPTION
  Preserves original ZIP; excludes Mac resource forks, PDFs and other files.
  Produces files under presentation-skill/source-library/aviation-extracted
  plus a CSV index under presentation-skill/catalog.
  Does not git add, commit, push, or alter repository visibility.
#>
param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zipPath = Join-Path $RepoRoot 'presentation-skill\source-library\Aviation Slides.zip'
$outRoot = Join-Path $RepoRoot 'presentation-skill\source-library\aviation-extracted'
$catalogDir = Join-Path $RepoRoot 'presentation-skill\catalog'
$manifestPath = Join-Path $catalogDir 'aviation-extracted-files.csv'
if (-not (Test-Path -LiteralPath $zipPath)) { throw "ZIP not found: $zipPath. Run git lfs pull if needed." }
if ((Get-Item -LiteralPath $zipPath).Length -lt 1048576) { throw "The ZIP appears to be a Git LFS pointer. Run git lfs pull first." }
[void](New-Item -ItemType Directory -Force -Path $outRoot)
[void](New-Item -ItemType Directory -Force -Path $catalogDir)
$rootFull = [IO.Path]::GetFullPath($outRoot).TrimEnd('\') + '\'
$rows = New-Object System.Collections.Generic.List[object]
$zip = [IO.Compression.ZipFile]::OpenRead($zipPath)
try {
  foreach ($entry in $zip.Entries) {
    $path = $entry.FullName.Replace('\','/')
    if (-not $path.EndsWith('.pptx', [StringComparison]::OrdinalIgnoreCase)) { continue }
    if ($path.StartsWith('__MACOSX/') -or $path.StartsWith('._') -or $path -match '/\._') { continue }
    $relative = $path
    if ($relative.StartsWith('Aviation Slides/')) { $relative = $relative.Substring('Aviation Slides/'.Length) }
    $parts = $relative.Split('/')
    if ($parts | Where-Object { $_ -eq '..' -or $_ -eq '.' }) { throw "Invalid ZIP path: $path" }
    $dest = [IO.Path]::GetFullPath((Join-Path $outRoot ($relative.Replace('/','\'))))
    if (-not $dest.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe ZIP entry: $path" }
    $parent = Split-Path -Parent $dest
    [void](New-Item -ItemType Directory -Force -Path $parent)
    if (-not (Test-Path -LiteralPath $dest) -or (Get-Item -LiteralPath $dest).Length -ne $entry.Length) {
      [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$dest,$true)
    }
    $rows.Add([pscustomobject]@{
      source_archive = 'Aviation Slides.zip'
      zip_entry = $path
      relative_pptx_path = $relative
      size_bytes = $entry.Length
      status = 'extracted'
    })
  }
} finally { $zip.Dispose() }
$rows | Sort-Object relative_pptx_path | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8
Write-Host ("Extracted {0} PPTX files into: {1}" -f $rows.Count,$outRoot)
Write-Host ("Manifest: {0}" -f $manifestPath)
Write-Host 'No Git commit or push has been performed.'
