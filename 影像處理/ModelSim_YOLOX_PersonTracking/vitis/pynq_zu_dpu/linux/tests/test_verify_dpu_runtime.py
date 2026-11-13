"""Offline contract tests for the board-side DPU runtime gate."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


LINUX_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LINUX_DIR))

from verify_dpu_runtime import (
    DPU_COMPATIBLE,
    command_result,
    dpu_device_tree_nodes,
    graph_runner_result,
    python_runtime_results,
    valid_xmodel,
)


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

    def test_accepts_only_a_python_binding_that_exposes_graph_runner(self) -> None:
        graph_runner_type = type("GraphRunner", (), {})
        good_module = type("GoodModule", (), {"GraphRunner": graph_runner_type})
        missing_module = type("MissingModule", (), {})

        self.assertEqual(graph_runner_result(lambda _: good_module)["available"], True)
        missing = graph_runner_result(lambda _: missing_module)
        self.assertFalse(missing["available"])
        self.assertIn("GraphRunner", str(missing["error"]))

    def test_requires_numpy_and_opencv_imports_before_runtime_can_pass(self) -> None:
        def modules(name: str) -> dict[str, object]:
            return {"available": name != "cv2"}

        report = python_runtime_results(
            module_probe=modules,
            graph_probe=lambda: {"available": True},
        )
        self.assertTrue(report["numpy"]["available"])
        self.assertFalse(report["cv2"]["available"])
        self.assertFalse(report["ok"])

    def test_reports_a_timeout_instead_of_hanging_on_xdputil_query(self) -> None:
        def times_out(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd=[sys.executable, "--version"], timeout=2)

        report = command_result([sys.executable, "--version"], timeout_seconds=2,
                                runner=times_out)
        self.assertTrue(report["available"])
        self.assertTrue(report["timed_out"])
        self.assertIsNone(report["returncode"])


if __name__ == "__main__":
    unittest.main()
