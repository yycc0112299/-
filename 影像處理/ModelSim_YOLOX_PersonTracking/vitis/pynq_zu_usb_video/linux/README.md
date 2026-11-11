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
