$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$pythonw = Join-Path $repoRoot ".venv\Scripts\pythonw.exe"
$scriptPath = Join-Path $PSScriptRoot "sync_codex_dev_log_to_gdrive.py"
$mirrorDir = "G:\我的云端硬盘\Ashare_backups\codex_dev_log_mirror"
$pollSeconds = 5

function Get-WatcherProcesses {
    Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -eq "python.exe" -or $_.Name -eq "pythonw.exe") -and $_.CommandLine -like "*sync_codex_dev_log_to_gdrive.py*"
    }
}

$existing = Get-WatcherProcesses
if ($existing) {
    Start-Sleep -Seconds 2
    $existing = Get-WatcherProcesses
}

if ($existing) {
    Write-Output "CODEX_DEV_LOG sync watcher is already running."
    $existing | Select-Object ProcessId, Name, CommandLine
    exit 0
}

if (Test-Path $python) {
    $pythonExecutable = $python
} elseif (Test-Path $pythonw) {
    $pythonExecutable = $pythonw
} else {
    throw "Python executable not found under $repoRoot\.venv\Scripts"
}

$args = @(
    $scriptPath,
    "--mirror-dir",
    $mirrorDir,
    "--poll-seconds",
    $pollSeconds
)

Start-Process -FilePath $pythonExecutable -ArgumentList $args -WorkingDirectory $repoRoot -WindowStyle Hidden | Out-Null
Write-Output "Started CODEX_DEV_LOG Google Drive sync watcher."
Write-Output "Mirror directory: $mirrorDir"
