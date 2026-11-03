param(
    [int]$CameraA = 0,
    [int]$CameraB = -1,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$site = $PSScriptRoot
$project = Split-Path -Parent $site
$work = Join-Path $project 'work\remote_site'
$cloudflared = Join-Path $env:LOCALAPPDATA 'Cloudflare\cloudflared\cloudflared.exe'
$port = 8766
if (!(Test-Path -LiteralPath $cloudflared)) { throw "cloudflared.exe not found: $cloudflared" }
if ($CameraA -lt 0 -or $CameraA -gt 9 -or $CameraB -lt -1 -or $CameraB -gt 9) {
    throw 'CameraA must be 0..9 and CameraB must be -1..9.'
}

New-Item -ItemType Directory -Force -Path $work | Out-Null
$serverLog = Join-Path $work 'server.log'
$serverError = Join-Path $work 'server-error.log'
$tunnelLog = Join-Path $work 'cloudflared.log'
$tunnelError = Join-Path $work 'cloudflared-error.log'
$linkFile = Join-Path $work 'private-link.txt'

# This launcher owns port 8766 for the current project. Stop only its prior
# listener so a new Quick Tunnel maps to a newly started local service.
Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction Stop }

$python = (Get-Command py.exe -ErrorAction SilentlyContinue).Source
if (!$python) { throw 'py.exe was not found.' }
$serverArgs = @('-3', 'dual_server.py', '--port', $port, '--allow-trycloudflare',
                '--camera-a', $CameraA, '--camera-b', $CameraB)
$server = Start-Process -FilePath $python -ArgumentList $serverArgs -WorkingDirectory $site -PassThru -RedirectStandardOutput $serverLog -RedirectStandardError $serverError

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        Invoke-RestMethod "http://127.0.0.1:$port/api/health" -TimeoutSec 2 | Out-Null
        $ready = $true
        break
    } catch { Start-Sleep -Milliseconds 500 }
}
if (!$ready) {
    if (!$server.HasExited) { Stop-Process -Id $server.Id -Force }
    throw "Website service did not become healthy. See $serverError"
}

$tunnel = Start-Process -FilePath $cloudflared -ArgumentList @('tunnel','--no-autoupdate','--url',"http://127.0.0.1:$port") -PassThru -RedirectStandardOutput $tunnelLog -RedirectStandardError $tunnelError
$link = $null
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    $text = (Get-Content -LiteralPath $tunnelLog,$tunnelError -Raw -ErrorAction SilentlyContinue) -join "`n"
    $match = [regex]::Match($text, 'https://[a-z0-9-]+\.trycloudflare\.com')
    if ($match.Success) { $link = $match.Value; break }
    if ($tunnel.HasExited) { break }
}
if (!$link) {
    if (!$tunnel.HasExited) { Stop-Process -Id $tunnel.Id -Force }
    throw "Cloudflare Quick Tunnel did not return a URL. See $tunnelError"
}
$link | Set-Content -LiteralPath $linkFile -NoNewline -Encoding utf8
if (!$NoBrowser) { Start-Process $link }
Write-Output "SERVER_PID=$($server.Id)"
Write-Output "TUNNEL_PID=$($tunnel.Id)"
Write-Output "PRIVATE_LINK=$link"
