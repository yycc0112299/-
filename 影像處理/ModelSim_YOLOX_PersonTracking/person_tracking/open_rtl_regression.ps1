param([switch]$Batch)
$ErrorActionPreference = 'Stop'
$sim = if ($env:MODELSIM_VSIM) { $env:MODELSIM_VSIM } else { 'C:\modeltech64_2020.4\win64\vsim.exe' }
if (!(Test-Path -LiteralPath $sim)) { throw "ModelSim not found: $sim" }
# ASCII work path avoids ModelSim's known problems with Chinese directory names.
$work = Join-Path $env:TEMP 'project_rtl_regression'
New-Item -ItemType Directory -Force -Path $work | Out-Null
foreach ($name in @('person_roi_stream.v','person_feature_compare.v','tb_rtl_regression.v')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $work -Force
}
$macro = @'
onerror {quit -code 1 -force}
if {![file exists work]} {vlib work}
vmap work work
vlog -sv person_roi_stream.v person_feature_compare.v tb_rtl_regression.v
vsim -onfinish stop -voptargs=+acc work.tb_rtl_regression
log -r /*
add wave -divider {Input and ROI}
add wave sim:/tb_rtl_regression/clk sim:/tb_rtl_regression/reset sim:/tb_rtl_regression/pixel_valid sim:/tb_rtl_regression/frame_start
add wave -radix unsigned sim:/tb_rtl_regression/x0 sim:/tb_rtl_regression/y0 sim:/tb_rtl_regression/x1 sim:/tb_rtl_regression/y1
add wave -divider {Feature outputs}
add wave sim:/tb_rtl_regression/feature_valid sim:/tb_rtl_regression/person_valid
add wave -radix hexadecimal sim:/tb_rtl_regression/feature
add wave -radix unsigned sim:/tb_rtl_regression/top_pixels sim:/tb_rtl_regression/bottom_pixels sim:/tb_rtl_regression/pixel_count
add wave -divider {Compare and progress}
add wave sim:/tb_rtl_regression/color_similar
add wave -radix unsigned sim:/tb_rtl_regression/frames sim:/tb_rtl_regression/checks
run -all
'@
if ($Batch) { $macro += "`nquit -code 0 -force`n" }
else { $macro += "`nview wave`nwave zoom full`n" }
Set-Content -LiteralPath (Join-Path $work 'regression.do') -Value $macro -Encoding ascii
if ($Batch) {
    Push-Location $work
    try {
        $output = & $sim -c -do regression.do 2>&1
        $output | Set-Content (Join-Path $work 'console.txt')
        $output
        if ($LASTEXITCODE -ne 0 -or !($output -match 'RTL_REGRESSION_PASS')) { throw "RTL verification failed; see $work" }
    } finally { Pop-Location }
} else {
    Start-Process -FilePath $sim -WorkingDirectory $work -ArgumentList '-do regression.do'
}
