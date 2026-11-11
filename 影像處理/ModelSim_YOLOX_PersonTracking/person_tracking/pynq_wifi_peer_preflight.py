#!/usr/bin/env python3
"""Read-only readiness gate for PYNQ-ZU two-board Wi-Fi metadata exchange."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys


def interface_ipv4_addresses(interface: str) -> list[str]:
    """Return IPv4 addresses reported by the Linux `ip` tool, without changes."""
    try:
        completed = subprocess.run(
            ["ip", "-j", "addr", "show", "dev", interface], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
    except OSError:
        return []
    if completed.returncode:
        return []
    try:
        entries = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    return sorted({
        str(address["local"])
        for entry in entries
        for address in entry.get("addr_info", [])
        if address.get("family") == "inet" and address.get("local")
    })


def probe_peer(host: str, port: int, timeout: float) -> dict[str, object]:
    """Attempt one TCP connection; it does not send payload or change settings."""
    report: dict[str, object] = {"host": host, "port": port, "reachable": False}
    try:
        with socket.create_connection((host, port), timeout=timeout):
            report["reachable"] = True
    except OSError as error:
        report["error"] = f"{type(error).__name__}: {error}"
    return report


def evaluate_wifi_readiness(*, interface: str = "wlan0", interface_exists: bool, operstate: str | None,
                            ipv4_addresses: list[str], peer: dict[str, object] | None,
                            require_peer: bool) -> dict[str, object]:
    """Apply the exact gates required before starting the two-board sender."""
    reasons: list[str] = []
    if not interface_exists:
        reasons.append(f"{interface} interface is missing")
    else:
        if operstate != "up":
            reasons.append(f"{interface} operstate is {operstate or 'unknown'}, not up")
        if not ipv4_addresses:
            reasons.append(f"{interface} has no IPv4 address")
    if require_peer:
        if peer is None:
            reasons.append("no TCP peer was supplied for the required peer check")
        elif not peer.get("reachable"):
            reasons.append(f"TCP peer {peer.get('host')}:{peer.get('port')} is not reachable")
    return {
        "status": "PASS" if not reasons else "FAIL",
        "interface": interface,
        "interface_exists": interface_exists,
        "operstate": operstate,
        "ipv4_addresses": ipv4_addresses,
        "peer": peer,
        "blocking_reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", default="wlan0")
    parser.add_argument("--peer-host")
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--timeout", type=float, default=3.0)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.timeout <= 0:
        parser.error("port must be 1..65535 and timeout must be positive")
    interface_path = Path("/sys/class/net") / args.interface
    interface_exists = interface_path.is_dir()
    operstate = None
    if interface_exists:
        try:
            operstate = (interface_path / "operstate").read_text().strip()
        except OSError:
            pass
    peer = probe_peer(args.peer_host, args.port, args.timeout) if args.peer_host else None
    report = evaluate_wifi_readiness(
        interface=args.interface, interface_exists=interface_exists, operstate=operstate,
        ipv4_addresses=interface_ipv4_addresses(args.interface) if interface_exists else [],
        peer=peer, require_peer=bool(args.peer_host),
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    marker = "PYNQ_WIFI_PEER_PREFLIGHT_PASS" if report["status"] == "PASS" else "PYNQ_WIFI_PEER_PREFLIGHT_FAIL"
    print(marker)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
