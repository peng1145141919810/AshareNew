param(
    [string]$RepoRoot = "F:\quant_data\AshareCSharp-runtime-skeleton",
    [string]$RepoName = "AshareCSharp-runtime-skeleton",
    [string]$Visibility = "private",
    [string]$Description = "Faithful C# runtime skeleton for Ashare governance, safety, OMS, execution, and Python bridge."
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $RepoRoot)) {
    throw "Repository root not found: $RepoRoot"
}

if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    throw "Repository root is not initialized as a git repository: $RepoRoot"
}

if ($Visibility -notin @("private", "public")) {
    throw "Visibility must be 'private' or 'public'."
}

function Get-GitHubCredential {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "git"
    $psi.Arguments = "credential-manager get"
    $psi.RedirectStandardInput = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false

    $process = [System.Diagnostics.Process]::Start($psi)
    $process.StandardInput.WriteLine("protocol=https")
    $process.StandardInput.WriteLine("host=github.com")
    $process.StandardInput.WriteLine()
    $process.StandardInput.Close()

    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    if ($process.ExitCode -ne 0) {
        throw "git credential-manager get failed: $stderr"
    }

    $pairs = @{}
    foreach ($line in ($stdout -split "`r?`n")) {
        if ($line -match "^(.*?)=(.*)$") {
            $pairs[$matches[1]] = $matches[2]
        }
    }

    if (-not $pairs.ContainsKey("username") -or -not $pairs.ContainsKey("password")) {
        throw "GitHub credential payload missing username or password."
    }

    return [PSCustomObject]@{
        Username = $pairs["username"]
        Password = $pairs["password"]
    }
}

$credential = Get-GitHubCredential
$headers = @{
    Authorization = "Bearer $($credential.Password)"
    Accept = "application/vnd.github+json"
    "User-Agent" = "Codex-AshareCSharp"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$body = @{
    name = $RepoName
    private = ($Visibility -eq "private")
    description = $Description
    auto_init = $false
} | ConvertTo-Json

$repo = $null
try {
    $repo = Invoke-RestMethod `
        -Method Post `
        -Uri "https://api.github.com/user/repos" `
        -Headers $headers `
        -Body $body `
        -ContentType "application/json"
}
catch {
    $statusCode = $null
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
    }

    if ($statusCode -eq 422) {
        $repo = Invoke-RestMethod `
            -Method Get `
            -Uri ("https://api.github.com/repos/{0}/{1}" -f $credential.Username, $RepoName) `
            -Headers $headers
    }
    else {
        throw
    }
}

$remoteUrl = $repo.clone_url
$existingRemote = $null
try {
    $existingRemote = git -C $RepoRoot remote get-url origin 2>$null
}
catch {
    $existingRemote = $null
}

if ($existingRemote) {
    git -C $RepoRoot remote set-url origin $remoteUrl | Out-Null
}
else {
    git -C $RepoRoot remote add origin $remoteUrl
}

git -C $RepoRoot push -u origin main | Out-Null

Write-Output ("Published runtime skeleton repository: {0}" -f $repo.full_name)
Write-Output ("Repository URL: {0}" -f $repo.html_url)
Write-Output ("Visibility: {0}" -f $(if ($repo.private) { "private" } else { "public" }))
