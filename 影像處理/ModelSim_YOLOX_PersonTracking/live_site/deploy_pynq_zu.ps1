[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$BoardHost,

    [string]$BoardUser = "xilinx",
    [string]$RemoteDir = "pynq_dual_dashboard",
    [string]$LocalPython = "python",
    [string]$PythonCommand = "python3",
    [int]$CameraA = 0,
    [int]$CameraB = 1,
    [string]$OverlayDir,
    [switch]$RunSystemPreflight,
    [switch]$RunCameraPreflight,
    [switch]$RunBringupCheck
)

<#
.SYNOPSIS
Build and copy the PYNQ-ZU dashboard bundle to an SD-booted PYNQ Linux board.

.DESCRIPTION
This script intentionally asks OpenSSH for authentication instead of storing a
password.  It does not start a camera or alter the board boot configuration.
Use -RunCameraPreflight only after both UVC cameras are connected.  Use
-RunBringupCheck only with a matching Overlay directory; it downloads the PL
overlay and performs the mailbox MMIO readback check.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

foreach ($command in @($LocalPython, "ssh", "scp")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Required command '$command' was not found. Install Python 3 or Windows OpenSSH Client, or pass -LocalPython."
    }
}

if ($CameraA -lt 0 -or $CameraB -lt 0 -or $CameraA -eq $CameraB) {
    throw "CameraA and CameraB must be distinct non-negative indices."
}
if ($RemoteDir -notmatch '^[A-Za-z0-9._-]+$') {
    throw "RemoteDir may contain only letters, digits, dot, underscore, and hyphen."
}
if ($RunBringupCheck -and [string]::IsNullOrWhiteSpace($OverlayDir)) {
    throw "-RunBringupCheck requires -OverlayDir containing pynq_zu_yolox.bit and .hwh."
}

$scriptDir = Split-Path -Parent $PSCommandPath
$bundle = Join-Path $env:TEMP "pynq_dual_dashboard.tar.gz"
$bundleArgs = @((Join-Path $scriptDir "prepare_pynq_dual_bundle.py"), "--output", $bundle)
if (-not [string]::IsNullOrWhiteSpace($OverlayDir)) {
    $bundleArgs += @("--overlay-dir", $OverlayDir)
}

Write-Host "Building deployment bundle..."
& $LocalPython @bundleArgs
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $bundle -PathType Leaf)) {
    throw "Bundle build failed. Set PATH/PYTHONPATH so python can load the project files."
}

$target = "$BoardUser@$BoardHost"
Write-Host "Checking SSH connection to $target ..."
& ssh -o ConnectTimeout=10 $target "true"
if ($LASTEXITCODE -ne 0) { throw "SSH connection failed; confirm SD boot, network address, account, and credentials." }

Write-Host "Copying bundle (authentication may be requested)..."
& scp $bundle "${target}:~/pynq_dual_dashboard.tar.gz"
if ($LASTEXITCODE -ne 0) { throw "SCP copy failed." }

$remoteInstall = "set -eu; test ! -e '$RemoteDir'; mkdir '$RemoteDir'; tar -xzf ~/pynq_dual_dashboard.tar.gz -C '$RemoteDir'; chmod +x '$RemoteDir/live_site/start_pynq_dual.sh'; test -f '$RemoteDir/person_tracking/assets/yolov8n.onnx'"
Write-Host "Unpacking on board..."
& ssh $target $remoteInstall
if ($LASTEXITCODE -ne 0) { throw "Remote unpack validation failed." }

if ($RunSystemPreflight) {
    Write-Host "Running read-only board dependency and model preflight..."
    & ssh $target "cd '$RemoteDir'; $PythonCommand live_site/pynq_system_preflight.py"
    if ($LASTEXITCODE -ne 0) { throw "System preflight failed; deployment remains on the board for diagnosis." }
}
if ($RunCameraPreflight) {
    Write-Host "Running read-only UVC camera preflight..."
    & ssh $target "cd '$RemoteDir'; $PythonCommand live_site/pynq_usb_camera_preflight.py --camera-a $CameraA --camera-b $CameraB"
    if ($LASTEXITCODE -ne 0) { throw "Camera preflight failed; deployment remains on the board for diagnosis." }
}
if ($RunBringupCheck) {
    Write-Host "Downloading overlay and checking AXI-Lite mailbox..."
    & ssh $target "cd '$RemoteDir'; cp overlay/pynq_zu_yolox.bit overlay/pynq_zu_yolox.hwh person_tracking/; $PythonCommand person_tracking/verify_pynq_zu_bringup.py"
    if ($LASTEXITCODE -ne 0) { throw "Overlay/MMIO check failed; deployment remains on the board for diagnosis." }
}

Write-Host "PYNQ_DEPLOY_PASS host=$BoardHost remote_dir=~/$RemoteDir"
Write-Host "Start dashboard on board: cd ~/$RemoteDir && bash live_site/start_pynq_dual.sh <PYNQ-IP-USED-IN-BROWSER>"
