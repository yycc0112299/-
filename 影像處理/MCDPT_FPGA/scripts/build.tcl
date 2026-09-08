set root [file normalize [file join [file dirname [info script]] ..]]
file mkdir [file join $root reports]
source [file join $root scripts create_project.tcl]
open_project [file join $root vivado_project mcdpt_fpga.xpr]
synth_design -top mcdpt_fpga_top -part xc7a35tcsg324-1
report_utilization -file [file join $root reports synthesis_utilization.rpt]
write_checkpoint -force [file join $root vivado_project mcdpt_fpga_synth.dcp]
opt_design
place_design
phys_opt_design
route_design
phys_opt_design
report_utilization -file [file join $root reports implementation_utilization.rpt]
report_timing_summary -file [file join $root reports timing_summary.rpt]
report_drc -file [file join $root reports drc.rpt]
report_route_status -file [file join $root reports route_status.rpt]
set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
if {$wns < 0.0} {error "Timing failed: WNS=$wns"}
write_checkpoint -force [file join $root vivado_project mcdpt_fpga_routed.dcp]
write_bitstream -force [file join $root vivado_project mcdpt_fpga_top.bit]
puts "BUILD COMPLETE WNS=$wns"
puts "BITSTREAM: [file join $root vivado_project mcdpt_fpga_top.bit]"
