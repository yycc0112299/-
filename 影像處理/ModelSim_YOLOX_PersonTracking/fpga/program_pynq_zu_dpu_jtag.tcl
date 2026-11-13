# Volatile-only programming of the current PYNQ-ZU DPU bitstream through JTAG.
#
# Required environment:
#   PYNQ_ZU_DPU_JTAG_BIT  absolute path to the implemented B512 .bit file
#
# This intentionally does not program configuration memory, reset the PS, load
# a bare-metal application, or modify an SD card.  A power cycle clears this
# PL configuration.  Linux/VART/YOLOv8 verification still requires the
# matching SD image because this script programs PL only.

if {![info exists ::env(PYNQ_ZU_DPU_JTAG_BIT)] ||
    ![file isfile $::env(PYNQ_ZU_DPU_JTAG_BIT)]} {
    error "PYNQ_ZU_DPU_JTAG_BIT must name an existing B512 bitstream"
}
set bit [file normalize $::env(PYNQ_ZU_DPU_JTAG_BIT)]

open_hw_manager
connect_hw_server
set targets [get_hw_targets]
if {[llength $targets] != 1} {
    error "Expected exactly one local JTAG target; found [llength $targets]"
}
set target [lindex $targets 0]
open_hw_target $target
set device [lindex [get_hw_devices xczu5_0] 0]
if {$device eq ""} {
    error "Expected the PYNQ-ZU PL device xczu5_0 on JTAG target $target"
}

set_property PROGRAM.FILE $bit $device
program_hw_devices $device
refresh_hw_device $device
set eos [get_property REGISTER.CONFIG_STATUS.BIT04_END_OF_STARTUP_\(EOS\)_STATUS $device]
if {$eos ne "1"} {
    error "Bitstream did not reach end-of-startup; EOS status is '$eos'"
}
puts "PYNQ_ZU_DPU_JTAG_PROGRAM_PASS bit=$bit device=[get_property NAME $device] eos=$eos"

close_hw_target $target
disconnect_hw_server
close_hw_manager
