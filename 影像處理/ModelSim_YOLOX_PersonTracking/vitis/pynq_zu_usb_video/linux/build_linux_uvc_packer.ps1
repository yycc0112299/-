[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'build'),
    [string]$VitisRoot = 'C:\Xilinx_Embedded_2024_2\Vitis\2024.2'
)

$ErrorActionPreference = 'Stop'
$toolBin = Join-Path $VitisRoot 'gnu\aarch64\nt\aarch64-linux\bin'
$compiler = Join-Path $toolBin 'aarch64-linux-gnu-gcc.exe'
$source = Join-Path $PSScriptRoot 'uvc_v4l2_packer.c'
$output = Join-Path $OutputDirectory 'uvc_v4l2_packer'
if (!(Test-Path -LiteralPath $compiler)) { throw "Vitis Linux compiler not found: $compiler" }
if (!(Test-Path -LiteralPath $source)) { throw "Source not found: $source" }
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$originalPath = $env:PATH
try {
    $env:PATH = "$toolBin;$originalPath"
    & $compiler -std=c11 -Wall -Wextra -Werror -O2 $source -o $output
    if ($LASTEXITCODE -ne 0) { throw "AArch64 compiler failed with exit code $LASTEXITCODE" }
} finally {
    $env:PATH = $originalPath
}
Get-Item -LiteralPath $output | Select-Object FullName, Length, LastWriteTime
Write-Output "PYNQ_ZU_UVC_PACKER_BUILD_PASS=$output"
