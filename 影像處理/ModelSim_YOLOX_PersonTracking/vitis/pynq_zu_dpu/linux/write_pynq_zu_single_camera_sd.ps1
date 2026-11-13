<#
.SYNOPSIS
Writes the verified PYNQ-ZU single-camera DPU image to one explicit removable disk.

.DESCRIPTION
This is intentionally a narrow deployment tool.  It will not discover or pick a
disk automatically, never formats a disk, and only writes the image after the
operator explicitly supplies both a disk number and the erase acknowledgement.
It refuses boot/system disks and anything not reported by Windows as USB or SD.
Any Windows-mounted volume on the selected removable card is locked and
dismounted during writing so Windows cannot modify the new Linux partitions
before the card is removed for the board.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, [int]::MaxValue)]
    [int]$DiskNumber,

    [Parameter()]
    [string]$ImagePath = 'C:\pynq_zu_dpu_2022_20261113\sd_image_20261113\pynq_zu_dpu_single_camera_tracker_python_modules_2022_1.wic',

    [Parameter(Mandatory = $true)]
    [switch]$IUnderstandThisErasesDisk,

    [Parameter()]
    [string]$ErrorReportPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {

    $expectedSha256 = '1c1604a7d60febe5e028e4ee64513be971a80f1f061a82caa1c25f480b6255ec'
    $approvedBusTypes = 'USB', 'SD'

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Add-PynqZuVolumeControlType {
    if ($null -ne ('PynqZuVolumeControl' -as [type])) {
        return
    }

    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

public static class PynqZuVolumeControl
{
    public const UInt32 GENERIC_READ = 0x80000000;
    public const UInt32 GENERIC_WRITE = 0x40000000;
    public const UInt32 FILE_SHARE_READ = 0x00000001;
    public const UInt32 FILE_SHARE_WRITE = 0x00000002;
    public const UInt32 OPEN_EXISTING = 3;
    public const UInt32 FSCTL_LOCK_VOLUME = 0x00090018;
    public const UInt32 FSCTL_DISMOUNT_VOLUME = 0x00090020;

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern SafeFileHandle CreateFile(
        string fileName,
        UInt32 desiredAccess,
        UInt32 shareMode,
        IntPtr securityAttributes,
        UInt32 creationDisposition,
        UInt32 flagsAndAttributes,
        IntPtr templateFile);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool DeviceIoControl(
        SafeFileHandle device,
        UInt32 controlCode,
        IntPtr inputBuffer,
        UInt32 inputBufferSize,
        IntPtr outputBuffer,
        UInt32 outputBufferSize,
        out UInt32 bytesReturned,
        IntPtr overlapped);
}
'@
}

function Lock-PynqZuMountedVolumes {
    param([int]$TargetDiskNumber)

    Add-PynqZuVolumeControlType
    $handles = New-Object System.Collections.ArrayList
    foreach ($partition in @(Get-Partition -DiskNumber $TargetDiskNumber)) {
        foreach ($accessPath in @($partition.AccessPaths | Where-Object { $_ -match '^[A-Za-z]:\\$' })) {
            $driveLetter = $accessPath.Substring(0, 1)
            $volumePath = "\\.\${driveLetter}:"
            $handle = [PynqZuVolumeControl]::CreateFile(
                $volumePath,
                [PynqZuVolumeControl]::GENERIC_READ -bor [PynqZuVolumeControl]::GENERIC_WRITE,
                [PynqZuVolumeControl]::FILE_SHARE_READ -bor [PynqZuVolumeControl]::FILE_SHARE_WRITE,
                [IntPtr]::Zero,
                [PynqZuVolumeControl]::OPEN_EXISTING,
                0,
                [IntPtr]::Zero)
            if ($handle.IsInvalid) {
                $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
                throw "Cannot open mounted volume $volumePath for lock/dismount (Win32 error $errorCode). Close Explorer and reject Windows scan/repair prompts, then retry."
            }

            try {
                [uint32]$bytesReturned = 0
                if (-not [PynqZuVolumeControl]::DeviceIoControl(
                    $handle, [PynqZuVolumeControl]::FSCTL_LOCK_VOLUME,
                    [IntPtr]::Zero, 0, [IntPtr]::Zero, 0,
                    [ref]$bytesReturned, [IntPtr]::Zero)) {
                    $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
                    throw "Cannot lock mounted volume $volumePath (Win32 error $errorCode). Close Explorer and reject Windows scan/repair prompts, then retry."
                }
                if (-not [PynqZuVolumeControl]::DeviceIoControl(
                    $handle, [PynqZuVolumeControl]::FSCTL_DISMOUNT_VOLUME,
                    [IntPtr]::Zero, 0, [IntPtr]::Zero, 0,
                    [ref]$bytesReturned, [IntPtr]::Zero)) {
                    $errorCode = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
                    throw "Cannot dismount mounted volume $volumePath (Win32 error $errorCode)."
                }
                [void]$handles.Add($handle)
                $handle = $null
            }
            finally {
                if ($null -ne $handle) { $handle.Dispose() }
            }
        }
    }
    return $handles
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
    throw 'Run this script from an elevated Windows PowerShell session so Windows can lock and dismount the removable card volume.'
}

$targetDescription = "Disk ${DiskNumber}: $($disk.FriendlyName), bus=$($disk.BusType), size=$($disk.Size) bytes"
if (-not $PSCmdlet.ShouldProcess($targetDescription, "write verified image $($image.Name)")) {
    Write-Host 'No disk was changed.'
    return
}

$inputStream = $null
$outputStream = $null
$volumeHandles = @()
try {
    $volumeHandles = @(Lock-PynqZuMountedVolumes -TargetDiskNumber $DiskNumber)
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
        throw "Write was incomplete ($written of $($image.Length) bytes). The target volume remains dismounted."
    }
    Write-Host "PYNQ_ZU_SINGLE_CAMERA_SD_WRITE_PASS disk=$DiskNumber bytes=$written sha256=$imageHash"
    Write-Host 'The mounted Windows volume was deliberately dismounted. Safely remove the card and insert it into the PYNQ-ZU board.'
}
finally {
    if ($null -ne $outputStream) { $outputStream.Dispose() }
    if ($null -ne $inputStream) { $inputStream.Dispose() }
    foreach ($handle in $volumeHandles) {
        if ($null -ne $handle) { $handle.Dispose() }
    }
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
