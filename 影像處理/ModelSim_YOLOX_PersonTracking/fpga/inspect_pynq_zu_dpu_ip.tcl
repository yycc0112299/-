# Inspect the packaged DPU CZDX8G IP's actual Vivado-visible pins/interfaces.
# This is deliberately separate from implementation: encrypted DPU sources can
# change their exposed names across AMD releases, so BD wiring must use observed
# names rather than copied ZCU104 assumptions.

if {[info exists ::env(DPUCZDX8G_HOME)] && $::env(DPUCZDX8G_HOME) ne ""} {
    # Native DPU IP has the AXI-Lite control interface required by Linux VART.
    set ip_repo [file join [file normalize $::env(DPUCZDX8G_HOME)] dpu_ip]
    set dpu_pattern {xilinx.com:ip:dpuczdx8g:*}
    set build_dir [file normalize [file join $::env(TEMP) pynq_zu_dpu_native_inspect]]
} else {
    # Retained to inspect the legacy Vitis RTL-kernel package when diagnosing it.
    if {![info exists ::env(PYNQ_ZU_DPU_BUILD_DIR)] || $::env(PYNQ_ZU_DPU_BUILD_DIR) eq ""} {
        error "Set DPUCZDX8G_HOME (native IP) or PYNQ_ZU_DPU_BUILD_DIR (legacy package)"
    }
    set build_dir [file normalize $::env(PYNQ_ZU_DPU_BUILD_DIR)]
    set ip_repo [file join $build_dir ip_repo]
    set dpu_pattern {xilinx.com:RTLKernel:dpu_wrapper:*}
}
if {![file exists $ip_repo]} { error "Missing DPU IP repository: $ip_repo" }
set probe_dir [file join $build_dir inspect]
create_project -force pynq_zu_dpu_inspect $probe_dir -part xczu5eg-sfvc784-1-e
set_property ip_repo_paths $ip_repo [current_project]
update_ip_catalog
set matches [get_ipdefs -all $dpu_pattern]
if {[llength $matches] != 1} { error "Expected exactly one DPU IP matching $dpu_pattern, found: $matches" }
set dpu_vlnv [lindex $matches 0]
create_bd_design pynq_zu_dpu_inspect
create_bd_cell -type ip -vlnv $dpu_vlnv dpu_czdx8g_0
puts "PYNQ_ZU_DPU_VLNV=$dpu_vlnv"
puts "PYNQ_ZU_DPU_PINS=[lsort [get_property NAME [get_bd_pins dpu_czdx8g_0/*]]]"
puts "PYNQ_ZU_DPU_INTERFACES=[lsort [get_property NAME [get_bd_intf_pins dpu_czdx8g_0/*]]]"
foreach interface [get_bd_intf_pins dpu_czdx8g_0/*] {
    puts "PYNQ_ZU_DPU_INTERFACE_[get_property NAME $interface]_WIDTH=[get_property CONFIG.DATA_WIDTH $interface]"
}
set config_properties {}
foreach property [list_property [get_bd_cells dpu_czdx8g_0]] {
    if {[string match {CONFIG.*} $property]} { lappend config_properties $property }
}
puts "PYNQ_ZU_DPU_CONFIG_PROPERTIES=[lsort $config_properties]"
foreach property {CONFIG.VER_DPU_NUM CONFIG.ARCH CONFIG.ARCH_IMG_BKGRP CONFIG.LOAD_AUGM CONFIG.CONV_RELU_ADDON CONFIG.ALU_PARALLEL_USER CONFIG.ALU_LEAKYRELU CONFIG.SFM_ENA CONFIG.S_AXI_FREQ_MHZ CONFIG.M_AXI_FREQ_MHZ CONFIG.ARCH_HP_BW} {
    puts "PYNQ_ZU_DPU_$property=[get_property $property [get_bd_cells dpu_czdx8g_0]]"
}
save_bd_design
close_project
