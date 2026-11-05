param([switch]$Batch)

$ErrorActionPreference = 'Stop'
$xsimBin = if ($env:VIVADO_XSIM_BIN) { $env:VIVADO_XSIM_BIN } else { 'C:\Xilinx\Vivado\2024.2\bin' }
$xvlog = Join-Path $xsimBin 'xvlog.bat'
$xelab = Join-Path $xsimBin 'xelab.bat'
$xsim = Join-Path $xsimBin 'xsim.bat'
foreach ($tool in @($xvlog, $xelab, $xsim)) {
    if (!(Test-Path -LiteralPath $tool)) {
        throw "Vivado XSim tool not found: $tool. Set VIVADO_XSIM_BIN to Vivado's bin directory."
    }
}

# Stage sources to an ASCII TEMP path because Vivado command-line tools can fail
# when a working path contains non-ASCII characters.
$work = Join-Path $env:TEMP 'project_xsim_yolox_command_path'
New-Item -ItemType Directory -Force -Path $work | Out-Null
foreach ($name in @('yolox_bbox_axilite.v', 'yolox_frame_command_adapter.v', 'tb_yolox_command_path.v')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $work -Force
}

Push-Location $work
try {
    & $xvlog -sv yolox_bbox_axilite.v yolox_frame_command_adapter.v tb_yolox_command_path.v
    if ($LASTEXITCODE -ne 0) { throw "xvlog failed; see $work" }
    & $xelab tb_yolox_command_path -s yolox_command_path_xsim
    if ($LASTEXITCODE -ne 0) { throw "xelab failed; see $work" }
    if ($Batch) {
        $output = & $xsim yolox_command_path_xsim -runall 2>&1
        $output | Set-Content (Join-Path $work 'console.txt')
        $output
        if ($LASTEXITCODE -ne 0 -or !($output -match 'YOLOX_COMMAND_PATH_PASS')) {
            throw "XSim YOLOX command-path verification failed; see $work"
        }
    } else {
        & $xsim yolox_command_path_xsim -gui
    }
} finally {
    Pop-Location
}
