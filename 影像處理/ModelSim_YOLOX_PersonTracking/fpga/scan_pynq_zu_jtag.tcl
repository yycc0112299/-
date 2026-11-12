# Read-only PYNQ-ZU JTAG discovery through Vivado Hardware Manager.
#
# This script opens the local hardware server and emits all known target and
# device properties.  It deliberately has no program/reset/configuration
# command, so it is safe to run while diagnosing USB/JTAG transport.

open_hw_manager
connect_hw_server
foreach target [get_hw_targets] {
    puts "PYNQ_ZU_JTAG_TARGET=[get_property NAME $target]"
    puts "PYNQ_ZU_JTAG_TARGET_PROPERTIES=[report_property -return_string $target]"
    open_hw_target $target
    foreach device [get_hw_devices] {
        puts "PYNQ_ZU_JTAG_DEVICE=[get_property NAME $device]"
        puts "PYNQ_ZU_JTAG_DEVICE_PROPERTIES=[report_property -return_string $device]"
    }
    close_hw_target $target
}
disconnect_hw_server
close_hw_manager
puts "PYNQ_ZU_JTAG_SCAN_COMPLETE"
