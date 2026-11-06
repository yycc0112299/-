# Build the PYNQ-ZU USB-camera hardware boundary.
#
# Logitech C270 is UVC: its D+/D- pairs terminate in the MPSoC USB controller,
# not in PL I/O.  The PYNQ-ZU board preset assigns USB0 to MIO 52 .. 63 and
# USB1 to MIO 64 .. 75.  Vitis/Linux receives UVC frames into DDR, then a
# software-programmed AXI DMA sends packed A/B RGB888 words to the PL core.
# One 64-bit word is B[55:32] + A[23:0], as required by the RTL adapter.

set script_dir [file dirname [file normalize [info script]]]
if {[info exists ::env(PYNQ_ZU_BUILD_DIR)] && $::env(PYNQ_ZU_BUILD_DIR) ne ""} {
 set build_dir [file normalize $::env(PYNQ_ZU_BUILD_DIR)]
} else {
 set build_dir [file normalize [file join $::env(TEMP) pynq_zu_usb_video]]
}
set project_file [file join $build_dir pynq_zu_usb_video.xpr]
if {![file exists $project_file]} { error "Run create_pynq_zu_usb_video_project.tcl first" }
open_project $project_file

set bd_name pynq_zu_usb_video
set bd_dir [file join $build_dir pynq_zu_usb_video.srcs sources_1 bd $bd_name]
set existing_bd [get_files -quiet [file join $bd_dir ${bd_name}.bd]]
if {[llength $existing_bd] != 0} { remove_files $existing_bd }
if {[file exists $bd_dir]} { file delete -force $bd_dir }
create_bd_design $bd_name

create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.5 zynq_ultra_ps_e_0
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e -config {apply_board_preset "1"} [get_bd_cells zynq_ultra_ps_e_0]
# USB D+/D- are PS MIO pins (USB0 MIO 52 .. 63; USB1 MIO 64 .. 75), never
# make them external PL ports.  Keep both preset USB host controllers enabled.
# PG201 maps the HP0 FPD interface to configurable S_AXI_GP2.
set_property -dict [list \
 CONFIG.PSU__USB0__PERIPHERAL__ENABLE {1} \
 CONFIG.PSU__USB1__PERIPHERAL__ENABLE {1} \
 CONFIG.PSU__USE__M_AXI_GP0 {1} \
 CONFIG.PSU__USE__M_AXI_GP1 {0} \
 CONFIG.PSU__USE__S_AXI_GP2 {1} \
 CONFIG.PSU__USE__IRQ0 {1} \
 CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {100}] [get_bd_cells zynq_ultra_ps_e_0]

