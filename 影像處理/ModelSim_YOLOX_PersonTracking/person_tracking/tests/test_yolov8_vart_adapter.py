"""Offline contracts for the future PYNQ-ZU VART YOLOv8 adapter."""

from pathlib import Path
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "assets"))

from yolov8_vart import VartYoloV8, standard_yolov8_decoder


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


class VartYoloV8Tests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
