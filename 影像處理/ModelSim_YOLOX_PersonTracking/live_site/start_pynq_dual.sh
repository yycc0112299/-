#!/usr/bin/env bash
# Run on a PYNQ-ZU SD-boot Linux image after the deployment bundle is unpacked.
# The first argument is the PYNQ address used by the browser to reach this
# dashboard.  It becomes the HTTP Host allow-list entry, so it must be the
# board address (not the viewing PC's address).
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BROWSER_HOST="${1:?Usage: ./start_pynq_dual.sh <PYNQ-IP-or-hostname>}"
PORT="${PYNQ_DASHBOARD_PORT:-8766}"

cd "$SCRIPT_DIR"
exec python3 dual_server.py \
  --bind 0.0.0.0 \
  --port "$PORT" \
  --allow-host "${BROWSER_HOST}:${PORT}" \
  --camera-a "${PYNQ_CAMERA_A:-0}" \
  --camera-b "${PYNQ_CAMERA_B:-1}"
