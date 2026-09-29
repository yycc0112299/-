param([switch]$Gui)
$ErrorActionPreference = 'Stop'
$simulator = $env:MODELSIM_VSIM
if (!$simulator) { $simulator = (Get-Command vsim.exe -ErrorAction SilentlyContinue).Source }
if (!$simulator -and (Test-Path -LiteralPath 'C:\modeltech64_2020.4\win64\vsim.exe')) { $simulator = 'C:\modeltech64_2020.4\win64\vsim.exe' }
if (!$simulator) { throw 'ModelSim vsim.exe not found. Add it to PATH or set MODELSIM_VSIM.' }
if (!(Test-Path -LiteralPath $simulator)) { throw "ModelSim not found: $simulator" }
$runDirectory = Join-Path $env:TEMP ('two_camera_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runDirectory | Out-Null
Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object { $_.Extension -in '.v','.do' } | Copy-Item -Destination $runDirectory
Write-Output "ModelSim run directory: $runDirectory"
if ($Gui) {
    Start-Process -FilePath $simulator -WorkingDirectory $runDirectory -ArgumentList '-do','run.do'
    exit 0
}
Push-Location -LiteralPath $runDirectory
try {
    & $simulator -c -do 'do run_batch.do'
    $simulationExit = $LASTEXITCODE
} finally { Pop-Location }
$results = Join-Path $PSScriptRoot 'results'
New-Item -ItemType Directory -Path $results -Force | Out-Null
foreach ($name in @('transcript','vsim.wlf')) {
    $source = Join-Path $runDirectory $name
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $results -Force }
}
Set-Content -LiteralPath (Join-Path $results 'last_run.txt') -Value $runDirectory
if ($simulationExit -ne 0) { throw "ModelSim failed with exit code $simulationExit" }
if (!(Select-String -LiteralPath (Join-Path $results 'transcript') -SimpleMatch 'ALL PASS:')) {
    throw 'ModelSim ended without the expected test completion marker'
}
Write-Output 'Verified ALL PASS; transcript and waveform copied to results.'
