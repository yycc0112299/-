"""Contract checks for the target-side VART link smoke test source."""

from pathlib import Path
import unittest


LINUX_DIR = Path(__file__).resolve().parents[1]


class VartLinkSmokeSourceTests(unittest.TestCase):
    def test_smoke_source_and_builder_keep_runtime_link_contract(self) -> None:
        source = (LINUX_DIR / "vart_link_smoke.cpp").read_text(encoding="utf-8")
        builder = (LINUX_DIR / "build_vart_link_smoke.sh").read_text(encoding="utf-8")
        self.assertIn("#include <vart/runner.hpp>", source)
        self.assertIn("vart::Runner::create_runner", source)
        self.assertIn("${CXX:?", builder)
        self.assertIn("-lvart-runner", builder)
        self.assertIn("-lxir", builder)
        self.assertIn("-lunilog", builder)


if __name__ == "__main__":
    unittest.main()
