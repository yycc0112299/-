set root [file normalize [file join [file dirname [info script]] ..]]
file mkdir [file join $root reports]
create_project -force mcdpt_sim [file join $root sim_project] -part xc7a35tcsg324-1
set_property target_language Verilog [current_project]
set_property include_dirs [file join $root src] [get_filesets sources_1]
set_property include_dirs [file join $root src] [get_filesets sim_1]
set srcs {frame_rom_a.v frame_rom_b.v frame_selector.v feature_extractor.v feature_memory.v sad_matcher.v search_controller.v tracker_fsm.v}
foreach f $srcs {read_verilog [file join $root src $f]}
add_files -fileset sim_1 [file join $root sim mcdpt_fpga_tb.v]
set_property top mcdpt_fpga_tb [get_filesets sim_1]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
launch_simulation -mode behavioral
set log [file join $root reports simulation_result.log]
run all
close_sim
