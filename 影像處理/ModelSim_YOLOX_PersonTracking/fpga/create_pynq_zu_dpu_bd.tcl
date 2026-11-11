# Create the PYNQ-ZU DPUCZDX8G B512 Block Design.
#
# Camera USB D+/D- remains PS MIO (USB0/USB1); Linux UVC/V4L2 puts a one-camera
# frame in DDR. VART then programs this DPU's AXI-Lite control space. The DPU
# masters fetch instructions and tensors from PS DDR through LPD/HP ports.
#
# Requirements:
#   set DPUCZDX8G_HOME=<official AMD DPUCZDX8G source root>
# Optional:
#   set PYNQ_ZU_DPU_BUILD_DIR=<short writable build directory>

set script_dir [file dirname [file normalize [info script]]]
if {![info exists ::env(DPUCZDX8G_HOME)] || $::env(DPUCZDX8G_HOME) eq ""} {
    error "Set DPUCZDX8G_HOME to AMD's extracted DPUCZDX8G source root"
}
set vendor_root [file normalize $::env(DPUCZDX8G_HOME)]
set native_ip_source [file join $vendor_root dpu_ip DPUCZDX8G_v4_0_0 component.xml]
if {![file exists $native_ip_source]} {
    error "DPUCZDX8G_HOME does not contain the native DPUCZDX8G_v4_0_0 IP"
}
if {[info exists ::env(PYNQ_ZU_DPU_BUILD_DIR)] && $::env(PYNQ_ZU_DPU_BUILD_DIR) ne ""} {
    set build_dir [file normalize $::env(PYNQ_ZU_DPU_BUILD_DIR)]
} else {
    set build_dir [file normalize [file join $::env(TEMP) pynq_zu_dpu_b512]]
}
set project_dir [file join $build_dir project]
set staged_parent [file join $build_dir native_dpu_ip]
set staged_ip_root [file join $staged_parent dpu_ip]
file mkdir $build_dir

# Keep a self-contained copy of AMD's native IP under the build output. It is
# generated/external material and intentionally not checked into this project.
if {[file exists $staged_parent]} { file delete -force $staged_parent }
file mkdir $staged_parent
file copy -force [file join $vendor_root dpu_ip] $staged_parent

create_project -force pynq_zu_dpu $project_dir -part xczu5eg-sfvc784-1-e
set_property board_part tul.com.tw:pynqzu:part0:1.1 [current_project]
set_property ip_repo_paths $staged_ip_root [current_project]
update_ip_catalog
set dpu_vlnv [lindex [get_ipdefs -all xilinx.com:ip:dpuczdx8g:4.0] 0]
if {$dpu_vlnv eq ""} { error "Native DPUCZDX8G IP was not found in $staged_ip_root" }

set bd_name pynq_zu_dpu
create_bd_design $bd_name
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.5 zynq_ultra_ps_e_0
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e -config {apply_board_preset "1"} [get_bd_cells zynq_ultra_ps_e_0]

# USB controllers stay on PS MIO. No USB pin is made external to PL.
# PL0 is 100 MHz AXI-Lite; PL1 is 150 MHz DPU/DDR data. A clock wizard produces
# the DPU's required 2x (300 MHz) compute clock from PL1.
set_property -dict [list \
 CONFIG.PSU__USB0__PERIPHERAL__ENABLE {1} \
 CONFIG.PSU__USB1__PERIPHERAL__ENABLE {1} \
 CONFIG.PSU__USE__M_AXI_GP0 {1} \
 CONFIG.PSU__USE__M_AXI_GP1 {0} \
 CONFIG.PSU__USE__S_AXI_GP2 {1} \
 CONFIG.PSU__USE__S_AXI_GP3 {1} \
 CONFIG.PSU__USE__S_AXI_GP4 {1} \
 CONFIG.PSU__USE__IRQ0 {1} \
 CONFIG.PSU__FPGA_PL1_ENABLE {1} \
 CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {100} \
 CONFIG.PSU__CRL_APB__PL1_REF_CTRL__FREQMHZ {150}] [get_bd_cells zynq_ultra_ps_e_0]

create_bd_cell -type ip -vlnv $dpu_vlnv dpu_czdx8g_0
set_property -dict [list \
 CONFIG.VER_DPU_NUM {1} \
 CONFIG.ARCH {512} \
 CONFIG.ARCH_IMG_BKGRP {2} \
 CONFIG.LOAD_AUGM {1} \
 CONFIG.CONV_RELU_ADDON {3} \
 CONFIG.ALU_PARALLEL_USER {4} \
 CONFIG.ALU_LEAKYRELU {0} \
 CONFIG.SFM_ENA {0} \
 CONFIG.S_AXI_CLK_INDEPENDENT {1}] [get_bd_cells dpu_czdx8g_0]

