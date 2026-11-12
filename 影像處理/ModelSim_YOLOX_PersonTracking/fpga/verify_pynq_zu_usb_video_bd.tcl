# Read-only Vivado verification for the existing PYNQ-ZU USB-video BD.
# Requires PYNQ_ZU_BUILD_DIR to point to a completed local project directory.

if {![info exists ::env(PYNQ_ZU_BUILD_DIR)] || $::env(PYNQ_ZU_BUILD_DIR) eq ""} {
    error "Set PYNQ_ZU_BUILD_DIR to the existing pynq_zu_usb_video build directory"
}
set build_dir [file normalize $::env(PYNQ_ZU_BUILD_DIR)]
set project_file [file join $build_dir pynq_zu_usb_video.xpr]
set bd_file [file join $build_dir pynq_zu_usb_video.srcs sources_1 bd pynq_zu_usb_video pynq_zu_usb_video.bd]
if {![file exists $project_file] || ![file exists $bd_file]} {
    error "Missing existing project or Block Design under $build_dir"
}

open_project $project_file
open_bd_design $bd_file
validate_bd_design

proc require_address {instance expected} {
    set address_space [get_bd_addr_spaces zynq_ultra_ps_e_0/Data]
    set segments [get_bd_addr_segs -quiet -of_objects $address_space -filter "NAME =~ *${instance}*"]
    if {[llength $segments] != 1} {
        error "Expected exactly one PS address segment for $instance, found [llength $segments]"
    }
    set actual [format "0x%08X" [get_property OFFSET [lindex $segments 0]]]
    if {$actual ne $expected} {
        error "$instance has $actual, expected $expected"
    }
    puts "PYNQ_ZU_USB_VIDEO_BD_ADDRESS_${instance}=$actual"
}

require_address axi_dma_0 0xA0000000
require_address frame_id_gpio_0 0xA0010000
require_address yolox_video_rtl_0 0xA0020000
puts "PYNQ_ZU_USB_VIDEO_BD_VERIFY_PASS=$bd_file"
