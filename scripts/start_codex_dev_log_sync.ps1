$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $PSScriptRoot "sync_codex_dev_log_to_gdrive.py"
$mirrorDir = "H:\我的云端硬盘\AshareCSharp_backups\codex_dev_log_mirror"
$pollSeconds = 5

function Resolve-PythonLaunch {
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    $venvPythonw = Join-Path $repoRoot ".venv\Scripts\pythonw.exe"
    if (Test-Path $venvPython) {
        return @{
            FilePath = $venvPython
            Arguments = @()
        }
    }
    if (Test-Path $venvPythonw) {
        return @{
            FilePath = $venvPythonw
            Arguments = @()
        }
    }
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return @{
            FilePath = $pythonCmd.Source
            Arguments = @()
        }
    }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        return @{
            FilePath = $pyCmd.Source
            Arguments = @("-3")
        }
    }
    throw "No usable Python launcher found. Expected .venv\Scripts\python.exe, PATH python, or py launcher."
}

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

$launch = Resolve-PythonLaunch

$args = @(
    $launch.Arguments
    $scriptPath
    "--mirror-dir"
    $mirrorDir
    "--poll-seconds"
    $pollSeconds
)

Start-Process -FilePath $launch.FilePath -ArgumentList $args -WorkingDirectory $repoRoot -WindowStyle Hidden | Out-Null
Write-Output "Started CODEX_DEV_LOG Google Drive sync watcher."
Write-Output "Mirror directory: $mirrorDir"