# A SmartConnect converts the A53 HPM master width to the DPU's 32-bit S_AXI
# register file. DPU instruction traffic is 32 bit and is width-converted into
# HP2; image/weight/data traffic is 128 bit through HP0 and HP1. This avoids
# assuming that a board preset exposes the optional S_AXI_LPD clock.
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 dpu_ctrl_smc_0
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] [get_bd_cells dpu_ctrl_smc_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 dpu_instr_smc_0
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] [get_bd_cells dpu_instr_smc_0]
connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/M_AXI_HPM0_FPD] [get_bd_intf_pins dpu_ctrl_smc_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins dpu_ctrl_smc_0/M00_AXI] [get_bd_intf_pins dpu_czdx8g_0/S_AXI]
connect_bd_intf_net [get_bd_intf_pins dpu_czdx8g_0/DPU0_M_AXI_INSTR] [get_bd_intf_pins dpu_instr_smc_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins dpu_instr_smc_0/M00_AXI] [get_bd_intf_pins zynq_ultra_ps_e_0/S_AXI_HP2_FPD]
connect_bd_intf_net [get_bd_intf_pins dpu_czdx8g_0/DPU0_M_AXI_DATA0] [get_bd_intf_pins zynq_ultra_ps_e_0/S_AXI_HP0_FPD]
connect_bd_intf_net [get_bd_intf_pins dpu_czdx8g_0/DPU0_M_AXI_DATA1] [get_bd_intf_pins zynq_ultra_ps_e_0/S_AXI_HP1_FPD]

create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 dpu_2x_clk_wiz_0
set_property -dict [list CONFIG.PRIM_IN_FREQ {150.000} CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {300.000} CONFIG.USE_RESET {true}] [get_bd_cells dpu_2x_clk_wiz_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 reset_invert_0
set_property -dict [list CONFIG.C_OPERATION {not} CONFIG.C_SIZE {1}] [get_bd_cells reset_invert_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 reset_locked_0
set_property -dict [list CONFIG.CONST_VAL {1} CONFIG.CONST_WIDTH {1}] [get_bd_cells reset_locked_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 dpu_ctrl_reset_0
create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 dpu_data_reset_0
create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 dpu_2x_reset_0

connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] \
 [get_bd_pins zynq_ultra_ps_e_0/maxihpm0_fpd_aclk] [get_bd_pins dpu_czdx8g_0/s_axi_aclk] \
 [get_bd_pins dpu_ctrl_smc_0/aclk] [get_bd_pins dpu_ctrl_reset_0/slowest_sync_clk]
connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk1] \
 [get_bd_pins zynq_ultra_ps_e_0/saxihp0_fpd_aclk] [get_bd_pins zynq_ultra_ps_e_0/saxihp1_fpd_aclk] \
 [get_bd_pins zynq_ultra_ps_e_0/saxihp2_fpd_aclk] [get_bd_pins dpu_czdx8g_0/m_axi_dpu_aclk] \
 [get_bd_pins dpu_instr_smc_0/aclk] [get_bd_pins dpu_2x_clk_wiz_0/clk_in1] [get_bd_pins dpu_data_reset_0/slowest_sync_clk]
connect_bd_net [get_bd_pins dpu_2x_clk_wiz_0/clk_out1] [get_bd_pins dpu_czdx8g_0/dpu_2x_clk] [get_bd_pins dpu_2x_reset_0/slowest_sync_clk]

connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_resetn0] [get_bd_pins reset_invert_0/Op1]
connect_bd_net [get_bd_pins reset_invert_0/Res] \
 [get_bd_pins dpu_ctrl_reset_0/ext_reset_in] [get_bd_pins dpu_data_reset_0/ext_reset_in] \
 [get_bd_pins dpu_2x_reset_0/ext_reset_in] [get_bd_pins dpu_2x_clk_wiz_0/reset]
connect_bd_net [get_bd_pins reset_locked_0/dout] \
 [get_bd_pins dpu_ctrl_reset_0/dcm_locked] [get_bd_pins dpu_data_reset_0/dcm_locked] [get_bd_pins dpu_2x_reset_0/dcm_locked]
connect_bd_net [get_bd_pins dpu_ctrl_reset_0/peripheral_aresetn] \
 [get_bd_pins dpu_ctrl_smc_0/aresetn] [get_bd_pins dpu_czdx8g_0/s_axi_aresetn]
connect_bd_net [get_bd_pins dpu_data_reset_0/peripheral_aresetn] [get_bd_pins dpu_instr_smc_0/aresetn] [get_bd_pins dpu_czdx8g_0/m_axi_dpu_aresetn]
connect_bd_net [get_bd_pins dpu_2x_reset_0/peripheral_aresetn] [get_bd_pins dpu_czdx8g_0/dpu_2x_resetn]

connect_bd_net [get_bd_pins dpu_czdx8g_0/dpu0_interrupt] [get_bd_pins zynq_ultra_ps_e_0/pl_ps_irq0]
assign_bd_address
validate_bd_design
save_bd_design
puts "PYNQ_ZU_DPU_BD_CREATED=[get_property FILE_NAME [current_bd_design]]"
puts "PYNQ_ZU_DPU_CONTROL_ADDRESS=[get_property OFFSET [get_bd_addr_segs dpu_czdx8g_0/S_AXI/reg0]]"
