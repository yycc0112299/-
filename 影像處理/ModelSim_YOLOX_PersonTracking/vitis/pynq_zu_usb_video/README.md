# PYNQ-ZU USB-video Vitis control

This folder is the software half of the Vivado `pynq_zu_usb_video` design.
It is intentionally not a Jupyter/PYNQ control path.

## Before creating the Vitis application

1. In Vivado, run `create_pynq_zu_usb_video_project.tcl`,
   `create_pynq_zu_usb_video_bd.tcl`, then `export_pynq_zu_usb_video_xsa.tcl`.
2. Set `PYNQ_ZU_USB_VIDEO_XSA` to the resulting `.xsa`, then run
   `build_vitis_embedded.py` through Vitis Embedded 2024.2. It creates an A53
   standalone platform and `pynq_zu_usb_video_app.elf`.
3. Let Vitis generate `xparameters.h`; `main.c` uses those generated base
   addresses and deliberately fails compilation if the expected IP is absent.

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
Actual Logitech C270 UVC capture, DMA cache maintenance, interrupt setup and
bandwidth/USB-root-hub validation remain board-dependent integration work.

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
reproducible host build flow. The JTAG AXI smoke-test result is documented
below; UVC/DMA/PL streaming remains unverified on hardware.

## JTAG AXI smoke test

`main.c` submits a frame-ID 42 bbox pair, reads the AXI GPIO and AXI-Lite
mailbox back, and stores four volatile values (`video_control_result`, GPIO
readback, mailbox frame readback, and mailbox status). They can be inspected
over JTAG after the CPU is stopped. On 2026-11-06, a clean PYNQ-ZU JTAG flow
(PS/DDR initialization, PL bitstream, then A53 ELF) read result `0`, GPIO
`42`, mailbox frame `42`, and status `3`. Status bits 0/1 mean the one command
is pending and pair-present; with no UVC/DMA input this is expected. This proves
PS-to-PL AXI control only; it does not prove camera capture or DMA streaming.
