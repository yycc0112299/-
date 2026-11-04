# Generate the HDL wrapper and run synthesis after create_pynq_zu_yolox_bd.tcl.
# This is intentionally synthesis-only: video ports are still board-interface
# dependent and have no final XDC/camera source, so implementation/bitstream is
# not claimed by this script.
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
generate_target all [get_files $bd_file]
make_wrapper -files [get_files $bd_file] -top
set wrapper [file join $build_dir pynq_zu_rtl.gen sources_1 bd pynq_zu_yolox hdl pynq_zu_yolox_wrapper.v]
if {![file exists $wrapper]} { error "Block-design wrapper was not generated" }
if {[llength [get_files -quiet $wrapper]] == 0} { add_files -norecurse $wrapper }
set_property top pynq_zu_yolox_wrapper [current_fileset]
update_compile_order -fileset sources_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
set run_status [get_property STATUS [get_runs synth_1]]
puts "PYNQ_ZU_YOLOX_SYNTHESIS_STATUS=$run_status"
if {$run_status ne "synth_design Complete!"} { error "Synthesis failed: $run_status" }
