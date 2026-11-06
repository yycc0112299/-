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

## Vitis 2024.2 Windows environment check

The first platform build must use a Vitis installation with the embedded
software flow, including `xsct`, the `embeddedsw` repository, and a working
Lopper installation.  The Vitis Python CLI uses `VITIS_LOPPER_INSTALL_LOC`
for the Lopper root and `ESW_REPO` for the embedded-software repository.

On 2026-11-06 this computer successfully exported the XSA and started the
Vitis platform creation, but its Vitis 2024.2 installation had no `xsct` and
its bundled Lopper requirements link was absent.  A local Lopper virtual
environment could be made runnable, yet Vitis still failed while generating
the system device tree.  Therefore this repository does **not** claim a Vitis
BSP/application compile or board download.  Repair or install the complete
Vitis Embedded Development flow, then create an A53 `standalone` platform
from the XSA before compiling `src/`.
