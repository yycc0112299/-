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
6. Python 3, NumPy and Python OpenCV when using the tracked Python
   GraphRunner/camera pipeline.

The official AMD DPUCZDX8G 4.0 source includes a 2022.1 ZCU102 reference
PetaLinux project.  Its kernel patch only adds the `4.0` compatible string to
`drivers/misc/xlnx_dpu.c`; it is evidence of the required driver contract, not
a PYNQ-ZU Linux image or a safe patch for the PYNQ 3.1.1 kernel.  Its VART 2.5
recipe also depends on XIR, target-factory and (for the Vitis flow) XRT.  Do
not copy ZCU102 device-tree addresses, boot files, or prebuilt libraries into
this project.

The Windows host now has usable Vivado/Vitis and PetaLinux **2022.1**. The
DPU B512 XSA was built with that version and the external matching PetaLinux
project has produced `BOOT.BIN` and `petalinux-sdimage.wic`. The current
PYNQ 2024.1 SD card remains a different, incompatible image; no generated
artifact is silently substituted onto that card.

## Board-side acceptance test

Copy `verify_dpu_runtime.py` and the compiled model to the board after it boots
the matching image, then run:

```sh
python3 verify_dpu_runtime.py --xmodel /opt/models/yolov8n_b512.xmodel --require-camera
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
  --petalinux-version 2022.1 \
  --petalinux-root /path/to/petalinux/2022.1
```

The generated hardware's `component.xml` identifies it as DPUCZDX8G **4.0**.
AMD's compatibility matrix pairs that IP with Vitis AI **2.5** and
Vivado/Vitis/PetaLinux **2022.1**. Vitis AI 3.5's 2023.1 contract applies to
DPUCZDX8G **4.1**, not this bitstream. The present hardware is now built with
Vivado 2022.1; the remaining toolchain mismatch is the installed PetaLinux
2024.1 host. Do not infer Linux runtime compatibility from a successful Vivado
implementation. Either use a 2022.1 PetaLinux host for this 4.0 IP, or first
replace it with DPU 4.1 and then use the 3.5/2023.1 contract.

The preflight requires the exact local Docker compiler image for the selected
DPU contract (DPU 4.0: `xilinx/vitis-ai:2.5.0`) or `vai_c_xir`, a PetaLinux
installation and the exact DPU-generated `arch.json`. When `--petalinux-root`
is supplied, it reads `PETALINUX_VER` from that installation's `settings.sh`
instead of trusting a claimed version. It intentionally refuses to guess a
fingerprint or compile an `.xmodel` from a board-family JSON. It prints
`PYNQ_ZU_DPU_BUILD_HOST_PASS` only for the compatible build contract; it does
not download software, alter the workstation, build an image or touch the
board.

## Stage the official 2022.1 DPU additions

After installing PetaLinux **2022.1** and creating/configuring an external
project from the exact B512 XSA, stage only the official DPU 4.0 additions:

```sh
python3 prepare_dpu_4_0_petalinux_project.py \
  --project /work/pynq_zu_dpu_2022_1 \
  --petalinux-root /opt/petalinux/2022.1 \
  --official-meta-user /external/DPUCZDX8G/prj/Vivado/xilinx_zcu102_bsp/project-spec/meta-user \
  --xmodel /external/yolov8n_b512.xmodel \
  --runtime-source /path/to/ModelSim_YOLOX_PersonTracking
```

The helper validates the official `xlnx_dpu` 4.0-compatible patch and
`CONFIG_XILINX_DPU=y`, then copies only the official kernel/Vitis-AI recipe
trees into the external project. It appends the VART/XIR/unilog/target-factory
rootfs selections and adds `python3-numpy` plus `python3-opencv` to the image
without deleting existing user selections, writes a small manifest, and rejects
every PetaLinux release other than 2022.1. It deliberately does not copy ZCU102
device-tree addresses or boot assets, build an image, or touch the board. Run
`petalinux-config --get-hw-description` against the exact PYNQ-ZU XSA before
staging so the generated DPU node comes from this hardware.

The helper also appends built-in PS USB **dual-role** DWC3, V4L2 and UVC options
to the project kernel fragment. Dual-role is required by the Xilinx 5.15 kernel
configuration used here: the host-only variant fails to link its required
gadget-hibernation object. This is required for a C270 UVC camera to enumerate
on the new image; it does not prove physical USB capture until the board boots
it.

