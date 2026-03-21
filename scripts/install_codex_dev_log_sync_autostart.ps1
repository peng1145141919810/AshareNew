$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$startScript = Join-Path $PSScriptRoot "start_codex_dev_log_sync.ps1"
$taskName = "Ashare Codex Dev Log Mirror"
$taskCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$startScript`""

schtasks.exe /Create /TN $taskName /SC ONLOGON /DELAY 0002:00 /RL LIMITED /F /TR $taskCommand | Out-Null

Write-Output "Installed logon autostart task: $taskName"
Write-Output "Command: $taskCommand"
Write-Output "Behavior: starts 2 minutes after logon, runs a hidden PowerShell launcher, then starts the watcher with low-priority polling."
