param(
    [string]$SourceRoot = "F:\quant_data\Ashare\data",
    [string]$TargetRoot = "F:\quant_data\AshareC#\data"
)

$ErrorActionPreference = "Stop"

function Copy-Tree {
    param(
        [string]$Source,
        [string]$Target
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        return $false
    }

    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    Copy-Item -LiteralPath (Join-Path $Source "*") -Destination $Target -Recurse -Force -ErrorAction Stop
    return $true
}

$items = @(
    @{ Rel = "trade_clock"; Category = "clock_safety_runtime"; Notes = "trade clock heartbeat, safety, runtime" },
    @{ Rel = "trade_release_v1"; Category = "release_contract"; Notes = "release pointer/manifests/targets" },
    @{ Rel = "live_execution_bridge\oms_v1"; Category = "oms_truth"; Notes = "OMS summary, actual-state and ledgers" },
    @{ Rel = "live_execution_bridge\portfolio_control_runs"; Category = "execution_audit"; Notes = "portfolio control audits" },
    @{ Rel = "live_execution_bridge\execution_reports"; Category = "execution_reports"; Notes = "execution report history" },
    @{ Rel = "portfolio_recommendation_v6"; Category = "desired_state_source"; Notes = "desired-state source artifacts" },
    @{ Rel = "event_lake_v6\research\supervisor"; Category = "supervisor_state"; Notes = "supervisor runtime state" },
    @{ Rel = "daily_cache_v6"; Category = "market_cache"; Notes = "automation basic market cache" }
)

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

$copiedAt = (Get-Date).ToString("o")
$manifest = @()

foreach ($item in $items) {
    $sourcePath = Join-Path $SourceRoot $item.Rel
    $targetPath = Join-Path $TargetRoot $item.Rel
    $ok = Copy-Tree -Source $sourcePath -Target $targetPath
    $manifest += [ordered]@{
        source_path = $sourcePath
        target_path = $targetPath
        category = $item.Category
        copied_at = $copiedAt
        exists_after_copy = (Test-Path -LiteralPath $targetPath)
        notes = $item.Notes
        copied = $ok
    }
}

$manifestPath = Join-Path $TargetRoot "migration_manifest.json"
$doc = [ordered]@{
    copied_at = $copiedAt
    source_root = $SourceRoot
    target_root = $TargetRoot
    entries = $manifest
}
$doc | ConvertTo-Json -Depth 6 | Set-Content -Path $manifestPath -Encoding UTF8

Write-Host "Migration manifest written:" $manifestPath
