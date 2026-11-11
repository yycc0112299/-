# Package AMD's DPUCZDX8G sources as a reusable IP Catalog core for PYNQ-ZU.
#
# Prerequisite: download/extract AMD's official DPUCZDX8G distribution and set
# DPUCZDX8G_HOME to its top-level directory. This script copies it into the
# disposable build tree before inserting the B512 configuration, so it never
# changes the vendor extraction. The result is a packaged IP, not proof that
# it fits/runs on xczu5eg or that Linux/VART is installed.

set script_dir [file dirname [file normalize [info script]]]
if {![info exists ::env(DPUCZDX8G_HOME)] || $::env(DPUCZDX8G_HOME) eq ""} {
    error "Set DPUCZDX8G_HOME to AMD DPUCZDX8G source root before packaging"
}
set vendor_root [file normalize $::env(DPUCZDX8G_HOME)]
if {![file exists [file join $vendor_root dpu_ip Vitis dpu hdl DPUCZDX8G.v]]} {
    error "DPUCZDX8G_HOME does not contain dpu_ip/Vitis/dpu/hdl/DPUCZDX8G.v"
}
if {[info exists ::env(PYNQ_ZU_DPU_BUILD_DIR)] && $::env(PYNQ_ZU_DPU_BUILD_DIR) ne ""} {
    set build_dir [file normalize $::env(PYNQ_ZU_DPU_BUILD_DIR)]
} else {
    set build_dir [file normalize [file join $::env(TEMP) pynq_zu_dpu_b512]]
}
set config_file [file join $script_dir dpu_config_pynq_zu_b512.vh]
if {![file exists $config_file]} { error "Missing tracked B512 DPU config: $config_file" }
file mkdir $build_dir

# Isolate third-party inputs and generated IP below the explicit build root.
set vendor_stage_parent [file join $build_dir vendor_stage]
set vendor_stage [file join $vendor_stage_parent DPUCZDX8G]
set ip_repo [file join $build_dir ip_repo]
if {[file exists $vendor_stage_parent]} { file delete -force $vendor_stage_parent }
if {[file exists $ip_repo]} { file delete -force $ip_repo }
file mkdir $vendor_stage_parent
file copy -force $vendor_root $vendor_stage_parent
if {![file exists $vendor_stage]} {
    # Permit a source directory whose leaf name is not DPUCZDX8G.
    file mkdir $vendor_stage
    foreach source [glob -nocomplain -directory $vendor_root *] {
        file copy -force $source $vendor_stage
    }
}
file copy -force $config_file [file join $vendor_stage prj Vitis dpu_conf.vh]

# Reuse AMD's IP packager with its source tree staged above. The AMD packager
# imports all protected HDL, XDC and Tcl metadata into an RTLKernel IP.
set old_pwd [pwd]
cd [file join $vendor_stage prj Vitis]
set ::env(TRD_PATH) $vendor_stage
set suffix pynq_zu_b512
# The 2022.1 package script removes a generated page named "Page 0". Vivado
# 2024.2 may not create that page, which makes `ipgui::remove_page` fail even
# though IP packaging has otherwise succeeded. Patch only the staged copy;
# AMD's original extraction remains untouched.
set amd_packager [file join $vendor_stage prj Vitis scripts package_dpu_kernel.tcl]
set compat_packager [file join [pwd] package_dpu_kernel_2024_compat.tcl]
set input [open $amd_packager r]
set packager_text [read $input]
close $input
regsub -all {ipgui::remove_page -component \[ipx::current_core\] \[bip_pagespec "Page 0"\]} \
    $packager_text {# Vivado 2024.2 has no default Page 0 to remove.} packager_text
# Vivado 2024.2 no longer exposes the imported DPU fingerprint *.ttcl files
# through these legacy file-group queries. They are metadata, not synthesizable
# RTL; leaving the legacy `set_property` calls would fail on an empty object.
regsub -all {set_property type ttcl \[ipx::get_files src/\*\.ttcl[^\n]*\]} \
    $packager_text {# Legacy TTCL metadata is intentionally omitted on Vivado 2024.2.} packager_text
# These helpers target the legacy Vitis kernel wrapper clock name `aclk`. The
# standalone DPUCZDX8G core exports `dpu_clk`/`dpu_clk_dsp`, already inferred
# by Vivado, so invoking the helpers on 2024.2 makes an empty-object error.
regsub -all {bip_set_bus_interfaces} $packager_text \
    {# DPU native AXI bus interfaces were inferred by Vivado.} packager_text
regsub -all {bip_set_bus_enablement_dependency} $packager_text \
    {# No legacy XRT bus-enablement dependencies are needed for BD use.} packager_text
regsub -all {ipx::infer_bus_interface ap_clk_2[^\n]*} $packager_text \
    {# DPU native clocks are inferred from the protected top-level HDL.} packager_text
regsub -all {ipx::infer_bus_interface ap_rst_n_2[^\n]*} $packager_text \
    {# DPU native reset is inferred from the protected top-level HDL.} packager_text
set output [open $compat_packager w]
puts -nonewline $output $packager_text
close $output
source -notrace $compat_packager
set packaged_ip [file join [pwd] packaged_kernel_${suffix}]
cd $old_pwd
if {![file exists [file join $packaged_ip component.xml]]} {
    error "AMD DPU IP packaging did not produce component.xml at $packaged_ip"
}
file mkdir $ip_repo
file copy -force $packaged_ip $ip_repo
puts "PYNQ_ZU_DPU_IP_REPO=[file join $ip_repo [file tail $packaged_ip]]"
puts "PYNQ_ZU_DPU_IP_VLNV=xilinx.com:RTLKernel:dpu_wrapper:1.0"
