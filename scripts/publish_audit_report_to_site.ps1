param(
    [string]$ReportDir = "",
    [string]$RemoteUser = "ubuntu",
    [string]$RemoteHost = "43.129.28.141",
    [string]$RemoteRoot = "/var/www/peng1145141919810.xyz/site",
    [string]$Domain = "peng1145141919810.xyz"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = "C:\Users\Administrator\PyCharmMiscProject\.venv\Scripts\python.exe"
$automationRoot = Join-Path $repoRoot "outputs\automation_runs"
$publishStage = Join-Path $repoRoot "outputs\site_publish_stage"
$reportsStage = Join-Path $publishStage "reports"

if (-not (Test-Path $automationRoot)) {
    throw "Automation runs root not found: $automationRoot"
}

if ([string]::IsNullOrWhiteSpace($ReportDir)) {
    $latest = Get-ChildItem -Path $automationRoot -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName "strategy_audit.html") } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        throw "No strategy_audit.html report directory found under $automationRoot"
    }
    $ReportDir = $latest.FullName
}

$resolvedReportDir = (Resolve-Path $ReportDir).Path
$reportName = Split-Path $resolvedReportDir -Leaf

New-Item -ItemType Directory -Force -Path $reportsStage | Out-Null
$stageReportDir = Join-Path $reportsStage $reportName
if (Test-Path $stageReportDir) {
    Remove-Item -Recurse -Force $stageReportDir
}
Copy-Item -Recurse -Force $resolvedReportDir $stageReportDir

& $pythonExe (Join-Path $PSScriptRoot "build_audit_site_index.py") `
    --reports-root $reportsStage `
    --output-dir $publishStage `
    --domain $Domain

Write-Host "Uploading report directory: $resolvedReportDir"
ssh "$RemoteUser@$RemoteHost" "mkdir -p $RemoteRoot/reports"
Push-Location $reportsStage
try {
    scp -r ".\$reportName" "$RemoteUser@$RemoteHost`:$RemoteRoot/reports/"
}
finally {
    Pop-Location
}

Push-Location $publishStage
try {
    Get-ChildItem -Path . -File -Filter *.html | ForEach-Object {
        scp $_.Name "$RemoteUser@$RemoteHost`:$RemoteRoot/$($_.Name)"
    }
}
finally {
    Pop-Location
}

Write-Host "Publish completed."
Write-Host "Report URL: https://$Domain/reports/$reportName/strategy_audit.html"
Write-Host "Index URL:  https://$Domain/"
