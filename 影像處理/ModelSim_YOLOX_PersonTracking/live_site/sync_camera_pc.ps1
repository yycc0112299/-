param(
    [string]$Repo = (Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))),
    [string]$Branch = 'main',
    [string]$Bind = '0.0.0.0',
    [string]$AllowHost
)
$ErrorActionPreference = 'Stop'
if (!(Test-Path (Join-Path $Repo '.git'))) { throw "Not a Git checkout: $Repo" }
git -C $Repo fetch origin $Branch
git -C $Repo pull --ff-only origin $Branch
if ($LASTEXITCODE -ne 0) { throw 'Git pull failed; resolve local changes before starting the camera service.' }
$args = @('--bind', $Bind)
if ($AllowHost) { $args += @('--allow-host', $AllowHost) }
& (Join-Path $PSScriptRoot 'start_dual.ps1') -ServerArgs $args