create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 axi_ctrl_smc_0
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {3}] [get_bd_cells axi_ctrl_smc_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 axi_ddr_smc_0
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] [get_bd_cells axi_ddr_smc_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 axi_dma_0
set_property -dict [list \
 CONFIG.c_include_mm2s {1} CONFIG.c_include_s2mm {0} \
 CONFIG.c_include_sg {0} CONFIG.c_m_axis_mm2s_tdata_width {64}] [get_bd_cells axi_dma_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 frame_id_gpio_0
set_property -dict [list CONFIG.C_GPIO_WIDTH {32} CONFIG.C_ALL_OUTPUTS {1}] [get_bd_cells frame_id_gpio_0]
create_bd_cell -type module -reference dual_camera_yolox_axis_top yolox_video_rtl_0
create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 video_irq_or_0
set_property -dict [list CONFIG.C_OPERATION {or} CONFIG.C_SIZE {1}] [get_bd_cells video_irq_or_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 reset_invert_0
set_property -dict [list CONFIG.C_OPERATION {not} CONFIG.C_SIZE {1}] [get_bd_cells reset_invert_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 reset_locked_0
set_property -dict [list CONFIG.CONST_VAL {1} CONFIG.CONST_WIDTH {1}] [get_bd_cells reset_locked_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 proc_sys_reset_0

# AXI-Lite control: Vitis programs DMA, frame ID and the YOLOX mailbox.
connect_bd_intf_net [get_bd_intf_pins zynq_ultra_ps_e_0/M_AXI_HPM0_FPD] [get_bd_intf_pins axi_ctrl_smc_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_ctrl_smc_0/M00_AXI] [get_bd_intf_pins yolox_video_rtl_0/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_ctrl_smc_0/M01_AXI] [get_bd_intf_pins axi_dma_0/S_AXI_LITE]
connect_bd_intf_net [get_bd_intf_pins axi_ctrl_smc_0/M02_AXI] [get_bd_intf_pins frame_id_gpio_0/S_AXI]

# AXI DMA reads the packed UVC frames from PS DDR through HPC0 and sends them
# into the 64-bit PL AXI4-Stream input.  UVC capture itself is a PS driver
# responsibility and is intentionally not modelled as a PL IP core.
connect_bd_intf_net [get_bd_intf_pins axi_dma_0/M_AXI_MM2S] [get_bd_intf_pins axi_ddr_smc_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_ddr_smc_0/M00_AXI] [get_bd_intf_pins zynq_ultra_ps_e_0/S_AXI_HP0_FPD]
connect_bd_intf_net [get_bd_intf_pins axi_dma_0/M_AXIS_MM2S] [get_bd_intf_pins yolox_video_rtl_0/S_AXIS_VIDEO]
connect_bd_net [get_bd_pins frame_id_gpio_0/gpio_io_o] [get_bd_pins yolox_video_rtl_0/stream_frame_id]

# One PL clock domain simplifies the existing RGB feature RTL.  AXI DMA is
# configured only for MM2S because this revision produces feature/IRQ results
# through the existing AXI-Lite mailbox rather than writing an output frame.
connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_clk0] \
 [get_bd_pins zynq_ultra_ps_e_0/maxihpm0_fpd_aclk] \
 [get_bd_pins zynq_ultra_ps_e_0/saxihp0_fpd_aclk] \
 [get_bd_pins axi_ctrl_smc_0/aclk] [get_bd_pins axi_ddr_smc_0/aclk] \
 [get_bd_pins axi_dma_0/s_axi_lite_aclk] [get_bd_pins axi_dma_0/m_axi_mm2s_aclk] [get_bd_pins frame_id_gpio_0/s_axi_aclk] \
 [get_bd_pins yolox_video_rtl_0/clk] [get_bd_pins proc_sys_reset_0/slowest_sync_clk]
connect_bd_net [get_bd_pins zynq_ultra_ps_e_0/pl_resetn0] [get_bd_pins reset_invert_0/Op1]
connect_bd_net [get_bd_pins reset_invert_0/Res] [get_bd_pins proc_sys_reset_0/ext_reset_in]
connect_bd_net [get_bd_pins reset_locked_0/dout] [get_bd_pins proc_sys_reset_0/dcm_locked]
connect_bd_net [get_bd_pins proc_sys_reset_0/peripheral_reset] [get_bd_pins yolox_video_rtl_0/reset]
connect_bd_net [get_bd_pins proc_sys_reset_0/peripheral_aresetn] \
 [get_bd_pins axi_ctrl_smc_0/aresetn] [get_bd_pins axi_ddr_smc_0/aresetn] \
 [get_bd_pins axi_dma_0/axi_resetn] [get_bd_pins yolox_video_rtl_0/s_axi_aresetn]

# Either mailbox or DMA completion/error wakes software; software reads each
# IP's status register to determine and acknowledge the source.
connect_bd_net [get_bd_pins yolox_video_rtl_0/irq] [get_bd_pins video_irq_or_0/Op1]
connect_bd_net [get_bd_pins axi_dma_0/mm2s_introut] [get_bd_pins video_irq_or_0/Op2]
connect_bd_net [get_bd_pins video_irq_or_0/Res] [get_bd_pins zynq_ultra_ps_e_0/pl_ps_irq0]

assign_bd_address
validate_bd_design
save_bd_design
puts "PYNQ_ZU_USB_VIDEO_BD_CREATED=[get_property FILE_NAME [current_bd_design]]"
