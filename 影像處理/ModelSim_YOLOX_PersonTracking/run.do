onerror {quit -code 1 -force}
if {![file exists work]} {vlib work}
vmap work work
vlog -sv color_feature.v two_camera_top.v tb_two_camera.v
vsim -onfinish stop -voptargs=+acc work.tb_two_camera
log -r /*
if {![batch_mode]} {add wave -r /tb_two_camera/dut/*}
run -all
if {![batch_mode]} {wave zoom full}
