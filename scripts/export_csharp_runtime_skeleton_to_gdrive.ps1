param(
    [string]$SourceRoot = "F:\quant_data\AshareCSharp-runtime-skeleton",
    [string]$BackupRoot = "G:\我的云端硬盘\AshareCSharp_backups\runtime_skeleton_versions",
    [string]$Label = "bootstrap_runtime_skeleton"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $SourceRoot)) {
    throw "Source skeleton repository not found: $SourceRoot"
}

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

$dateStamp = Get-Date -Format "yyyyMMdd"
$existing = Get-ChildItem -Path $BackupRoot -Directory -Filter ("SKELETON-{0}-R*" -f $dateStamp) -ErrorAction SilentlyContinue |
    Sort-Object Name
$nextRevision = if ($existing) { $existing.Count + 1 } else { 1 }
$versionId = "SKELETON-{0}-R{1}" -f $dateStamp, $nextRevision.ToString("000")
$targetRoot = Join-Path $BackupRoot $versionId

New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null

$arguments = @(
    $SourceRoot,
    $targetRoot,
    "/MIR",
    "/XD", "bin", "obj", ".git", ".idea", ".vs",
    "/R:1",
    "/W:1",
    "/NFL",
    "/NDL",
    "/NP"
)

& robocopy @arguments | Out-Null
$exitCode = $LASTEXITCODE
if ($exitCode -ge 8) {
    throw "Robocopy failed with exit code $exitCode."
}

$manifest = [PSCustomObject]@{
    version_id = $versionId
    label = $Label
    created_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
    source_root = $SourceRoot
    target_root = $targetRoot
}

$manifest | ConvertTo-Json | Set-Content -Path (Join-Path $targetRoot "snapshot_manifest.json") -Encoding UTF8

$catalogPath = Join-Path $BackupRoot "VERSION_CATALOG.md"
if (-not (Test-Path $catalogPath)) {
    @(
        "# Runtime Skeleton Version Catalog",
        "",
        "| Version | Created | Label | Source | Target |",
        "| --- | --- | --- | --- | --- |"
    ) | Set-Content -Path $catalogPath -Encoding UTF8
}

$catalogLine = "| {0} | {1} | {2} | `{3}` | `{4}` |" -f `
    $versionId, `
    $manifest.created_at, `
    $Label, `
    $SourceRoot, `
    $targetRoot

Add-Content -Path $catalogPath -Value $catalogLine -Encoding UTF8

Write-Output ("Exported runtime skeleton to Google Drive: {0}" -f $targetRoot)
Write-Output ("Version ID: {0}" -f $versionId)
