#!/usr/bin/env bash
# Run on a PYNQ-ZU SD-boot Linux image after the deployment bundle is unpacked.
# The first argument is the PC address permitted to view the dashboard.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PC_HOST="${1:?Usage: ./start_pynq_dual.sh <PC-IP-or-hostname>}"
PORT="${PYNQ_DASHBOARD_PORT:-8766}"

cd "$SCRIPT_DIR"
exec python3 dual_server.py \
  --bind 0.0.0.0 \
  --port "$PORT" \
  --allow-host "${PC_HOST}:${PORT}" \
  --camera-a "${PYNQ_CAMERA_A:-0}" \
  --camera-b "${PYNQ_CAMERA_B:-1}"
