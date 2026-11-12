# PYNQ-ZU USB-video Vitis control

This folder is the software half of the Vivado `pynq_zu_usb_video` design.
It is intentionally not a Jupyter/PYNQ control path.

## Before creating the Vitis application

1. In Vivado, run `create_pynq_zu_usb_video_project.tcl`,
   `create_pynq_zu_usb_video_bd.tcl`, then `export_pynq_zu_usb_video_xsa.tcl`.
2. Set `PYNQ_ZU_USB_VIDEO_XSA` to the resulting `.xsa`, then use a Vitis build
   script that matches the toolchain used for that XSA.  For the verified
   2022.1 XSA, run `build_vitis_2022.tcl` through the 2022.1 `xsct.bat`; it
   creates an A53 standalone platform and `pynq_zu_usb_video_app.elf`.
   `build_vitis_embedded.py` remains the separate Vitis Embedded 2024.2 flow
   for a 2024.2 XSA and must not be used for the 2022.1 handoff.
3. Let Vitis generate `xparameters.h`; `main.c` uses those generated base
   addresses and deliberately fails compilation if the expected IP is absent.

After Vitis creates the platform, cross-check the handoff rather than assuming
the generated addresses match the source controller:

```sh
python3 fpga/verify_pynq_zu_usb_video_handoff.py \
  --xsa /path/to/pynq_zu_usb_video.xsa \
  --xparameters /path/to/standalone_domain/include/xparameters.h
```

It requires the Vivado HWH and Vitis header to agree on AXI DMA `0xA0000000`,
frame-ID GPIO `0xA0010000`, and video mailbox `0xA0020000`. This is a build
artifact contract only; it does not program the PL or exercise camera capture.

## IP Catalog / Block Design mapping

| Role | Vivado IP or module | Connection |
|---|---|---|
| USB camera wiring | Zynq UltraScale+ MPSoC PS | USB0 MIO 52–63; USB1 MIO 64–75 |
| USB frame storage | PS USB/UVC driver + DDR | Software-owned; no fake PL camera pins |
| DDR to PL | AXI DMA MM2S + SmartConnect | PS `S_AXI_HP0_FPD` |
| Frame identifier | AXI GPIO | `stream_frame_id` on custom RTL |
| Feature hardware | `dual_camera_yolox_axis_top` | 64-bit AXI4-Stream from DMA |
| Bbox / result interrupt | custom RTL AXI-Lite + IRQ | PS `M_AXI_HPM0_FPD`, `pl_ps_irq0` |

The C controller writes the frame ID, then all bbox payload registers, and
commits with CONTROL=`0x3` last.  The host unit test checks this contract.
Actual Logitech C270 UVC capture, interrupt setup and bandwidth/USB-root-hub
validation remain board-dependent integration work.  DMA cache maintenance is
implemented by `main.c` before its 64-bit source buffer is submitted.

## Vitis 2024.2 Windows environment check

The first platform build must use a Vitis installation with the embedded
software flow, including `xsct`, the `embeddedsw` repository, and a working
Lopper installation.  The Vitis Python CLI uses `VITIS_LOPPER_INSTALL_LOC`
for the Lopper root and `ESW_REPO` for the embedded-software repository.

On 2026-11-06, complete Vitis Embedded Development 2024.2 was installed and
used to build the platform, FSBL and A53 ELF from the exported XSA. The actual
generated mailbox macro is `XPAR_YOLOX_VIDEO_RTL_0_BASEADDR`, which this source
uses. The workspace must use a short Windows path (such as `C:\pynq_vitis`): a
long `%TEMP%` path made GCC fail while creating dependency files. This is a
reproducible host build flow. The JTAG DMA result is documented below; actual
UVC capture and continuous dual-camera operation remain unverified.

## UVC integration boundary

The installed standalone Embedded Software repository was inspected on
2026-11-06.  Its USB examples implement storage, mouse, keyboard and
microphone; it contains no UVC host-class implementation.  Consequently a
standalone A53 ELF must not be represented as a Logitech C270 capture driver.
It is valid for the tested AXI control/DMA role, but a real UVC source requires
the PYNQ Linux kernel's UVC/V4L2 driver.

The next non-Jupyter control path is therefore a Vitis **Linux A53
application**: V4L2 dequeues the two UVC frames into kernel/CMA-backed DDR,
the application packs the A/B RGB words, performs cache/DMA ownership changes,
and programs this Block Design's AXI DMA.  It needs a Linux sysroot plus a
board-side contiguous DMA-buffer interface; neither may be replaced by fake PL
camera pins or an unsupported bare-metal USB class driver.

