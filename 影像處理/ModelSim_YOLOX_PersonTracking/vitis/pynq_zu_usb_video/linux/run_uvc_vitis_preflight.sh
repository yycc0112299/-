#!/bin/sh
# Read-only-ish Linux UVC/Vitis preflight.  It only opens V4L2 cameras and
# writes one packed diagnostic frame to a caller-selected temporary directory.
set -eu

camera_a=${1:-/dev/video0}
camera_b=${2:-/dev/video2}
packer=${PACKER:-./uvc_v4l2_packer}
output_dir=${OUTPUT_DIR:-/tmp}
output="$output_dir/pynq_zu_dual_rgb888_640x480.bin"
expected_bytes=2457600

for device in "$camera_a" "$camera_b"; do
    if [ ! -c "$device" ]; then
        echo "PYNQ_ZU_UVC_PREFLIGHT_FAIL missing V4L2 device: $device" >&2
        exit 2
    fi
done
if [ ! -x "$packer" ]; then
    echo "PYNQ_ZU_UVC_PREFLIGHT_FAIL packer is not executable: $packer" >&2
    exit 3
fi
mkdir -p "$output_dir"
rm -f "$output"
"$packer" "$camera_a" "$camera_b" "$output"
actual_bytes=$(wc -c < "$output" | tr -d '[:space:]')
if [ "$actual_bytes" != "$expected_bytes" ]; then
    echo "PYNQ_ZU_UVC_PREFLIGHT_FAIL bytes=$actual_bytes expected=$expected_bytes" >&2
    exit 4
fi
echo "PYNQ_ZU_UVC_VITIS_PREFLIGHT_PASS camera_a=$camera_a camera_b=$camera_b bytes=$actual_bytes output=$output"
