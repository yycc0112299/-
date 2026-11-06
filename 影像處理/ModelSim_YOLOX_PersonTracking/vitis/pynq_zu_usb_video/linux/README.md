# Vitis Linux UVC frame source

`uvc_v4l2_packer.c` is the Linux counterpart to the bare-metal DMA smoke test.
It uses two V4L2 UVC YUYV capture devices, converts them to packed 64-bit words
(`A RGB[23:0]`, `B RGB[55:32]`), and writes exactly 640×480 words.  Build it
with the Vitis AArch64 Linux cross compiler, then run it on the PYNQ Linux
image with `/dev/video*` paths.  Its output is a safe format-contract check;
it is deliberately not a DMA allocation.  The production handoff must replace
the output file with a PYNQ Linux contiguous DMA buffer and submit that physical
address to the AXI DMA already verified through JTAG.

After copying the AArch64 executable and `run_uvc_vitis_preflight.sh` to the
board, run `chmod +x` on both and execute:

```sh
./run_uvc_vitis_preflight.sh /dev/video0 /dev/video2
```

It fails clearly if either device or executable is absent, then requires the
output to be exactly `2,457,600` bytes.  This validates UVC capture plus the
PL packing contract without programming AXI DMA yet.

The intended host command is:

```powershell
$bin = 'C:\Xilinx_Embedded_2024_2\Vitis\2024.2\gnu\aarch64\nt\aarch64-linux\bin'
$env:PATH = "$bin;$env:PATH"
& "$bin\aarch64-linux-gnu-gcc.exe" -std=c11 -Wall -Wextra -Werror -O2 uvc_v4l2_packer.c -o uvc_v4l2_packer
```

On 2026-11-06 this command produced a 74,624-byte AArch64 ELF64 PIE with
`-Wall -Wextra -Werror`.  Do not use the adjacent
`x86_64-petalinux-mingw32/.../aarch64-xilinx-linux-gcc.exe` wrapper on this
Windows installation: it exits with `0xC0000135` before launching GCC.
