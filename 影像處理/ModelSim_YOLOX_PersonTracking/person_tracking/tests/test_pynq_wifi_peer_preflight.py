"""Offline contracts for the read-only PYNQ two-board Wi-Fi preflight."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pynq_wifi_peer_preflight import evaluate_wifi_readiness


class PynqWifiPeerPreflightTests(unittest.TestCase):
    def test_accepts_connected_interface_and_reachable_peer(self) -> None:
        report = evaluate_wifi_readiness(
            interface_exists=True, operstate="up", ipv4_addresses=["192.168.50.10"],
            peer={"host": "192.168.50.11", "port": 8790, "reachable": True},
            require_peer=True,
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["blocking_reasons"], [])

    def test_rejects_unconfigured_wifi_without_claiming_peer_success(self) -> None:
        report = evaluate_wifi_readiness(
            interface_exists=True, operstate="down", ipv4_addresses=[], peer=None,
            require_peer=False,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("wlan0 has no IPv4 address", report["blocking_reasons"])

    def test_requires_peer_tcp_connection_when_requested(self) -> None:
        report = evaluate_wifi_readiness(
            interface_exists=True, operstate="up", ipv4_addresses=["192.168.50.10"],
            peer={"host": "192.168.50.11", "port": 8790, "reachable": False,
                  "error": "ConnectionRefusedError: refused"},
            require_peer=True,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("TCP peer 192.168.50.11:8790 is not reachable", report["blocking_reasons"])

    def test_reports_the_selected_interface_name(self) -> None:
        report = evaluate_wifi_readiness(
            interface="wifi-test", interface_exists=False, operstate=None,
            ipv4_addresses=[], peer=None, require_peer=False,
        )
        self.assertEqual(report["interface"], "wifi-test")
        self.assertIn("wifi-test interface is missing", report["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
