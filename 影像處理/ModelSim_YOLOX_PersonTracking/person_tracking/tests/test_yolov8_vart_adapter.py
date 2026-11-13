"""Offline contracts for the future PYNQ-ZU VART YOLOv8 adapter."""

from pathlib import Path
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "assets"))

from yolov8_vart import (
    GraphRunnerYoloV8,
    VartYoloV8,
    raw_yolov8_dfl_decoder,
    standard_yolov8_decoder,
)


class FakeTensor:
    def __init__(self, dims, fix_point, name="tensor"):
        self.dims = dims
        self.fix_point = fix_point
        self.name = name

    def get_attr(self, name):
        if name != "fix_point":
            raise KeyError(name)
        return self.fix_point


class FakeRunner:
    def __init__(self, output):
        self.output = output
        self.seen_input = None

    def execute_async(self, inputs, outputs):
        self.seen_input = inputs[0].copy()
        outputs[0][...] = self.output
        return 17

    def wait(self, job_id):
        self.last_job_id = job_id
        return 0


class FakeBuffer:
    """Small ndarray-backed stand-in for a Vitis AI TensorBuffer."""

    def __init__(self, tensor, values=None):
        self.tensor = tensor
        self.values = np.zeros(tensor.dims, dtype=np.int8) if values is None else values.copy()
        self.write_syncs = []
        self.read_syncs = []

    def get_tensor(self):
        return self.tensor

    def sync_for_write(self, offset, size):
        self.write_syncs.append((offset, size))

    def sync_for_read(self, offset, size):
        self.read_syncs.append((offset, size))

    def __array__(self, dtype=None):
        return self.values.astype(dtype) if dtype else self.values


class FakeGraphRunner:
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs

    def get_inputs(self):
        return self.inputs

    def get_outputs(self):
        return self.outputs

    def execute_async(self, inputs, outputs):
        self.seen_inputs = inputs
        self.seen_outputs = outputs
        return 31

    def wait(self, job_id):
        self.job_id = job_id
        return 0


class VartYoloV8Tests(unittest.TestCase):
    def test_raw_three_head_decoder_decodes_a_person_from_dfl_bins(self) -> None:
        heads = {}
        for size in (80, 40, 20):
            heads[f"head_{size}"] = np.zeros((1, 144, size, size), dtype=np.float32)
        # On the stride-32 grid, cell (0, 0) has center (16, 16).  Each DFL
        # distribution peaks at bin 1, giving four 32-pixel distances.
        selected = heads["head_20"]
        for side in range(4):
            selected[0, side * 16 + 1, 0, 0] = 20.0
        selected[0, 64, 0, 0] = .90

        decoder = raw_yolov8_dfl_decoder(confidence_threshold=.30, nms_threshold=.45)
        detections = decoder(heads, 640, 640)

        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["class_id"], 0)
        self.assertAlmostEqual(float(detections[0]["confidence"]), .90)
        self.assertEqual(detections[0]["box"], [0, 0, 48, 48])

    def test_standard_decoder_adapts_a_single_raw_yolov8_head_to_person_boxes(self) -> None:
        raw = np.zeros((1, 84, 1), dtype=np.float32)
        raw[0, :4, 0] = [320, 320, 320, 160]
        raw[0, 4, 0] = .90
        decoder = standard_yolov8_decoder(confidence_threshold=.30, nms_threshold=.45)
        detections = decoder({"output": raw}, 640, 480)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["class_id"], 0)
        self.assertEqual(detections[0]["box"], [160, 160, 480, 320])
        self.assertAlmostEqual(float(detections[0]["confidence"]), .90)

    def test_standard_decoder_refuses_ambiguous_multi_head_outputs(self) -> None:
        decoder = standard_yolov8_decoder()
        with self.assertRaisesRegex(RuntimeError, "exactly one standard YOLOv8 output"):
            decoder({"head0": np.zeros((1, 84, 1)), "head1": np.zeros((1, 84, 1))}, 640, 480)

    def test_letterboxes_rgb_and_quantizes_for_nhwc_dpu_input(self) -> None:
        runner = FakeRunner(np.zeros((1, 84, 1), dtype=np.int8))
        detector = VartYoloV8.from_runner(
            runner,
            input_tensor=FakeTensor([1, 640, 640, 3], 7),
            output_tensors=[FakeTensor([1, 84, 1], 0)],
        )
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[0, 0] = [255, 128, 0]  # BGR: exercises the RGB swap.
        self.assertEqual(list(detector.infer_tensors(frame)), ["tensor"])
        self.assertEqual(runner.last_job_id, 17)
        self.assertEqual(runner.seen_input.dtype, np.int8)
        self.assertEqual(runner.seen_input.shape, (1, 640, 640, 3))
        self.assertEqual(runner.seen_input[0, 80, 0].tolist(), [0, 64, 127])
        self.assertEqual(runner.seen_input[0, 0, 0].tolist(), [57, 57, 57])

    def test_returns_dequantized_named_output_tensors(self) -> None:
        raw = np.zeros((1, 3, 2), dtype=np.int8)
        raw[0, :, 0] = [-128, 0, 127]
        runner = FakeRunner(raw)
        detector = VartYoloV8.from_runner(
            runner,
            input_tensor=FakeTensor([1, 640, 640, 3], 7),
            output_tensors=[FakeTensor([1, 3, 2], 7, "head0")],
        )
        outputs = detector.infer_tensors(np.zeros((480, 640, 3), dtype=np.uint8))
        np.testing.assert_allclose(outputs["head0"][0, :, 0], [-1.0, 0.0, 127 / 128])

    def test_refuses_person_detections_until_a_compiled_model_decoder_is_supplied(self) -> None:
        detector = VartYoloV8.from_runner(
            FakeRunner(np.zeros((1, 84, 1), dtype=np.int8)),
            input_tensor=FakeTensor([1, 640, 640, 3], 7),
            output_tensors=[FakeTensor([1, 84, 1], 0)],
        )
        with self.assertRaisesRegex(RuntimeError, "model-specific VART decoder"):
            detector.infer(np.zeros((480, 640, 3), dtype=np.uint8))

    def test_graph_runner_uses_tensor_buffers_and_synchronizes_them(self) -> None:
        input_tensor = FakeTensor([1, 640, 640, 3], 7, "images")
        output_tensor = FakeTensor([1, 144, 20, 20], 3, "head20")
        input_buffer = FakeBuffer(input_tensor)
        output_values = np.zeros((1, 144, 20, 20), dtype=np.int8)
        output_values[0, 64, 0, 0] = 7
        output_buffer = FakeBuffer(output_tensor, output_values)
        runner = FakeGraphRunner([input_buffer], [output_buffer])
        detector = GraphRunnerYoloV8.from_graph_runner(
            runner, confidence_threshold=.30, nms_threshold=.45,
        )

        output = detector.infer_tensors(np.zeros((480, 640, 3), dtype=np.uint8))

        self.assertEqual(runner.job_id, 31)
        self.assertEqual(runner.seen_inputs, [input_buffer])
        self.assertEqual(runner.seen_outputs, [output_buffer])
        self.assertEqual(input_buffer.write_syncs, [(0, input_buffer.values.nbytes)])
        self.assertEqual(output_buffer.read_syncs, [(0, output_buffer.values.nbytes)])
        self.assertEqual(output["head20"].shape, (1, 144, 20, 20))
        self.assertAlmostEqual(float(output["head20"][0, 64, 0, 0]), 7 / 8)


if __name__ == "__main__":
    unittest.main()
