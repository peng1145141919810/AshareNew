$ErrorActionPreference = "Stop"

$watchers = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -eq "python.exe" -or $_.Name -eq "pythonw.exe") -and $_.CommandLine -like "*sync_codex_dev_log_to_gdrive.py*"
}

if (-not $watchers) {
    Write-Output "No running CODEX_DEV_LOG sync watcher was found."
    exit 0
}

$stopped = @()
foreach ($watcher in $watchers) {
    Stop-Process -Id $watcher.ProcessId -Force
    $stopped += $watcher.ProcessId
}

Write-Output ("Stopped CODEX_DEV_LOG Google Drive sync watcher(s): " + ($stopped -join ", "))
