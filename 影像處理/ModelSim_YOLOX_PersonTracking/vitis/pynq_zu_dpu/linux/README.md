# PYNQ-ZU DPU Linux runtime gate

The native DPU B512 bitstream and XSA are deliberately **not** deployed to the
current PYNQ SD image yet.  That image was inspected on hardware and lacks the
DPU device, DPU driver and VART.  Programming this bitstream without the
matching Linux description/runtime would not prove inference and may leave the
running image unable to use the PL.

## Required matching Linux image

Build the boot image from the same `pynq_zu_dpu_b512.xsa` exported by
`fpga/export_pynq_zu_dpu_xsa.tcl`.  The image must contain all of these:

1. the generated PL device tree node whose `compatible` is
   `xlnx,dpuczdx8g-4.0` and whose address/IRQ/clocks originate from the XSA;
2. a Linux DPU driver that explicitly supports that compatible string;
3. enough CMA contiguous memory for DPU buffers;
4. mutually compatible VART, XIR, XRT and DPU driver packages; and
5. an INT8 B512-matched `.xmodel` compiled using the DPU-specific `arch.json`.

The official AMD DPUCZDX8G 4.0 source includes a 2022.1 ZCU102 reference
PetaLinux project.  Its kernel patch only adds the `4.0` compatible string to
`drivers/misc/xlnx_dpu.c`; it is evidence of the required driver contract, not
a PYNQ-ZU Linux image or a safe patch for the PYNQ 3.1.1 kernel.  Its VART 2.5
recipe also depends on XIR, target-factory and (for the Vitis flow) XRT.  Do
not copy ZCU102 device-tree addresses, boot files, or prebuilt libraries into
this project.

The available Windows host has Embedded Vitis 2024.2 but no PetaLinux
installation.  A matching image therefore remains an explicit build/deployment
task on a supported PetaLinux host; it is not silently substituted with the
existing PYNQ SD image.

## Board-side acceptance test

Copy `verify_dpu_runtime.py` and the compiled model to the board after it boots
the matching image, then run:

```sh
python3 verify_dpu_runtime.py --xmodel /opt/models/yolov8_person.xmodel --require-camera
```

It is read-only: it searches the live device tree for the exact DPU compatible
string, checks `/dev/dpu*`, CMA, Python `vart`/`xir`, `xdputil query`, optional
model file and UVC camera nodes.  It prints JSON followed by
`PYNQ_ZU_DPU_LINUX_RUNTIME_PASS` only when each requested prerequisite exists.
Passing this gate still does not replace an end-to-end camera inference test;
the next test must run VART on a frame and validate a person-detection packet.

## Build-host gate and version contract

Before creating the matching image or compiling YOLOv8, run the host-side,
read-only gate:

```sh
python3 preflight_dpu_build_host.py \
  --arch-json /path/to/the/exact/DPU/arch.json \
  --vitis-ai-version 3.5 \
  --vivado-version 2024.1 \
  --petalinux-version 2024.1
```

The Vitis-AI `v4.0` release notes state that the DPU IP in that branch and
Vitis AI 3.5 are verified with Vivado, Vitis and PetaLinux **2024.1**. The
present hardware was successfully built with Vivado 2024.2, but that is not
the published compatible toolchain for this DPU Linux path. Do not infer
runtime compatibility from a successful Vivado implementation. Rebuild the
DPU/XSA on the 2024.1 toolchain before making a deployable Linux image.

The preflight requires a compiler route (Docker with Vitis AI or `vai_c_xir`),
PetaLinux and the exact DPU-generated `arch.json`. It intentionally refuses to
guess a fingerprint or compile an `.xmodel` from a board-family JSON. It prints
`PYNQ_ZU_DPU_BUILD_HOST_PASS` only for the compatible build contract; it does
not download software, alter the workstation, build an image or touch the
board.
