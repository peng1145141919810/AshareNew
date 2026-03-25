$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $PSScriptRoot "create_gdrive_script_snapshot.py"

function Resolve-PythonLaunch {
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return @{
            FilePath = $venvPython
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
    throw "No usable Python launcher found. Expected .venv\\Scripts\\python.exe, PATH python, or py launcher."
}

$label = if ($args.Count -gt 0) { [string]$args[0] } else { "manual" }
$launch = Resolve-PythonLaunch
$allArgs = @(
    $launch.Arguments
    $scriptPath
    "--label"
    $label
)

& $launch.FilePath @allArgs
