# Build the PYNQ-ZU USB-video A53 standalone control ELF with Vitis 2022.1 XSCT.
#
# Required environment variables:
#   PYNQ_ZU_USB_VIDEO_XSA        absolute path to pynq_zu_usb_video.xsa
# Optional environment variables:
#   PYNQ_ZU_VITIS_WORKSPACE      a new, short, otherwise non-existent directory
#                                (default C:/pynq_vitis_usb_video_2022)
#
# Example (PowerShell):
#   $env:PYNQ_ZU_USB_VIDEO_XSA = 'C:\build\pynq_zu_usb_video.xsa'
#   C:\Xilinx\Vivado\2022.1\Vitis\2022.1\bin\xsct.bat .\build_vitis_2022.tcl

proc required_xsa {} {
    if {![info exists ::env(PYNQ_ZU_USB_VIDEO_XSA)] ||
        ![file isfile $::env(PYNQ_ZU_USB_VIDEO_XSA)]} {
        error "PYNQ_ZU_USB_VIDEO_XSA must name an existing XSA file"
    }
    return [file normalize $::env(PYNQ_ZU_USB_VIDEO_XSA)]
}

set xsa [required_xsa]
if {[info exists ::env(PYNQ_ZU_VITIS_WORKSPACE)]} {
    set workspace [file normalize $::env(PYNQ_ZU_VITIS_WORKSPACE)]
} else {
    set workspace "C:/pynq_vitis_usb_video_2022"
}
if {[file exists $workspace]} {
    error "Workspace must not already exist: $workspace"
}

set script_dir [file dirname [file normalize [info script]]]
set source_dir [file join $script_dir src]
if {![file isdirectory $source_dir]} {
    error "Missing application source directory: $source_dir"
}

# Keep this workspace independent of the tracked repository and of any 2024.x
# Vitis workspace.  XSCT's platform/app project model is the 2022.1 flow.
file mkdir $workspace
setws $workspace

set platform_name pynq_zu_usb_video_platform
set domain_name standalone_domain
set app_name pynq_zu_usb_video_app

platform create -name $platform_name -hw $xsa -proc psu_cortexa53_0 -os standalone
platform generate
app create -name $app_name -platform $platform_name -domain $domain_name \
    -template "Empty Application"
importsources -name $app_name -path $source_dir
app build -name $app_name

set elf_candidates [glob -nocomplain [file join $workspace $app_name Debug *.elf]]
if {[llength $elf_candidates] != 1} {
    error "Expected exactly one Debug ELF, found: $elf_candidates"
}
puts "PYNQ_ZU_USB_VIDEO_VITIS_2022_ELF=[lindex $elf_candidates 0]"
exit 0
