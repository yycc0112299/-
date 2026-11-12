<#!
.SYNOPSIS
Stages the implemented USB-video Block Design as a PYNQ overlay.

.DESCRIPTION
PYNQ requires a bitstream and its matching HWH to have the same filename stem.
This script copies the two local Vivado implementation artifacts to a selected
directory as pynq_zu_usb_video.bit and pynq_zu_usb_video.hwh.  It neither
contacts a board nor writes an SD card or boot image.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$BuildDir,

    [string]$OutputDir = (Join-Path $env:TEMP 'pynq_zu_usb_video_overlay')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$bit = Join-Path $BuildDir 'pynq_zu_usb_video.runs\impl_1\pynq_zu_usb_video_wrapper.bit'
$hwh = Join-Path $BuildDir 'pynq_zu_usb_video.gen\sources_1\bd\pynq_zu_usb_video\hw_handoff\pynq_zu_usb_video.hwh'
foreach ($artifact in @($bit, $hwh)) {
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
        throw "Missing Vivado USB-video artifact: $artifact. Run implementation first."
    }
    if ((Get-Item -LiteralPath $artifact).Length -le 0) {
        throw "Vivado USB-video artifact is empty: $artifact"
    }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$overlayBase = 'pynq_zu_usb_video'
$outBit = Join-Path $OutputDir "$overlayBase.bit"
$outHwh = Join-Path $OutputDir "$overlayBase.hwh"
Copy-Item -LiteralPath $bit -Destination $outBit -Force
Copy-Item -LiteralPath $hwh -Destination $outHwh -Force

foreach ($artifact in @($outBit, $outHwh)) {
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf) -or
        (Get-Item -LiteralPath $artifact).Length -le 0) {
        throw "Overlay staging failed: $artifact"
    }
}

Write-Output "PYNQ_ZU_USB_VIDEO_OVERLAY_DIR=$OutputDir"
Write-Output "PYNQ_ZU_USB_VIDEO_OVERLAY_BIT=$outBit"
Write-Output "PYNQ_ZU_USB_VIDEO_OVERLAY_HWH=$outHwh"
Write-Output "PYNQ_ZU_USB_VIDEO_OVERLAY_BIT_SHA256=$((Get-FileHash -LiteralPath $outBit -Algorithm SHA256).Hash)"
Write-Output "PYNQ_ZU_USB_VIDEO_OVERLAY_HWH_SHA256=$((Get-FileHash -LiteralPath $outHwh -Algorithm SHA256).Hash)"
