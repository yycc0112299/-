# Implement and write a PYNQ-ZU bitstream after the reproducible RTL/BD and
# synthesis scripts have completed. The target directory follows the same
# short ASCII-path policy as the preceding scripts.
set script_dir [file dirname [file normalize [info script]]]
if {[info exists ::env(PYNQ_ZU_BUILD_DIR)] && $::env(PYNQ_ZU_BUILD_DIR) ne ""} {
 set build_dir [file normalize $::env(PYNQ_ZU_BUILD_DIR)]
} else {
 set build_dir [file normalize [file join $::env(TEMP) pynq_zu_rtl]]
}
set project_file [file join $build_dir pynq_zu_rtl.xpr]
if {![file exists $project_file]} { error "Run create_pynq_zu_rtl_project.tcl first" }
open_project $project_file
set bd_file [file join $build_dir pynq_zu_rtl.srcs sources_1 bd pynq_zu_yolox pynq_zu_yolox.bd]
if {![file exists $bd_file]} { error "Run create_pynq_zu_yolox_bd.tcl first" }
set wrapper [file join $build_dir pynq_zu_rtl.gen sources_1 bd pynq_zu_yolox hdl pynq_zu_yolox_wrapper.v]
if {![file exists $wrapper]} { error "Run synthesize_pynq_zu_yolox.tcl first" }

# Do not downgrade UCIO/NSTD checks: a bitstream may only be emitted when all
# external ports have deliberate board constraints.
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
set run_status [get_property STATUS [get_runs impl_1]]
puts "PYNQ_ZU_YOLOX_IMPLEMENT_STATUS=$run_status"
if {$run_status ne "write_bitstream Complete!"} {
 error "Implementation or bitstream generation failed: $run_status"
}
set bit_file [file join $build_dir pynq_zu_rtl.runs impl_1 pynq_zu_yolox_wrapper.bit]
if {![file exists $bit_file]} { error "Vivado reported success but bitstream is missing: $bit_file" }
puts "PYNQ_ZU_YOLOX_BITSTREAM=$bit_file"
