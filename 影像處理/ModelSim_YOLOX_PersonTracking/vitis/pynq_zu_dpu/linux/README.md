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
  --dpu-ip-version 4.0 \
  --vitis-ai-version 2.5 \
  --vivado-version 2022.1 \
  --petalinux-version 2022.1
```

The generated hardware's `component.xml` identifies it as DPUCZDX8G **4.0**.
AMD's compatibility matrix pairs that IP with Vitis AI **2.5** and
Vivado/Vitis/PetaLinux **2022.1**. Vitis AI 3.5's 2023.1 contract applies to
DPUCZDX8G **4.1**, not this bitstream. The present hardware was built with
Vivado 2024.2 and the installed PetaLinux host is 2024.1, neither of which is
the published compatible toolchain for this DPU 4.0 build. Do not infer
runtime compatibility from a successful Vivado implementation. Either rebuild
this IP using the 2.5/2022.1 contract, or first replace it with DPU 4.1 and
then use the 3.5/2023.1 contract.

The preflight requires a compiler route (Docker with Vitis AI or `vai_c_xir`),
PetaLinux and the exact DPU-generated `arch.json`. It intentionally refuses to
guess a fingerprint or compile an `.xmodel` from a board-family JSON. It prints
`PYNQ_ZU_DPU_BUILD_HOST_PASS` only for the compatible build contract; it does
not download software, alter the workstation, build an image or touch the
board.

From the repository's `ModelSim_YOLOX_PersonTracking` root, the tracked helper
below extracts that file from a completed Vivado project:

```sh
python3 fpga/export_pynq_zu_dpu_arch_json.py \
  --build-dir /path/to/PYNQ_ZU_DPU_BUILD_DIR \
  --output /path/to/pynq_zu_dpu_b512_arch.json
```

For the currently generated native B512 hardware it emitted fingerprint
`0x101000016010400`. The output is deliberately outside Git because it is
derived from the local Vivado build; regenerate it after any DPU IP
configuration change. The presence of this architecture file only unlocks the
correct compiler input—it does not resolve the required matching build host or
create a working Linux DPU runtime.

## 2022.1 SDK VART link smoke

The actual DPUCZDX8G 4.0 contract uses the 2022.1 target SDK and Vitis AI
2.5 runtime. Once those assets have been installed into a Linux sysroot,
source the matching SDK environment and run the small cross-link check:

```sh
source /home/petalinux/sdk_2022_1/environment-setup-cortexa72-cortexa53-xilinx-linux
bash build_vart_link_smoke.sh /tmp/vart_link_smoke.elf
readelf -d /tmp/vart_link_smoke.elf | grep NEEDED
```

The expected AArch64 ELF has `libvart-runner.so.2`, `libxir.so.2`, and
`libunilog.so.2` in its dynamic dependencies. This verifies that the
cross-compiler can consume the matching target headers and libraries; it does
not execute VART. `vart_link_smoke.cpp` deliberately supplies a null subgraph
and must never be run on a target. It is not a model test, DPU driver test,
boot-image test, or board-side inference result.
