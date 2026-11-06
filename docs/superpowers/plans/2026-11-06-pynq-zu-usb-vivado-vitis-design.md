# PYNQ-ZU USB Vivado/Vitis Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the notebook-oriented control path with a reproducible Vivado Block Design/XSA and a Vitis bare-metal control application for the PYNQ-ZU USB-camera pipeline.

**Architecture:** Logitech C270 cameras remain USB/UVC peripherals of the Zynq UltraScale+ PS. The PYNQ-ZU board preset assigns USB0 to MIO 52–63 and USB1 to MIO 64–75; those are PS-fixed connections, not PL GPIO. The Block Design provides PS DDR, AXI SmartConnect, AXI DMA and the existing mailbox/ROI RTL. Software built in Vitis owns USB-driver integration, DMA buffers, mailbox writes and IRQ handling; a hardware-independent stub proves register sequencing until USB capture is available.

**Tech Stack:** Vivado 2024.2 TCL, Zynq UltraScale+ MPSoC, AXI DMA, AXI4-Lite, AXI4-Stream, Vitis 2024.2 C/C++, Xilinx standalone BSP.

**Spec:** Repository progress files and `fpga/README.md`.

## Global Constraints

- Target is TUL PYNQ-ZU `xczu5eg-sfvc784-1-e`; use board preset `tul.com.tw:pynqzu:part0:1.1`.
- USB C270 D+/D− is controlled by PS USB hardware; never expose it as PL external ports or create PL XDC assignments for it.
- Keep generated Vivado/Vitis output outside Git; sources, scripts, tests and documentation are tracked.
- Export an XSA only after Block Design validation and successful implementation.
- Do not claim that a USB/UVC, DMA or camera hardware test passed unless it was run on the PYNQ-ZU.

## Review Focus

- A future edit must retain both board-preset USB controllers and their MIO mappings.
- AXI DMA must have a memory-facing PS high-performance connection, not only a control-plane connection.
- DMA stream width must exactly match the existing 64-bit packed dual-RGB stream adapter.
- Software must reject a missing DMA/IP base address rather than write a hard-coded value.
- A Vitis application must compile without requiring a physical camera or PYNQ Python.

---

### Task 1: Assert the USB/PS Block Design contract

**Files:**
- Create: `fpga/tests/test_pynq_zu_usb_bd_contract.py`
- Modify: `fpga/create_pynq_zu_usb_video_bd.tcl`

**Interfaces:**
- Produces: a script that creates `pynq_zu_usb_video` and prints `PYNQ_ZU_USB_VIDEO_BD_CREATED=`.

- [ ] **Step 1: Write failing static-contract tests** for USB0/USB1 preset retention, AXI DMA, PS high-performance port, 64-bit AXIS and mailbox IRQ.
- [ ] **Step 2: Run** `python fpga/tests/test_pynq_zu_usb_bd_contract.py`; expect failure because the script is absent.
- [ ] **Step 3: Implement** `create_pynq_zu_usb_video_bd.tcl` with PS, SmartConnect control plane, AXI DMA, AXIS interconnect/FIFO boundary, existing RTL mailbox, 20 MHz control clock and PS IRQ.
- [ ] **Step 4: Run static-contract tests** and Vivado batch `validate_bd_design`; expect pass.

### Task 2: Export reproducible hardware platform

**Files:**
- Create: `fpga/export_pynq_zu_usb_video_xsa.tcl`
- Modify: `fpga/create_pynq_zu_rtl_project.tcl`

**Interfaces:**
- Consumes: completed `pynq_zu_usb_video.bd`.
- Produces: `pynq_zu_usb_video.xsa` in `$PYNQ_ZU_BUILD_DIR`.

- [ ] **Step 1: Extend contract test** to require `write_hw_platform -fixed -include_bit` and a missing-build guard.
- [ ] **Step 2: Run test**; expect failure before exporter exists.
- [ ] **Step 3: Implement exporter** which generates wrapper, runs implementation and emits an XSA only on successful bitstream creation.
- [ ] **Step 4: Run tests and Vivado batch flow**; record actual result without treating a local test as board validation.

### Task 3: Add Vitis standalone control application

**Files:**
- Create: `vitis/pynq_zu_usb_video/src/main.c`
- Create: `vitis/pynq_zu_usb_video/src/video_control.h`
- Create: `vitis/pynq_zu_usb_video/README.md`
- Create: `vitis/pynq_zu_usb_video/tests/test_video_control.c`

**Interfaces:**
- Produces: `video_control_init`, `video_control_submit_pair`, `video_control_ack_irq`; base addresses are compile-time BSP parameters, never repository machine paths.

- [ ] **Step 1: Write host-buildable failing C tests** for register ordering and invalid hardware-address rejection.
- [ ] **Step 2: Compile/run test**; expect missing production symbols.
- [ ] **Step 3: Implement minimal controller** that writes DMA/RTL mailbox only through its injected register interface; add Vitis-specific `main.c` that gets addresses from xparameters.
- [ ] **Step 4: Run host tests** and Vitis compilation when the Vitis CLI is installed.

### Task 4: Document and synchronize

**Files:**
- Modify: `fpga/README.md`
- Modify: `PROGRESS_FOR_CODEX.md`
- Modify: `PROGRESS_FOR_HUMANS.md`
- Modify: `CONVERSATION_PROGRESS_LOG.md`

- [ ] **Step 1: Document IP Catalog locations, USB MIO mappings, XSA→Vitis procedure and verification boundary.**
- [ ] **Step 2: Run whitespace checks, tests and Git diff review.**
- [ ] **Step 3: Commit and push the verified source/doc changes to `main`.**
