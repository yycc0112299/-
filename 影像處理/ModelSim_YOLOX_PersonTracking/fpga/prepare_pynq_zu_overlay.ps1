<#!
.SYNOPSIS
Creates a PYNQ-ZU overlay directory from an implemented local Vivado build.

.DESCRIPTION
PYNQ requires the .bit and its matching .hwh filename to share the same stem.
This script copies (rather than moves) the generated artifacts into a deployable
directory. It does not upload anything to the board and does not modify an SD
card. Run it after implement_pynq_zu_yolox.tcl reports write_bitstream Complete!.
#>
[CmdletBinding()]
param(
    [string]$BuildDir = 'C:\pynq_zu_bringup',
    [string]$OutputDir = (Join-Path $env:TEMP 'pynq_zu_yolox_overlay')
)

$ErrorActionPreference = 'Stop'
$bit = Join-Path $BuildDir 'pynq_zu_rtl.runs\impl_1\pynq_zu_yolox_wrapper.bit'
$hwh = Join-Path $BuildDir 'pynq_zu_rtl.gen\sources_1\bd\pynq_zu_yolox\hw_handoff\pynq_zu_yolox.hwh'
foreach ($artifact in @($bit, $hwh)) {
    if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) {
        throw "Missing Vivado artifact: $artifact. Run the four PYNQ-ZU TCL scripts first."
    }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$overlayBase = 'pynq_zu_yolox'
$outBit = Join-Path $OutputDir "$overlayBase.bit"
$outHwh = Join-Path $OutputDir "$overlayBase.hwh"
Copy-Item -LiteralPath $bit -Destination $outBit -Force
Copy-Item -LiteralPath $hwh -Destination $outHwh -Force

if ((Get-Item -LiteralPath $outBit).Length -le 0 -or (Get-Item -LiteralPath $outHwh).Length -le 0) {
    throw 'Copied overlay artifact is empty.'
}

Write-Output "PYNQ_ZU_OVERLAY_DIR=$OutputDir"
Write-Output "PYNQ_ZU_OVERLAY_BIT=$outBit"
Write-Output "PYNQ_ZU_OVERLAY_HWH=$outHwh"
