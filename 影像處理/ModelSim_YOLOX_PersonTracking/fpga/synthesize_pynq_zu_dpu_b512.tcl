# Synthesize the B512 PYNQ-ZU DPU Block Design created by
# create_pynq_zu_dpu_bd.tcl. This is a resource/timing feasibility gate; it
# does not create a bitstream or assert that VART/PetaLinux is ready.
if {![info exists ::env(PYNQ_ZU_DPU_BUILD_DIR)] || $::env(PYNQ_ZU_DPU_BUILD_DIR) eq ""} {
    error "Set PYNQ_ZU_DPU_BUILD_DIR to the directory used for create_pynq_zu_dpu_bd.tcl"
}
set build_dir [file normalize $::env(PYNQ_ZU_DPU_BUILD_DIR)]
set project_file [file join $build_dir project pynq_zu_dpu.xpr]
if {![file exists $project_file]} { error "Missing DPU project: $project_file" }
open_project $project_file
set bd_file [get_files [file join $build_dir project pynq_zu_dpu.srcs sources_1 bd pynq_zu_dpu pynq_zu_dpu.bd]]
if {[llength $bd_file] != 1} { error "Missing generated PYNQ-ZU DPU BD" }
generate_target all $bd_file
set wrapper_dir [file join $build_dir project pynq_zu_dpu.gen sources_1 bd pynq_zu_dpu hdl]
set wrapper_file [file join $wrapper_dir pynq_zu_dpu_wrapper.v]
if {![file exists $wrapper_file]} {
    make_wrapper -files $bd_file -top
}
# `generate_target` can create the wrapper before this script runs.  In that
# case it exists on disk but is not necessarily part of sources_1 yet.
if {[llength [get_files -quiet $wrapper_file]] == 0} {
    add_files -norecurse $wrapper_file
}
set_property top pynq_zu_dpu_wrapper [current_fileset]
update_compile_order -fileset sources_1
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
set status [get_property STATUS [get_runs synth_1]]
if {$status ne "synth_design Complete!"} { error "PYNQ-ZU DPU synthesis did not complete: $status" }
open_run synth_1
report_utilization -file [file join $build_dir dpu_b512_utilization.rpt]
report_timing_summary -file [file join $build_dir dpu_b512_timing_summary.rpt]
puts "PYNQ_ZU_DPU_B512_SYNTHESIS_PASS=$build_dir"
