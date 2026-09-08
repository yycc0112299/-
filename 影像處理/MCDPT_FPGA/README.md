# MCDPT FPGA / EGo1 / Verilog

This project is an **MCDPT concept simplified FPGA implementation**, not a full
MCDPT CNN/OpenVINO Re-ID port. It preserves cross-frame feature storage,
feature matching and identity continuity. Deep Re-ID is replaced by a
low-resource Verilog-2001 4x4 block-average feature extractor and multi-cycle SAD matcher
suitable for the EGo1 Artix-7.

The deterministic 160x120 4-bit synthetic ROM frames contain a reference person
at (30,25) and the same pattern in Frame B at (70,45). VGA scales pixels 4x to
640x480. The reference/search/tracked boxes are yellow/orange/green and retain
Person ID 1 conceptually. Tracking starts after reset; R15 starts it again.

Verified hardware data was reused from `C:\EGo1_Snake`: part
`xc7a35tcsg324-1`, 100 MHz clock P17, reset R1, button R15 and VGA pins.

Run with Vivado 2020.1 batch mode:

```
C:\Vivado\2020.1\bin\vivado.bat -mode batch -source scripts\run_sim.tcl
C:\Vivado\2020.1\bin\vivado.bat -mode batch -source scripts\build.tcl
```

`scripts/image_to_mem.py` converts later PNG/JPEG input into 160x120 4-bit COE
initialization data; Python performs no tracking inference.

All synthesizable RTL and the tracking testbench are implemented in Verilog;
there are no VHDL design sources in this revision.
