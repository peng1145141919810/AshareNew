$ErrorActionPreference = "Stop"

$taskName = "AshareCSharp Codex Dev Log Mirror"
$null = schtasks.exe /Delete /TN $taskName /F 2>$null
Write-Output "Removed logon autostart task: $taskName"
