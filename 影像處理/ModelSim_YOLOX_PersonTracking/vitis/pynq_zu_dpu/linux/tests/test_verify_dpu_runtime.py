"""Offline contract tests for the board-side DPU runtime gate."""

from pathlib import Path
import sys
import tempfile
import unittest


LINUX_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LINUX_DIR))

from verify_dpu_runtime import DPU_COMPATIBLE, dpu_device_tree_nodes, valid_xmodel


class DpuRuntimeGateTests(unittest.TestCase):
    def test_discovers_only_the_expected_dpu_compatible_node(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dpu = root / "amba_pl" / "dpu@400000000"
            dpu.mkdir(parents=True)
            (dpu / "compatible").write_bytes(
                b"xlnx,other\0" + DPU_COMPATIBLE.encode("ascii") + b"\0"
            )
            other = root / "amba_pl" / "other@0"
            other.mkdir()
            (other / "compatible").write_bytes(b"xlnx,other\0")
            self.assertEqual(dpu_device_tree_nodes(root), [str(dpu)])

    def test_requires_a_nonempty_xmodel_file_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = Path(temporary) / "person.xmodel"
            model.touch()
            self.assertFalse(valid_xmodel(model))
            model.write_bytes(b"compiled-graph")
            self.assertTrue(valid_xmodel(model))
            self.assertFalse(valid_xmodel(model.with_suffix(".bin")))


if __name__ == "__main__":
    unittest.main()
