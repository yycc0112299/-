# PYNQ-ZU two-board Linux, DPU, and camera architecture

Date: 2026-11-11

## Chosen target architecture

Each PYNQ-ZU board owns exactly one Logitech C270 on its PS USB host port.
The Linux UVC driver exposes that camera as one V4L2 capture node.  The A53
Linux application performs capture, pre-processing, DPU inference, and result
publication.  A Wi-Fi link exchanges compact detection/tracking messages,
not a second USB-camera stream as a prerequisite for first bring-up.

```
C270 -> PS USB -> Linux UVC/V4L2 -> A53 preprocessing -> DPU -> detections
 board A                                                        | Wi-Fi JSON
                                                                v
 board B <- C270 -> PS USB -> Linux UVC/V4L2 -> A53 -> DPU -> fusion/display
```

Raw/encoded video forwarding is a later optional feature. It must be versioned
as a separate protocol because it has much higher Wi-Fi bandwidth and latency
requirements than detections.

## Vivado responsibility (hardware deliverable)

The Vivado Block Design must retain the Zynq UltraScale+ processing system,
DDR, PS USB MIO, clocks/resets, and interrupt wiring. A DPU integration is an
additional PL subsystem, not a replacement for the kernel UVC driver. The
hardware work required before DPU inference is claimed is:

1. Obtain a DPUCZDX8G configuration that fits the actual `xczu5eg` PYNQ-ZU
   resources and a matching Vitis AI release.
2. Add the DPU IP and its AXI master/control/interrupt connections to the PS
   DDR/HP interfaces in a new, reproducible Vivado script and export its XSA.
3. Generate a matching device tree and Linux image with DPU driver, reserved
   CMA memory, and VART runtime support. The current PYNQ v3.1.1 image has
   none of those components.
4. Run implementation and timing checks, then prove the DPU device and VART
   are present on each board before model deployment.

The existing AXI-DMA + custom packed-stream path remains a verified synthetic
frame bring-up asset. It is not a DPU integration and must not be represented
as one.

## Vitis/Linux responsibility (software deliverable)

The Linux application owns V4L2 negotiation, buffer ownership, model input
preprocess/quantization, VART job submission, output post-processing (NMS),
and the Wi-Fi protocol. Vitis standalone is still useful for low-level DMA/PL
diagnostics but has no UVC host middleware, so it cannot replace Linux for the
C270 path.

Model deployment sequence:

1. Select **YOLOv8** as the new detector target. The existing project contains
   YOLOX Python assets; it is not correct to call them YOLOv8 interchangeably.
2. Export a fixed-input ONNX model, quantize it to INT8 with the Vitis AI flow,
   and compile it against the *exact* DPU `arch.json` generated for this
   hardware. The result is a DPU-specific `.xmodel`, not a generic ONNX file.
3. Keep the existing Python/YOLOX application boundary by defining a detector
   adapter with one output schema (class, confidence, bounding box, frame ID,
   timestamp). Its implementation can initially be CPU YOLOv8 and later VART;
   downstream tracking and Wi-Fi code then does not depend on the accelerator.
4. Validate single-board, single-camera capture and DPU inference first;
   then validate two boards and message exchange; finally validate fusion.

## Verified facts and current blockers

- One PYNQ-ZU running PYNQ Linux has been reached by SSH and has two C270s as
  V4L2 capture nodes. Vitis-built AArch64 code successfully ran on it.
- The current board's two C270s share USB topology `1-1.3`/`1-1.4`. Even after
  both negotiated 320×240 at 10 FPS, the second stream failed at
  `VIDIOC_STREAMON` with kernel USB bandwidth `ENOSPC`. A 320×240 MJPEG
  stream-only test failed at the same point. This is real board evidence, not
  a software assertion.
- The current PYNQ image has no `xdputil`, VART Python module, or `/dev/dpu`.
  Thus DPU hardware/runtime/model inference is not yet installed or verified.
- AMD documents DPUCZDX8G as the configurable DPU family for Zynq UltraScale+
  MPSoCs; it requires matching DPU hardware, driver/runtime, compiler target,
  and model artifacts. Board fit and the complete image build remain open.

## Immediate acceptance gates

