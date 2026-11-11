# Export the fixed PYNQ-ZU B512 DPU hardware hand-off for Vitis/Linux work.
# Run only after implement_pynq_zu_dpu_b512.tcl has finished successfully.
if {![info exists ::env(PYNQ_ZU_DPU_BUILD_DIR)] || $::env(PYNQ_ZU_DPU_BUILD_DIR) eq ""} {
    error "Set PYNQ_ZU_DPU_BUILD_DIR to the directory used for create_pynq_zu_dpu_bd.tcl"
}
set build_dir [file normalize $::env(PYNQ_ZU_DPU_BUILD_DIR)]
set project_file [file join $build_dir project pynq_zu_dpu.xpr]
if {![file exists $project_file]} { error "Missing DPU project: $project_file" }
open_project $project_file
set status [get_property STATUS [get_runs impl_1]]
if {$status ne "write_bitstream Complete!"} {
    error "Run implement_pynq_zu_dpu_b512.tcl first; impl_1 status is: $status"
}
open_run impl_1
set xsa_file [file join $build_dir pynq_zu_dpu_b512.xsa]
write_hw_platform -fixed -include_bit -force -file $xsa_file
if {![file exists $xsa_file]} { error "DPU XSA export failed: $xsa_file" }
puts "PYNQ_ZU_DPU_B512_XSA_PASS=$xsa_file"
