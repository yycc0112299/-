# Vitis Linux UVC frame source

`uvc_v4l2_packer.c` is the Linux counterpart to the bare-metal DMA smoke test.
It uses two V4L2 UVC YUYV capture devices, converts them to packed 64-bit words
(`A RGB[23:0]`, `B RGB[55:32]`), and writes exactly 640×480 words.  The current
bring-up request is 320×240 YUYV at 10 FPS; each input pixel is expanded to a
2×2 area so the downstream PL/DMA contract remains exactly 640×480. Build it
with the Vitis AArch64 Linux cross compiler, then run it on the PYNQ Linux
image with `/dev/video*` paths.  Its output is a safe format-contract check;
it is deliberately not a DMA allocation.  The production handoff must replace
the output file with a PYNQ Linux contiguous DMA buffer and submit that physical
address to the AXI DMA already verified through JTAG.

For the deployed two-board topology, use one C270 per PYNQ-ZU with an explicit
single-lane command. `--single-a` writes captured RGB only to the low A lane;
`--single-b` writes it only to the high B lane. The unused lane is all-black;
the program does not duplicate a camera and falsely represent it as an
independent second source.

```sh
# On board A: write camera pixels to RGB A[23:0], leave B[55:32] black.
./uvc_v4l2_packer --single-a /dev/video0 /tmp/board_a_rgb888.bin

# On board B: write camera pixels to RGB B[55:32], leave A[23:0] black.
./uvc_v4l2_packer --single-b /dev/video0 /tmp/board_b_rgb888.bin
```

On 2026-11-11 the Vitis 2024.2 AArch64 ELF was copied temporarily to the live
PYNQ-ZU and `--single-a /dev/video0` completed at negotiated 320×240 YUYV,
10 FPS. It produced 2,457,600 bytes / 307,200 words; 307,160 low A-lane words
were nonzero and every high B-lane word was zero. The temporary executable and
output were then removed. This is a real single-camera V4L2/packing result;
it is not AXI DMA, PL, DPU, two-camera, or two-board Wi-Fi proof.

The packer explicitly negotiates the source rate after selecting the format and
prints the negotiated result before streaming. Both C270s share the tested
PYNQ-ZU USB 2 hub. On 2026-11-11, the board accepted 320×240/10-FPS for both
devices but rejected the second `VIDIOC_STREAMON` with `ENOSPC`; the kernel
reported `Not enough bandwidth ... altsetting 7`. The same happened in a
320×240/10-FPS MJPEG stream-only test. Therefore this specific one-board,
two-C270 topology is **not** a completed capture path. Use one camera per
board for the planned two-board Wi-Fi architecture unless the physical USB
topology is changed and retested.

Two diagnostic modes are built into the same AArch64 executable:

```sh
# List formats, sizes, and frame intervals for one V4L2 capture node.
sudo ./uvc_v4l2_packer --probe /dev/video0

# Test whether two cameras can reach STREAMON using MJPEG. It does not decode
# MJPEG or produce a packed frame; it is solely a USB-resource diagnostic.
sudo ./uvc_v4l2_packer --mjpeg-stream-test /dev/video0 /dev/video2
```

After copying the AArch64 executable and `run_uvc_vitis_preflight.sh` to the
board, run `chmod +x` on both and execute:

```sh
./run_uvc_vitis_preflight.sh /dev/video0 /dev/video2
```

It fails clearly if either device or executable is absent, then requires the
output to be exactly `2,457,600` bytes. This validates UVC capture plus the PL
packing contract without programming AXI DMA yet. It has **not** passed with
two physical C270s on the currently tested USB hub.

The intended host command is:

```powershell
$bin = 'C:\Xilinx_Embedded_2024_2\Vitis\2024.2\gnu\aarch64\nt\aarch64-linux\bin'
$env:PATH = "$bin;$env:PATH"
& "$bin\aarch64-linux-gnu-gcc.exe" -std=c11 -Wall -Wextra -Werror -O2 uvc_v4l2_packer.c -o uvc_v4l2_packer
```

Or run `./build_linux_uvc_packer.ps1` from PowerShell; it writes the deployable
`uvc_v4l2_packer` ELF under `linux/build/` and prints a PASS marker.

On 2026-11-06 this command produced a 74,624-byte AArch64 ELF64 PIE with
`-Wall -Wextra -Werror`.  Do not use the adjacent
`x86_64-petalinux-mingw32/.../aarch64-xilinx-linux-gcc.exe` wrapper on this
Windows installation: it exits with `0xC0000135` before launching GCC.
