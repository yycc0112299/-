# Create a reproducible PYNQ-ZU Vivado RTL project without committing generated output.
set script_dir [file dirname [file normalize [info script]]]
set repo_root [file join $script_dir board_repos XilinxBoardStore-master boards]
set build_dir [file join $script_dir build pynq_zu_rtl]
set source_dir [file normalize [file join $script_dir .. person_tracking]]
if {![file exists [file join $repo_root TUL pynqzu 1.1 board.xml]]} { error "Run board setup first" }
set_param board.repoPaths [list $repo_root]
create_project pynq_zu_rtl $build_dir -part xczu5eg-sfvc784-1-e -force
set_property board_part tul.com.tw:pynqzu:part0:1.1 [current_project]
add_files [list \
 [file join $source_dir person_roi_stream.v] \
 [file join $source_dir cross_camera_pair_matcher.v] \
 [file join $script_dir dual_camera_roi_match_top.v] \
 [file join $script_dir yolox_bbox_axilite.v] \
 [file join $script_dir yolox_frame_command_adapter.v] \
 [file join $script_dir dual_camera_yolox_axilite_top.v]]
set_property top dual_camera_yolox_axilite_top [current_fileset]
update_compile_order -fileset sources_1
puts "PYNQ_ZU_PROJECT_CREATED=$build_dir"
