# Create a short-ASCII-path Vivado project for the USB-camera DMA Block Design.
set script_dir [file dirname [file normalize [info script]]]
if {[info exists ::env(PYNQ_ZU_BUILD_DIR)] && $::env(PYNQ_ZU_BUILD_DIR) ne ""} {
 set build_dir [file normalize $::env(PYNQ_ZU_BUILD_DIR)]
} else {
 set build_dir [file normalize [file join $::env(TEMP) pynq_zu_usb_video]]
}
set board_root [file join $script_dir board_repos XilinxBoardStore-master boards]
set source_dir [file normalize [file join $script_dir .. person_tracking]]
if {![file exists [file join $board_root TUL pynqzu 1.1 board.xml]]} { error "PYNQ-ZU board files are missing under $board_root" }
set_param board.repoPaths [list $board_root]
create_project pynq_zu_usb_video $build_dir -part xczu5eg-sfvc784-1-e -force
set_property board_part tul.com.tw:pynqzu:part0:1.1 [current_project]

# Stage HDL because Vivado child processes do not reliably consume the parent
# repository's long Unicode path on Windows.
set staged_dir [file join $build_dir rtl_src]
file mkdir $staged_dir
set source_files [list \
 [file join $source_dir person_roi_stream.v] \
 [file join $source_dir cross_camera_pair_matcher.v] \
 [file join $script_dir dual_camera_roi_match_top.v] \
 [file join $script_dir yolox_bbox_axilite.v] \
 [file join $script_dir yolox_frame_command_adapter.v] \
 [file join $script_dir dual_camera_yolox_axilite_top.v] \
 [file join $script_dir axis_dual_rgb_stream_adapter.v] \
 [file join $script_dir dual_camera_yolox_axis_top.v]]
set staged_files {}
foreach source_file $source_files {
 if {![file exists $source_file]} { error "Required HDL source is missing: $source_file" }
 set staged_file [file join $staged_dir [file tail $source_file]]
 file copy -force $source_file $staged_file
 lappend staged_files $staged_file
}
add_files $staged_files
update_compile_order -fileset sources_1
puts "PYNQ_ZU_USB_VIDEO_PROJECT_CREATED=$build_dir"
