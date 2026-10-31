param([switch]$Batch)

$ErrorActionPreference = 'Stop'
$xsimBin = if ($env:VIVADO_XSIM_BIN) { $env:VIVADO_XSIM_BIN } else { 'C:\Xilinx\Vivado\2024.2\bin' }
$xvlog = Join-Path $xsimBin 'xvlog.bat'
$xelab = Join-Path $xsimBin 'xelab.bat'
$xsim = Join-Path $xsimBin 'xsim.bat'
foreach ($tool in @($xvlog, $xelab, $xsim)) {
    if (!(Test-Path -LiteralPath $tool)) { throw "Vivado XSim tool not found: $tool. Set VIVADO_XSIM_BIN to Vivado's bin directory." }
}

# The temporary ASCII path avoids simulator path issues caused by the repository's Chinese directory name.
$work = Join-Path $env:TEMP 'project_xsim_rtl_regression'
New-Item -ItemType Directory -Force -Path $work | Out-Null
foreach ($name in @('person_roi_stream.v', 'person_feature_compare.v', 'tb_rtl_regression.v')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $work -Force
}

Push-Location $work
try {
    & $xvlog -sv person_roi_stream.v person_feature_compare.v tb_rtl_regression.v
    if ($LASTEXITCODE -ne 0) { throw "xvlog failed; see $work" }
    & $xelab tb_rtl_regression -s rtl_regression_xsim
    if ($LASTEXITCODE -ne 0) { throw "xelab failed; see $work" }

    if ($Batch) {
        $output = & $xsim rtl_regression_xsim -runall 2>&1
        $output | Set-Content (Join-Path $work 'console.txt')
        $output
        if ($LASTEXITCODE -ne 0 -or !($output -match 'RTL_REGRESSION_PASS')) { throw "XSim RTL verification failed; see $work" }
    } else {
        & $xsim rtl_regression_xsim -gui
    }
} finally {
    Pop-Location
}
