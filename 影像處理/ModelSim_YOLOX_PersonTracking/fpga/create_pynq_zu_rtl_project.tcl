# Create a reproducible PYNQ-ZU Vivado RTL project without committing generated output.
set script_dir [file dirname [file normalize [info script]]]
set repo_root [file join $script_dir board_repos XilinxBoardStore-master boards]
# Vivado IP generation cannot reliably operate below this repository's long
# Unicode path on Windows.  Override PYNQ_ZU_BUILD_DIR when desired; otherwise
# use the short per-user TEMP location.  Generated projects are never tracked.
if {[info exists ::env(PYNQ_ZU_BUILD_DIR)] && $::env(PYNQ_ZU_BUILD_DIR) ne ""} {
 set build_dir [file normalize $::env(PYNQ_ZU_BUILD_DIR)]
} else {
 set build_dir [file normalize [file join $::env(TEMP) pynq_zu_rtl]]
}
set source_dir [file normalize [file join $script_dir .. person_tracking]]
if {![file exists [file join $repo_root TUL pynqzu 1.1 board.xml]]} { error "Run board setup first" }
set_param board.repoPaths [list $repo_root]
create_project pynq_zu_rtl $build_dir -part xczu5eg-sfvc784-1-e -force
set_property board_part tul.com.tw:pynqzu:part0:1.1 [current_project]
# Child synthesis runs on Windows do not reliably parse source paths containing
# non-ASCII characters. Stage only the HDL inputs into the short ASCII build
# directory; the repository remains the authoritative source of each file.
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
set_property top dual_camera_yolox_axilite_top [current_fileset]
update_compile_order -fileset sources_1
puts "PYNQ_ZU_PROJECT_CREATED=$build_dir"
