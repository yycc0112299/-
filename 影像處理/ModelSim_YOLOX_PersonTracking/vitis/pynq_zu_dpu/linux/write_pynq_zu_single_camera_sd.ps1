<#
.SYNOPSIS
Writes the verified PYNQ-ZU single-camera DPU image to one explicit removable disk.

.DESCRIPTION
This is intentionally a narrow deployment tool.  It will not discover or pick a
disk automatically, never formats a disk, and only writes the image after the
operator explicitly supplies both a disk number and the erase acknowledgement.
It refuses boot/system disks and anything not reported by Windows as USB or SD.
The disk remains offline after writing so Windows cannot mount and modify the
new Linux partitions before it is removed for the board.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$DiskNumber,

    [Parameter()]
    [string]$ImagePath = 'C:\pynq_zu_dpu_2022_20261113\sd_image_20261113\pynq_zu_dpu_single_camera_tracker_2022_1.wic',

    [Parameter(Mandatory = $true)]
    [switch]$IUnderstandThisErasesDisk,

    [Parameter()]
    [string]$ErrorReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {

    $expectedSha256 = '013f29c2f3feb8c0cf26b2f7f3987557905899d44b2157713cb0c9ae8e5791d6'
    $approvedBusTypes = 'USB', 'SD'

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not $IUnderstandThisErasesDisk) {
    throw 'Refusing to write: pass -IUnderstandThisErasesDisk only after checking the selected removable disk.'
}

if (-not (Test-Path -LiteralPath $ImagePath -PathType Leaf)) {
    throw "Image does not exist: $ImagePath"
}

$image = Get-Item -LiteralPath $ImagePath
$imageHash = (Get-FileHash -LiteralPath $ImagePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($imageHash -ne $expectedSha256) {
    throw "Image SHA-256 mismatch. Expected $expectedSha256, got $imageHash. Refusing to write an unverified image."
}

$disk = Get-Disk -Number $DiskNumber
if ($disk.Number -ne $DiskNumber) {
    throw "Windows returned an unexpected disk for disk number $DiskNumber."
}
if ($disk.IsBoot -or $disk.IsSystem) {
    throw "Disk $DiskNumber is a boot or system disk and is never a valid SD-card target."
}
if ($approvedBusTypes -notcontains [string]$disk.BusType) {
    throw "Disk $DiskNumber has bus type '$($disk.BusType)'. Only USB or SD removable targets are accepted."
}
if ($disk.IsReadOnly) {
    throw "Disk $DiskNumber is read-only. Remove the physical write lock before retrying."
}
if ([UInt64]$disk.Size -lt [UInt64]$image.Length) {
    throw "Disk $DiskNumber is smaller than the image ($($disk.Size) bytes < $($image.Length) bytes)."
}
if (-not (Test-Administrator)) {
    throw 'Run this script from an elevated Windows PowerShell session so Windows can take the removable disk offline.'
}

$targetDescription = "Disk ${DiskNumber}: $($disk.FriendlyName), bus=$($disk.BusType), size=$($disk.Size) bytes"
if (-not $PSCmdlet.ShouldProcess($targetDescription, "write verified image $($image.Name)")) {
    Write-Host 'No disk was changed.'
    return
}

Set-Disk -Number $DiskNumber -IsOffline $true -Confirm:$false

$inputStream = $null
$outputStream = $null
try {
    [string]$rawTarget = "\\.\PhysicalDrive$DiskNumber"
    $inputStream = [System.IO.File]::Open($image.FullName, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
    $outputStream = [System.IO.File]::Open($rawTarget, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    $buffer = New-Object byte[] (8MB)
    [Int64]$written = 0
    while (($read = $inputStream.Read($buffer, 0, $buffer.Length)) -gt 0) {
        $outputStream.Write($buffer, 0, $read)
        $written += $read
        $percent = [Math]::Min(100, [Math]::Floor(($written * 100.0) / $image.Length))
        Write-Progress -Activity 'Writing PYNQ-ZU SD image' -Status "$written / $($image.Length) bytes" -PercentComplete $percent
    }
    $outputStream.Flush($true)
    Write-Progress -Activity 'Writing PYNQ-ZU SD image' -Completed

    if ($written -ne $image.Length) {
        throw "Write was incomplete ($written of $($image.Length) bytes). The target has been left offline."
    }
    Write-Host "PYNQ_ZU_SINGLE_CAMERA_SD_WRITE_PASS disk=$DiskNumber bytes=$written sha256=$imageHash"
    Write-Host 'The removable disk was deliberately left offline. Safely remove it and insert it into the PYNQ-ZU board.'
}
finally {
    if ($null -ne $outputStream) { $outputStream.Dispose() }
    if ($null -ne $inputStream) { $inputStream.Dispose() }
}
}
catch {
    $errorText = $_ | Out-String
    if (-not [string]::IsNullOrWhiteSpace($ErrorReportPath)) {
        Set-Content -LiteralPath $ErrorReportPath -Value $errorText -Encoding utf8
    }
    Write-Error $errorText
    exit 1
}
