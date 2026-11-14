"""End-to-end loopback proof for the future second-PYNQ metadata service."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "simulate_two_pynq_cross_camera.py"


class SimulateTwoPynqCrossCameraTests(unittest.TestCase):
    def test_two_independent_fusion_processes_exchange_confirmed_candidates(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--output-dir",
                    str(output_directory),
                    "--min-hits",
                    "2",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("TWO_PYNQ_LOOPBACK_SIMULATION_PASS", result.stdout)
            for board in ("board_a", "board_b"):
                result_path = output_directory / f"{board}_candidates.json"
                payload = json.loads(result_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["candidates"][0]["status"], "confirmed_candidate")
                self.assertTrue(payload["candidates"][0]["candidate_label"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
