param(
    [string]$SourceRoot = "F:\quant_data\AshareC#\csharp_runtime_skeleton",
    [string]$TargetRoot = "F:\quant_data\AshareCSharp-runtime-skeleton"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SourceRoot)) {
    throw "Source skeleton root not found: $SourceRoot"
}

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

$arguments = @(
    $SourceRoot,
    $TargetRoot,
    '/MIR',
    '/XD', 'bin', 'obj', '.git', '.idea', '.vs',
    '/R:1',
    '/W:1',
    '/NFL',
    '/NDL',
    '/NP'
)

& robocopy @arguments | Out-Null
$exitCode = $LASTEXITCODE
if ($exitCode -ge 8) {
    throw "Robocopy failed with exit code $exitCode."
}

Write-Output "Exported C# runtime skeleton to: $TargetRoot"
