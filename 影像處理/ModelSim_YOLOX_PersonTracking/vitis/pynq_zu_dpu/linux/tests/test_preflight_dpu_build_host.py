"""Offline contract tests for the DPU Linux-image build-host preflight."""

from pathlib import Path
import sys
import unittest


LINUX_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LINUX_DIR))

from preflight_dpu_build_host import evaluate_build_contract


class DpuBuildHostPreflightTests(unittest.TestCase):
    def test_accepts_current_dpu_40_vitis_ai_25_2022_1_docker_route(self) -> None:
        report = evaluate_build_contract(
            commands={"docker": True, "vai_c_xir": False, "petalinux-create": True},
            has_arch_json=True,
            dpu_ip_version="4.0",
            vitis_ai_version="2.5",
            vivado_version="2022.1",
            petalinux_version="2022.1",
        )
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["blocking_reasons"], [])

    def test_rejects_vitis_ai_35_for_the_current_dpu_40_hardware(self) -> None:
        report = evaluate_build_contract(
            commands={"docker": True, "vai_c_xir": False, "petalinux-create": True},
            has_arch_json=True,
            dpu_ip_version="4.0",
            vitis_ai_version="3.5",
            vivado_version="2023.1",
            petalinux_version="2023.1",
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("DPUCZDX8G 4.0 is paired with Vitis AI 2.5; provide --vitis-ai-version 2.5.",
                      report["blocking_reasons"])

    def test_accepts_dpu_41_vitis_ai_35_2023_1_contract(self) -> None:
        report = evaluate_build_contract(
            commands={"docker": True, "vai_c_xir": False, "petalinux-create": True},
            has_arch_json=True,
            dpu_ip_version="4.1",
            vitis_ai_version="3.5",
            vivado_version="2023.1",
            petalinux_version="2023.1",
        )
        self.assertEqual(report["status"], "PASS")

    def test_requires_a_compiler_route_and_generated_architecture(self) -> None:
        report = evaluate_build_contract(
            commands={"docker": False, "vai_c_xir": False, "petalinux-create": False},
            has_arch_json=False,
            dpu_ip_version="4.0",
            vitis_ai_version=None,
            vivado_version="2022.1",
            petalinux_version=None,
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("No Vitis AI compiler route: install Docker for the Vitis AI 2.5 container or expose vai_c_xir.",
                      report["blocking_reasons"])
        self.assertIn("No DPU-generated arch.json was supplied; do not compile YOLOv8 for a guessed fingerprint.",
                      report["blocking_reasons"])


if __name__ == "__main__":
    unittest.main()