For real UVC work, use the board's physical `JTAG SD` boot-mode switch in the
**SD (right)** position and power-cycle with the prepared PYNQ SD card.  This
boots Linux/V4L2; it does not prevent later Vivado/Vitis JTAG debugging.  The
PYNQ-ZU reference manual documents JTAG on the left and MicroSD on the right.

`linux/uvc_v4l2_packer.c` now supplies the first Linux application component:
it V4L2-captures two 640×480 YUYV frames and produces the RTL's packed
64-bit A/B RGB format.  It is compiler-verified as a 74,624-byte AArch64
ELF64 via Vitis' direct `aarch64-linux-gnu-gcc.exe`; the similarly named
Windows wrapper fails with a DLL loader error and must not be used. The
board-side contiguous DMA allocation/handoff remains the next integration
point.

## JTAG AXI and full-frame DMA test

`main.c` creates one 640×480 packed dual-RGB synthetic frame in aligned DDR,
flushes the data cache, submits it through AXI DMA MM2S, and stores result,
GPIO readback, mailbox frame/status, and DMA status in volatile globals for
JTAG inspection. The Block Design uses transfer-length width 23, so a
2,457,600-byte frame fits in one SimpleTransfer.

On 2026-11-06, a clean PYNQ-ZU JTAG flow (PS/DDR initialization, new PL
bitstream, then new A53 ELF) read `result=0`, GPIO=`42`, mailbox frame=`42`,
mailbox status=`2`, and DMA status=`0x1002`; the AXI DMA status register also
read `0x1002` (idle plus IOC completion). This proves the A53 → DDR → AXI DMA
→ PL AXI4-Stream path for a complete frame. It does not prove USB UVC capture,
two-camera stability, real YOLOX results, or the IRQ handler.

`fpga/scan_pynq_zu_jtag.tcl` is a Vivado Hardware Manager read-only cable and
device scanner. `fpga/run_pynq_zu_usb_video_jtag.tcl` is the corresponding
volatile XSDB launcher: it requires external `PYNQ_ZU_JTAG_BIT`,
`PYNQ_ZU_JTAG_PMUFW`, `PYNQ_ZU_JTAG_FSBL`, `PYNQ_ZU_JTAG_ELF`, and
`PYNQ_ZU_JTAG_RESULT_ADDR` values. It can explicitly preserve already-loaded
PL and an SD-initialized PS with `PYNQ_ZU_JTAG_SKIP_FPGA=1`,
`PYNQ_ZU_JTAG_SKIP_RESET=1`, and `PYNQ_ZU_JTAG_SKIP_BOOT=1`; this is only
appropriate after a hardware operator has established the exact state. Neither
script writes SD, QSPI, eMMC, or configuration flash. A power-cycle restores
the selected boot source.

On 2026-11-12 Vivado Hardware Manager actually enumerated `xczu5_0` and
programmed the USB-video bitstream with `End of startup status: HIGH`. XSDB's
generic target reported an incompatible bitstream even with revision checking
disabled; do not use its skip-device-compatibility option. A direct Vitis ELF
attempt then stopped at `Cannot halt processor core, timeout`, so it is **not**
evidence of Vitis execution. Power-cycle back to SD/Linux before retrying.

## SD/Linux overlay staging

For a later SD-booted PYNQ Linux test, stage the exact implemented hardware
without programming the board.  From the `ModelSim_YOLOX_PersonTracking`
repository directory, run:

```powershell
.\fpga\prepare_pynq_zu_usb_video_overlay.ps1 `
  -BuildDir C:\path\to\pynq_zu_usb_video_build `
  -OutputDir $env:TEMP\pynq_zu_usb_video_overlay
```

The output is the matching pair `pynq_zu_usb_video.bit` and
`pynq_zu_usb_video.hwh`, plus their SHA-256 values.  Copying/loading that
pair remains a separate authenticated board action; staging neither writes an
SD card nor makes UVC/DMA/DPU inference work by itself.

To use the existing authenticated deployment helper after staging, pass that
directory via `-UsbVideoOverlayDir` and add `-RunUsbVideoOverlayCheck`.  The
bundle keeps this pair under `overlay_usb_video/`, copies it next to the
dedicated verifier, downloads it with `Overlay()`, and only round-trips the
frame-ID registers at GPIO `0xA0010000` and mailbox `0xA0020000`.  It never
writes the mailbox CONTROL register, so it does not command DMA or capture.
