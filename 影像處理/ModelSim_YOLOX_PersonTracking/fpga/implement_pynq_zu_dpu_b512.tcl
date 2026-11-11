# Implement and write a bitstream for the B512 PYNQ-ZU DPU design created by
# create_pynq_zu_dpu_bd.tcl.  The output is intentionally outside Git; a
# matching boot image/device tree and Vitis-AI runtime are still required on
# the board before the bitstream can run an application.
if {![info exists ::env(PYNQ_ZU_DPU_BUILD_DIR)] || $::env(PYNQ_ZU_DPU_BUILD_DIR) eq ""} {
    error "Set PYNQ_ZU_DPU_BUILD_DIR to the directory used for create_pynq_zu_dpu_bd.tcl"
}
set build_dir [file normalize $::env(PYNQ_ZU_DPU_BUILD_DIR)]
set project_file [file join $build_dir project pynq_zu_dpu.xpr]
if {![file exists $project_file]} { error "Missing DPU project: $project_file" }
open_project $project_file
set synth_status [get_property STATUS [get_runs synth_1]]
if {$synth_status ne "synth_design Complete!"} {
    error "Run synthesize_pynq_zu_dpu_b512.tcl first; synth_1 status is: $synth_status"
}
reset_run impl_1
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
set status [get_property STATUS [get_runs impl_1]]
if {$status ne "write_bitstream Complete!"} { error "PYNQ-ZU DPU implementation did not complete: $status" }
open_run impl_1
report_utilization -file [file join $build_dir dpu_b512_impl_utilization.rpt]
report_timing_summary -file [file join $build_dir dpu_b512_impl_timing_summary.rpt]
puts "PYNQ_ZU_DPU_B512_BITSTREAM_PASS=$build_dir"
