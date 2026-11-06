# Generate the wrapper, bitstream and hardware hand-off archive used by Vitis.
# Run only after create_pynq_zu_usb_video_project.tcl and
# create_pynq_zu_usb_video_bd.tcl have completed successfully.
if {[info exists ::env(PYNQ_ZU_BUILD_DIR)] && $::env(PYNQ_ZU_BUILD_DIR) ne ""} {
 set build_dir [file normalize $::env(PYNQ_ZU_BUILD_DIR)]
} else {
 set build_dir [file normalize [file join $::env(TEMP) pynq_zu_usb_video]]
}
set project_file [file join $build_dir pynq_zu_usb_video.xpr]
if {![file exists $project_file]} { error "Run create_pynq_zu_usb_video_project.tcl first" }
open_project $project_file
set bd_file [file join $build_dir pynq_zu_usb_video.srcs sources_1 bd pynq_zu_usb_video pynq_zu_usb_video.bd]
if {![file exists $bd_file]} { error "Run create_pynq_zu_usb_video_bd.tcl first" }
generate_target all [get_files $bd_file]
make_wrapper -files [get_files $bd_file] -top
set wrapper [file join $build_dir pynq_zu_usb_video.gen sources_1 bd pynq_zu_usb_video hdl pynq_zu_usb_video_wrapper.v]
if {![file exists $wrapper]} { error "Block-design wrapper was not generated" }
if {[llength [get_files -quiet $wrapper]] == 0} { add_files -norecurse $wrapper }
set_property top pynq_zu_usb_video_wrapper [current_fileset]
update_compile_order -fileset sources_1
reset_run synth_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {[get_property STATUS [get_runs synth_1]] ne "synth_design Complete!"} { error "Synthesis failed: [get_property STATUS [get_runs synth_1]]" }
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property STATUS [get_runs impl_1]] ne "write_bitstream Complete!"} { error "Implementation failed: [get_property STATUS [get_runs impl_1]]" }
set xsa_file [file join $build_dir pynq_zu_usb_video.xsa]
write_hw_platform -fixed -include_bit -force -file $xsa_file
if {![file exists $xsa_file]} { error "XSA export failed: $xsa_file" }
puts "PYNQ_ZU_USB_VIDEO_XSA=$xsa_file"
