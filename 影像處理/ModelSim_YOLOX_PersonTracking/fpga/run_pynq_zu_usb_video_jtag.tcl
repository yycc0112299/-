# Temporarily launch the USB-video Vitis smoke ELF through PYNQ-ZU JTAG.
#
# All artifacts are supplied by environment variables so this tracked source
# does not hard-code host paths or include binaries.  JTAG programming is
# volatile: this script does not touch the SD card, QSPI, eMMC, or configuration
# flash.  A power-cycle returns the board to its selected boot source.

proc required_file {name} {
    if {![info exists ::env($name)] || ![file isfile $::env($name)]} {
        error "$name must name an existing external artifact"
    }
    return $::env($name)
}

proc required_value {name} {
    if {![info exists ::env($name)] || $::env($name) eq ""} {
        error "$name must be set"
    }
    return $::env($name)
}

proc enabled {name} {
    return [expr {[info exists ::env($name)] && $::env($name) eq "1"}]
}

set bit [required_file PYNQ_ZU_JTAG_BIT]
set pmufw [required_file PYNQ_ZU_JTAG_PMUFW]
set fsbl [required_file PYNQ_ZU_JTAG_FSBL]
set elf [required_file PYNQ_ZU_JTAG_ELF]
set result_address [required_value PYNQ_ZU_JTAG_RESULT_ADDR]

connect
after 3000
if {![enabled PYNQ_ZU_JTAG_SKIP_RESET]} {
    targets -set -filter {name == "PSU"}
    rst -system
    after 5000
}
if {![enabled PYNQ_ZU_JTAG_SKIP_FPGA]} {
    targets -set -filter {name == "PL"}
    # XSDB reports this target only as generic xczu5_0; keep its device check but
    # bypass only the unavailable silicon-revision metadata check.
    fpga -n -file $bit
}

# Full bare-metal boot requires a downloadable PMU context.  On an already
# SD-booted board, it is valid to preserve the initialized PS/DDR and use the
# explicit skip mode to test just the Vitis A53 control ELF.
if {![enabled PYNQ_ZU_JTAG_SKIP_BOOT]} {
    targets -set -filter {name == "PMU"}
    dow $pmufw
    con
    after 1000
    targets -set -filter {name == "Cortex-A53 #0"}
    stop
    dow $fsbl
    con
    after 10000
}
targets -set -filter {name == "Cortex-A53 #0"}
stop
dow $elf
con
after 3000
stop
puts "PYNQ_ZU_USB_VIDEO_JTAG_RESULT=[mrd $result_address 5]"
puts "PYNQ_ZU_USB_VIDEO_JTAG_LAUNCHED bit=$bit elf=$elf"
