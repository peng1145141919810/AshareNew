param(
    [string]$RemoteUser = "ubuntu",
    [string]$RemoteHost = "43.129.28.141",
    [string]$Domain = "peng1145141919810.xyz",
    [string]$RemoteNginxConfig = "/etc/nginx/sites-available/peng1145141919810.xyz",
    [string]$RemoteAppRoot = "/opt/ashare_portal",
    [string]$RemoteDataRoot = "/var/lib/ashare_portal",
    [int]$BackendPort = 8765,
    [string]$Secret = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Secret)) {
    $Secret = [Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N")
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendScript = Join-Path $PSScriptRoot "portal_backend_server.py"
if (-not (Test-Path $backendScript)) {
    throw "Backend script not found: $backendScript"
}

$tmpRemoteScript = "/tmp/portal_backend_server.py"
$tmpEnv = Join-Path $env:TEMP "ashare_portal_backend.env"
$tmpService = Join-Path $env:TEMP "ashare-portal-backend.service"
$tmpPatch = Join-Path $env:TEMP "patch_nginx_portal_api.py"

[System.IO.File]::WriteAllText($tmpEnv, "ASHARE_PORTAL_SECRET=$Secret`n", (New-Object System.Text.UTF8Encoding($false)))

@"
[Unit]
Description=Ashare Portal Backend
After=network.target

[Service]
Type=simple
EnvironmentFile=/etc/ashare_portal_backend.env
ExecStart=/usr/bin/python3 $RemoteAppRoot/portal_backend_server.py --host 127.0.0.1 --port $BackendPort --db-path $RemoteDataRoot/portal.sqlite3 --secret `%ASHARE_PORTAL_SECRET`%
Restart=always
RestartSec=3
User=root
WorkingDirectory=$RemoteAppRoot

[Install]
WantedBy=multi-user.target
"@.Replace("`%ASHARE_PORTAL_SECRET`%", '$ASHARE_PORTAL_SECRET') | Set-Content -Path $tmpService -Encoding ASCII

@"
from pathlib import Path

path = Path(r"$RemoteNginxConfig")
text = path.read_text(encoding="utf-8")
if "location /api/" not in text:
    block = """
    location /api/ {
        proxy_pass http://127.0.0.1:$BackendPort/;
        proxy_http_version 1.1;
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
    }
"""
    marker = "    location / {\n        try_files `$uri `$uri/ =404;\n    }\n"
    if marker not in text:
        raise SystemExit("Could not find nginx location marker to patch.")
    text = text.replace(marker, marker + "\n" + block + "\n", 1)
    path.write_text(text, encoding="utf-8")
"@ | Set-Content -Path $tmpPatch -Encoding ASCII

ssh "$RemoteUser@$RemoteHost" "sudo mkdir -p $RemoteAppRoot $RemoteDataRoot"
scp $backendScript "$RemoteUser@$RemoteHost`:$tmpRemoteScript"
scp $tmpEnv "$RemoteUser@$RemoteHost`:/tmp/ashare_portal_backend.env"
scp $tmpService "$RemoteUser@$RemoteHost`:/tmp/ashare-portal-backend.service"
scp $tmpPatch "$RemoteUser@$RemoteHost`:/tmp/patch_nginx_portal_api.py"

ssh "$RemoteUser@$RemoteHost" "sudo mv $tmpRemoteScript $RemoteAppRoot/portal_backend_server.py && sudo chmod 755 $RemoteAppRoot/portal_backend_server.py"
ssh "$RemoteUser@$RemoteHost" "sudo mv /tmp/ashare_portal_backend.env /etc/ashare_portal_backend.env && sudo chmod 600 /etc/ashare_portal_backend.env"
ssh "$RemoteUser@$RemoteHost" "sudo mv /tmp/ashare-portal-backend.service /etc/systemd/system/ashare-portal-backend.service && sudo chmod 644 /etc/systemd/system/ashare-portal-backend.service"
ssh "$RemoteUser@$RemoteHost" "sudo python3 /tmp/patch_nginx_portal_api.py && rm -f /tmp/patch_nginx_portal_api.py"
ssh "$RemoteUser@$RemoteHost" "sudo nginx -t"
ssh "$RemoteUser@$RemoteHost" "sudo systemctl daemon-reload && sudo systemctl enable ashare-portal-backend && sudo systemctl restart ashare-portal-backend && sudo systemctl reload nginx"
ssh "$RemoteUser@$RemoteHost" "curl -fsS http://127.0.0.1:$BackendPort/api/health"
ssh "$RemoteUser@$RemoteHost" "curl -k -fsS https://$Domain/api/health"

Write-Host "Portal backend deployed."
Write-Host "API health URL: https://$Domain/api/health"
