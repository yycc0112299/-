# Finish (or rebuild) the application portion of an existing 2022.1 XSCT
# workspace made by build_vitis_2022.tcl.  Keeping this separate allows a
# platform that has already generated its BSP to be resumed after an IDE
# restart without recreating the XSA platform.
#
# Required environment variable:
#   PYNQ_ZU_VITIS_WORKSPACE  existing workspace containing the platform/app

if {![info exists ::env(PYNQ_ZU_VITIS_WORKSPACE)] ||
    ![file isdirectory $::env(PYNQ_ZU_VITIS_WORKSPACE)]} {
    error "PYNQ_ZU_VITIS_WORKSPACE must name an existing workspace"
}

set workspace [file normalize $::env(PYNQ_ZU_VITIS_WORKSPACE)]
set platform_name pynq_zu_usb_video_platform
set app_name pynq_zu_usb_video_app
set script_dir [file dirname [file normalize [info script]]]
set source_dir [file join $script_dir src]
if {![file isdirectory $source_dir]} {
    error "Missing application source directory: $source_dir"
}
if {![file isdirectory [file join $workspace $app_name]]} {
    error "Expected application project is missing: $app_name"
}
if {![file isdirectory [file join $workspace $platform_name]]} {
    error "Expected platform project is missing: $platform_name"
}

setws $workspace
# A forced close of the Vitis service may leave the files present but omit
# their entries from the fresh Eclipse workspace metadata.  Re-import both
# projects before asking the service to build the application.
importprojects -path [file join $workspace $platform_name] -silent
importprojects -path [file join $workspace $app_name] -silent
importsources -name $app_name -path $source_dir
app build -name $app_name

set elf_candidates [glob -nocomplain [file join $workspace $app_name Debug *.elf]]
if {[llength $elf_candidates] != 1} {
    error "Expected exactly one Debug ELF, found: $elf_candidates"
}
puts "PYNQ_ZU_USB_VIDEO_VITIS_2022_ELF=[lindex $elf_candidates 0]"
exit 0
