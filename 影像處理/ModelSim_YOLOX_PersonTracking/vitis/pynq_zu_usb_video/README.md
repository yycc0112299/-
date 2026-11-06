# PYNQ-ZU USB-video Vitis control

This folder is the software half of the Vivado `pynq_zu_usb_video` design.
It is intentionally not a Jupyter/PYNQ control path.

## Before creating the Vitis application

1. In Vivado, run `create_pynq_zu_usb_video_project.tcl`,
   `create_pynq_zu_usb_video_bd.tcl`, then `export_pynq_zu_usb_video_xsa.tcl`.
2. Create a Vitis 2024.2 platform from the resulting `.xsa` for the PYNQ-ZU
   A53 standalone domain, then add these `src/` files to an application.
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
