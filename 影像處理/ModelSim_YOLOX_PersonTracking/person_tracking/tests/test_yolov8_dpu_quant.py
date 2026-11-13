"""Contracts for making YOLOv8n quantizable by Vitis AI 2.5."""

from pathlib import Path
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "assets"))

from yolov8_dpu_quant import (
    c2f_forward_without_split,
    export_deploy_artifact,
    replace_silu_modules,
    split_c2f_projection,
)


class C2f:
    """Small NumPy equivalent of Ultralytics' C2f block for the contract test."""

    def __init__(self) -> None:
        self.c = 2
        self.cv1 = lambda value: value
        self.m = [lambda value: value + 10, lambda value: value + 100]
        self.cv2 = lambda value: value


class FakeQuantizer:
    def __init__(self) -> None:
        self.called = []

    def export_quant_config(self) -> None:
        self.called.append("quant_config")

    def export_xmodel(self) -> None:
        self.called.append("xmodel")


class SiLU:
    pass


class Linear:
    pass


class FakeParent:
    def __init__(self) -> None:
        self.activation = SiLU()
        self.linear = Linear()

    def named_children(self):
        return (("activation", self.activation), ("linear", self.linear))


class FakeNetwork:
    def __init__(self) -> None:
        self.parent = FakeParent()

    def modules(self):
        return (self, self.parent)

    def named_children(self):
        return (("parent", self.parent),)


class YoloV8DpuQuantTests(unittest.TestCase):
    def test_split_projection_uses_two_slices_that_preserve_both_channel_groups(self) -> None:
        projection = np.array([[[[1]], [[2]], [[3]], [[4]]]], dtype=np.float32)

        first, second = split_c2f_projection(projection, 2)

        np.testing.assert_array_equal(first, np.array([[[[1]], [[2]]]], dtype=np.float32))
        np.testing.assert_array_equal(second, np.array([[[[3]], [[4]]]], dtype=np.float32))

    def test_c2f_forward_without_split_chains_bottlenecks_from_the_second_slice(self) -> None:
        block = C2f()
        projection = np.array([[[[1]], [[2]], [[3]], [[4]]]], dtype=np.float32)

        result = c2f_forward_without_split(block, projection, np.concatenate)

        np.testing.assert_array_equal(
            result,
            np.array([[[[1]], [[2]], [[3]], [[4]], [[13]], [[14]], [[113]], [[114]]]],
                     dtype=np.float32),
        )

    def test_deploy_mode_exports_xmodel_after_calibration(self) -> None:
        quantizer = FakeQuantizer()

        export_deploy_artifact(quantizer, "test")

        self.assertEqual(quantizer.called, ["xmodel"])

    def test_activation_replacement_changes_only_silu_activations(self) -> None:
        network = FakeNetwork()

        replacements = replace_silu_modules(
            network, lambda: "LEAKYRELU", silu_type_name="SiLU"
        )

        self.assertEqual(replacements, 1)
        self.assertEqual(network.parent.activation, "LEAKYRELU")
        self.assertIsInstance(network.parent.linear, Linear)



if __name__ == "__main__":
    unittest.main()
