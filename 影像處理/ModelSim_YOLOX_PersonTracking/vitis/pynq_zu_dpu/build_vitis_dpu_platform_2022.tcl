# Create a PYNQ-ZU DPU B512 A53 standalone platform with Vitis 2022.1 XSCT.
#
# This verifies the Vivado 2022.1 XSA handoff only.  It does not create a DPU
# inference application: DPU execution belongs to the matching PetaLinux
# driver/VART/GraphRunner image, not to a bare-metal control ELF.
#
# Required:
#   PYNQ_ZU_DPU_XSA              absolute path to pynq_zu_dpu_b512.xsa
# Optional:
#   PYNQ_ZU_DPU_VITIS_WORKSPACE  new and otherwise non-existent short path

proc required_xsa {} {
    if {![info exists ::env(PYNQ_ZU_DPU_XSA)] ||
        ![file isfile $::env(PYNQ_ZU_DPU_XSA)]} {
        error "PYNQ_ZU_DPU_XSA must name an existing XSA file"
    }
    return [file normalize $::env(PYNQ_ZU_DPU_XSA)]
}

set xsa [required_xsa]
if {[info exists ::env(PYNQ_ZU_DPU_VITIS_WORKSPACE)]} {
    set workspace [file normalize $::env(PYNQ_ZU_DPU_VITIS_WORKSPACE)]
} else {
    set workspace "C:/pynq_vitis_dpu_2022"
}
if {[file exists $workspace]} {
    error "Workspace must not already exist: $workspace"
}

file mkdir $workspace
setws $workspace
set platform_name pynq_zu_dpu_platform
platform create -name $platform_name -hw $xsa -proc psu_cortexa53_0 -os standalone
platform generate

set platform_dir [file join $workspace $platform_name]
set xpfm_file [file join $platform_dir export $platform_name "${platform_name}.xpfm"]
if {![file isfile $xpfm_file]} {
    error "Vitis 2022.1 did not export the expected XPFM: $xpfm_file"
}
puts "PYNQ_ZU_DPU_VITIS_2022_XPFM=$xpfm_file"
exit 0
