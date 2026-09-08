set root [file normalize [file join [file dirname [info script]] ..]]
file mkdir [file join $root reports]
open_checkpoint [file join $root vivado_project mcdpt_fpga.runs synth_1 mcdpt_fpga_top.dcp]
read_xdc [file join $root constraints ego1_mcdpt.xdc]
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
puts "IMPLEMENTATION COMPLETE WNS=$wns"
puts "BITSTREAM: [file join $root vivado_project mcdpt_fpga_top.bit]"
