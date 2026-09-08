set root [file normalize [file join [file dirname [info script]] ..]]
set pdir [file join $root vivado_project]
create_project -force mcdpt_fpga $pdir -part xc7a35tcsg324-1
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property include_dirs [file join $root src] [get_filesets sources_1]
set_property include_dirs [file join $root src] [get_filesets sim_1]
set srcs {frame_rom_a.v frame_rom_b.v frame_selector.v feature_extractor.v feature_memory.v sad_matcher.v search_controller.v tracker_fsm.v vga_timing.v bounding_box_overlay.v status_display.v mcdpt_fpga_top.v}
foreach f $srcs {read_verilog [file join $root src $f]}
read_xdc [file join $root constraints ego1_mcdpt.xdc]
add_files -fileset sim_1 [file join $root sim mcdpt_fpga_tb.v]
set_property include_dirs [file join $root src] [get_filesets sources_1]
set_property include_dirs [file join $root src] [get_filesets sim_1]
set_property top mcdpt_fpga_top [current_fileset]
set_property top mcdpt_fpga_tb [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
close_project