When `--xmodel` is supplied, the helper copies only that nonempty compiled
`.xmodel` into the external PetaLinux layer and creates a closed local package
which installs it as `/opt/models/yolov8n_b512.xmodel`. Its SHA-256 and byte
count go into the external stage manifest. The model binary itself is not
tracked by this repository. This makes the image self-contained for the
GraphRunner route; it is still not evidence that target-side inference works
until the camera gate below succeeds.

When `--runtime-source` is supplied, the helper packages the smallest tracked
first-stage program set into `/opt/pynq-yolov8`: `pipeline.py`, the YOLOv8
decoder/GraphRunner adapter and `pynq_yolov8_dpu_inference.py`. After booting
the matching image, first-stage one-camera tracking can run without an SSH
source copy:

```sh
python3 /opt/pynq-yolov8/person_tracking/pynq_yolov8_dpu_inference.py \
  --camera 0 --frames 3
```

It prints `PYNQ_YOLOV8_DPU_CAMERA_PASS` only after each captured frame has run
through GraphRunner and the existing tracker. It is a runtime gate, not proof
that a person was present when the scene has zero detections.

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

## Artifact identity record

Before attaching a PetaLinux image, `.xmodel`, or SD deployment bundle to a
locally built DPU, record the exact hardware artifacts instead of referring to
them by a directory name:

```sh
python3 verify_dpu_artifact_contract.py \
  --component-xml /path/to/DPUCZDX8G_v4_0_0/component.xml \
  --arch-json /path/to/generated/arch.json \
  --bitstream /path/to/pynq_zu_dpu_wrapper.bit \
  --xsa /path/to/pynq_zu_dpu_b512.xsa
```

It emits the DPU IP version, `arch.json` fingerprint, and SHA-256 values for
all four inputs, followed by `PYNQ_ZU_DPU_ARTIFACT_CONTRACT_PASS`. It is a
read-only identity record, not an XSA implementation check, Linux runtime
test, or proof that an `.xmodel` matches the fingerprint.

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

## Controlled Windows SD writer

The current first-stage image is the externally generated
`C:\pynq_zu_dpu_2022_20261113\sd_image_20261113\pynq_zu_dpu_single_camera_tracker_2022_1.wic`.
Its required SHA-256 is
`013f29c2f3feb8c0cf26b2f7f3987557905899d44b2157713cb0c9ae8e5791d6`.
It supersedes every earlier exported WIC because it contains both the compiled
model and the target-side single-camera tracker.

`write_pynq_zu_single_camera_sd.ps1` is deliberately unable to guess a
destination. It requires an explicit Windows disk number and an erase
acknowledgement, accepts only a USB or SD bus, rejects boot/system/read-only
or undersized disks, verifies the image hash, and then leaves the written disk
offline. It neither formats disks nor writes configuration flash. Run it only
from an elevated PowerShell after separately reviewing the removable disk
number:

```powershell
& .\write_pynq_zu_single_camera_sd.ps1 `
  -DiskNumber <explicit-removable-disk-number> `
  -IUnderstandThisErasesDisk
```

Use `-WhatIf` first for a no-write review. A successful raw write is still not
a target proof: power down, move the PYNQ-ZU switch to SD, boot the card, then
run `verify_dpu_runtime.py --xmodel /opt/models/yolov8n_b512.xmodel
--require-camera` and the target tracker command above.

The script requires an elevated PowerShell because Windows must take the raw
removable disk offline. Its optional `-ErrorReportPath <path>` records a
non-secret error report when an elevated invocation fails; it does not weaken
the disk-selection or hash checks.

For non-interactive elevation, invoke PowerShell with an encoded `-Command`
that passes `-Confirm:$false` as a Boolean expression. Do not pass the literal
text `-Confirm:$false` through `powershell.exe -File`: Windows PowerShell can
then treat it as a string and reject the common `Confirm` switch before the
writer starts. The writer reports failures with a single top-level `try/catch`;
it intentionally has no rethrowing top-level `trap`, which could recursively
handle its own error and conceal the actual failure.
