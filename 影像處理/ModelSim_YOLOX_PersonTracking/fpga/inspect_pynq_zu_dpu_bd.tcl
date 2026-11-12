# Print actual pins from a partially or fully generated PYNQ-ZU DPU BD.
if {![info exists ::env(PYNQ_ZU_DPU_BUILD_DIR)] || $::env(PYNQ_ZU_DPU_BUILD_DIR) eq ""} {
    error "Set PYNQ_ZU_DPU_BUILD_DIR"
}
set build_dir [file normalize $::env(PYNQ_ZU_DPU_BUILD_DIR)]
open_project [file join $build_dir project pynq_zu_dpu.xpr]
open_bd_design [get_files [file join $build_dir project pynq_zu_dpu.srcs sources_1 bd pynq_zu_dpu pynq_zu_dpu.bd]]
puts "PYNQ_ZU_PS_PINS=[lsort [get_property NAME [get_bd_pins zynq_ultra_ps_e_0/*]]]"
puts "PYNQ_ZU_DPU_VISIBLE_PINS=[lsort [get_property NAME [get_bd_pins dpu_czdx8g_0/*]]]"
set dpu_control_segments [get_bd_addr_segs -of_objects [get_bd_addr_spaces zynq_ultra_ps_e_0/Data] \
    -filter {NAME =~ "*dpu_czdx8g_0*"}]
foreach segment $dpu_control_segments {
    puts "PYNQ_ZU_DPU_CONTROL_SEGMENT_[get_property NAME $segment]=[get_property OFFSET $segment],[get_property RANGE $segment]"
}
close_project