1. Board A: single C270 stays streaming for a sustained test and produces
   frames with recorded resolution/FPS.
2. Board B: repeat the same test independently.
3. Wi-Fi: both Linux hosts exchange versioned detection messages and tolerate
   a peer restart/disconnect.
4. DPU: Vivado implementation succeeds; Linux exposes DPU/VART; one known
   quantized `.xmodel` returns a repeatable result.
5. YOLOv8: a person image yields detections through the adapter, then the same
   output schema is consumed by the existing tracker/fusion code.

## References

- AMD [DPUCZDX8G system-integration guidance](https://xilinx.github.io/Vitis-AI/3.5/html/docs/workflow-system-integration)
  describes the runtime/CMA requirements for the Zynq UltraScale+ DPU.
- AMD [Vitis AI workflow overview](https://xilinx.github.io/Vitis-AI/3.5/html/docs/workflow.html)
  describes the supported platform workflow and version considerations.
- AMD [DPUCZDX8G product guide](https://docs.amd.com/r/4.0-English/pg338-dpu/Customizing-and-Generating-the-Core-in-the-Vitis-IDE)
  describes DPU configuration and PS DDR connectivity.

## 2026-11-11: native B512 DPU Vivado feasibility result

The repository now has a reproducible native-DPU Vivado flow under
`影像處理/ModelSim_YOLOX_PersonTracking/fpga/`. Set `DPUCZDX8G_HOME` to AMD's
extracted official DPUCZDX8G source root and, optionally,
`PYNQ_ZU_DPU_BUILD_DIR` to a short writable ASCII path. Run
`create_pynq_zu_dpu_bd.tcl`, `synthesize_pynq_zu_dpu_b512.tcl`, then
`implement_pynq_zu_dpu_b512.tcl` with Vivado 2024.2 batch mode.

`export_pynq_zu_dpu_xsa.tcl` is the next reproducible handoff step. It opens
only a `write_bitstream Complete!` implementation run and writes a fixed XSA
with the bitstream. It was run successfully: the 2,586,044-byte XSA contains
the DPU `.hwh`, bitstream, PS init files, `sysdef.xml`, and XSA metadata. The
archive is deliberately a local build artifact; the tracked Tcl reconstructs
it on another development machine.

The generated `pynq_zu_dpu` Block Design uses native
`xilinx.com:ip:dpuczdx8g:4.0`, one B512 core, PS USB0/USB1 on MIO, A53 HPM0
to the DPU AXI-Lite control slave, HP0/HP1 for 128-bit DPU data, HP2 for DPU
instructions, PL1=150 MHz DPU/DDR traffic, a generated 300 MHz DPU 2x clock,
and `dpu0_interrupt` to PS IRQ0. It was validated with
`validate_bd_design` and fully implemented for `xczu5eg-sfvc784-1-e`.

Actual Vivado 2024.2 result: bitstream generation completed with 0 errors and
0 critical warnings; all user timing constraints are met (WNS +0.966 ns,
WHS +0.010 ns); 68,180 of 68,180 routable nets were fully routed with 0 route
errors. Implemented utilization is 32,022 LUTs (27.34%), 41,567 registers
(17.75%), 72 BRAM tiles (50.00%), and 134 DSPs (10.74%). The generated
7,797,815-byte bitstream is intentionally not checked into Git because all
tracked Tcl sources rebuild it.

This is not yet a claim of DPU inference on the board. The current PYNQ Linux
image still lacks the matching DPU driver, VART, CMA/device-tree integration,
an `arch.json` matching this configuration, a compiled INT8 `.xmodel`, and an
on-board `xdputil`/VART execution test. USB UVC remains PS USB -> Linux V4L2
-> DDR before a VART application submits a tensor to the DPU.

The XSA was also consumed by complete Vitis Embedded 2024.2. The tracked
`vitis/pynq_zu_dpu/build_vitis_dpu_platform.py` produced SDT, A53 standalone
BSP, ZynqMP FSBL, and an exported XPFM. Its generated `xparameters.h` names
the DPU AXI-Lite window at `0x400000000`. This proves the Vivado-to-Vitis
hardware handoff, not native-DPU runtime support: VART needs the matching
Linux image and DPU driver rather than an invented bare-metal register API.
