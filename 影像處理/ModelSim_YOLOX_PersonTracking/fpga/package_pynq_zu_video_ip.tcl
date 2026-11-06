# Package the staged camera DMA/YOLOX RTL as a reusable IP Catalog core.
# This avoids Vivado's fragile module-reference GUI cache on Windows.
if {![info exists ::env(PYNQ_ZU_BUILD_DIR)] || $::env(PYNQ_ZU_BUILD_DIR) eq ""} {
 error "Set PYNQ_ZU_BUILD_DIR before packaging the video RTL"
}
set build_dir [file normalize $::env(PYNQ_ZU_BUILD_DIR)]
set rtl_dir [file join $build_dir rtl_src]
set ip_root [file join $build_dir ip_repo dual_camera_yolox_axis]
set pack_project [file join $build_dir ip_pack_project]
foreach required [list dual_camera_yolox_axis_top.v axis_dual_rgb_stream_adapter.v dual_camera_yolox_axilite_top.v] {
 if {![file exists [file join $rtl_dir $required]]} { error "Missing staged RTL: $required" }
}
create_project -force pynq_zu_video_ip $pack_project -part xczu5eg-sfvc784-1-e
add_files [glob -nocomplain [file join $rtl_dir *.v]]
set_property top dual_camera_yolox_axis_top [current_fileset]
update_compile_order -fileset sources_1
ipx::package_project -root_dir $ip_root -vendor project.local -library video -taxonomy /UserIP -import_files
set core [ipx::current_core]
set_property name dual_camera_yolox_axis $core
set_property version 1.0 $core
set_property display_name {Dual Camera YOLOX AXI Stream} $core
set_property description {DDR DMA-fed dual USB camera RGB stream processor} $core
ipx::save_core $core
puts "PYNQ_ZU_VIDEO_IP_REPO=[file join $build_dir ip_repo]"
