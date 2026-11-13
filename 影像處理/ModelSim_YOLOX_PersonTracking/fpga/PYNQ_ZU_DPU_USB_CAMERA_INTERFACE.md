# PYNQ-ZU DPU + USB camera interface map

This document applies to the current first-stage hardware: one PYNQ-ZU board
and one USB UVC camera. It is deliberately not a MIPI/CSI or parallel-camera
pinout.

## Electrical and software ownership

| Path | Owner | Evidence in this repository | What it does |
|---|---|---|---|
| USB camera D+/D- and VBUS | PYNQ-ZU board routing and Zynq PS MIO | Board preset plus `CONFIG.PSU__USB0__PERIPHERAL__ENABLE {1}` and `CONFIG.PSU__USB1__PERIPHERAL__ENABLE {1}` in `create_pynq_zu_dpu_bd.tcl` | Enumerates the UVC camera; these wires are **not** PL fabric ports. |
| USB protocol / frames | PetaLinux PS USB DWC3 and UVC/V4L2 drivers | DWC3 dual-role, V4L2 and UVC kernel selections staged by `prepare_dpu_4_0_petalinux_project.py` | Exposes a camera as `/dev/video*`; OpenCV reads frames through V4L2. |
| Frame buffers | PS DDR | Linux V4L2 buffers and DPU HP AXI interfaces | The camera driver writes frame buffers in DDR; the DPU runtime uses its own tensor buffers in DDR. |
| DPU register control | A53 PS → `M_AXI_HPM0_FPD` → SmartConnect → DPU `S_AXI` | `create_pynq_zu_dpu_bd.tcl` | VART/GraphRunner programs the DPU. The final AXI-Lite address is assigned by Vivado and emitted by `PYNQ_ZU_DPU_CONTROL_ADDRESS`. |
| DPU tensors/instructions | DPU → SmartConnect/HP DDR ports | DPU `DATA0`→`HP0`, `DATA1`→`HP1`, `INSTR`→`HP2` connections | Lets the DPU fetch graph instructions, weights and tensors from PS DDR. |
| Completion interrupt | DPU `dpu0_interrupt` → PS `pl_ps_irq0` | `create_pynq_zu_dpu_bd.tcl` | Lets the Linux DPU driver observe job completion. |
| YOLOv8 graph execution | Linux VART/XIR/GraphRunner | `pynq_yolov8_dpu_inference.py` and `assets/yolov8_vart.py` | Runs the original compiled B512 `.xmodel`; it is not a CPU ONNX replacement. |

## Why there are no camera PL pin constraints

The C270-class camera is a USB UVC device. Its high-speed USB signals terminate
at the Zynq PS USB controller through board-defined MIO routing. Therefore the
correct Vivado action is to retain USB0/USB1 in the PS configuration; it would
be incorrect to create arbitrary FPGA top-level pins or AXI video IP for this
camera. The Block Design comment and static contract explicitly require this
PS-MIO path.

If the project later uses a MIPI CSI-2 camera, that is a different hardware
design: it needs a compatible board connector, MIPI D-PHY/CSI receiver IP,
video pipeline, clock/reset constraints and an XDC pin assignment. Those pins
must not be inferred from the current USB camera design.

## Vivado, Vitis and Linux handoff

1. Vivado creates the PS/DPU clocks, resets, AXI memory/control paths and DPU
   interrupt; it exports the XSA.
2. Vitis 2022.1 consumes that XSA to create the platform handoff. It does not
   supply a bare-metal camera/DPU application because this workload requires
   Linux V4L2 plus VART/GraphRunner.
3. PetaLinux imports the same XSA for the DPU device tree and packages the
   DPU driver, VART/XIR, UVC/V4L2 and target Python runtime into the SD image.
4. At runtime OpenCV reads `/dev/video*`; GraphRunner submits tensors to DPU;
   the tracker consumes returned person detections.

## Verification boundary

The Vivado DPU bitstream was downloaded successfully over JTAG, and the
matching SD image booted to its UART login prompt. This establishes the
hardware handoff and initial boot only. The corrected image still needs to be
written to an SD card and booted before claiming Python imports, UVC frames,
DPU YOLOv8 inference or person tracking. A second PYNQ-ZU and authorized
Wi-Fi network remain required for the later two-board metadata exchange.
