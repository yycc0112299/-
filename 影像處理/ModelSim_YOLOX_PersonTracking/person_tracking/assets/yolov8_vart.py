"""VART execution boundary for a compiled PYNQ-ZU YOLOv8 DPU model.

This module intentionally owns only the parts that are invariant across VART
models: finding the DPU runner, RGB letterboxing, INT8 quantization, job
execution and output dequantization.  A Vitis-AI compiled YOLOv8 graph can
emit one or several output heads whose layout is model-specific, so person
detection is deliberately unavailable until that compiled model has a tested
decoder.  This prevents an ONNX-output assumption from being misrepresented
as a working DPU detector.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from yolov8 import YoloV8


Decoder = Callable[[Mapping[str, np.ndarray], int, int], list[dict[str, object]]]


def standard_yolov8_decoder(*, output_name: str | None = None,
                            confidence_threshold: float = .30,
                            nms_threshold: float = .45) -> Decoder:
    """Create a decoder for a *verified* raw single-head YOLOv8 output.

    The compiled model must expose one tensor compatible with the raw Ultralytics
    ONNX layout, either ``(1, 84, candidates)`` or ``(1, candidates, 84)``.
    DPU compilation can instead expose several feature heads, so callers must
    inspect the actual `.xmodel` before registering this decoder.
    """
    if not 0.0 <= confidence_threshold <= 1.0:
        raise ValueError("confidence_threshold must be between 0 and 1")
    if not 0.0 <= nms_threshold <= 1.0:
        raise ValueError("nms_threshold must be between 0 and 1")

    def decode(outputs: Mapping[str, np.ndarray], source_width: int,
               source_height: int) -> list[dict[str, object]]:
        if output_name is None:
            if len(outputs) != 1:
                raise RuntimeError(
                    "standard YOLOv8 decoder requires exactly one standard YOLOv8 output; "
                    "inspect the compiled model and select a model-specific decoder"
                )
            predictions = next(iter(outputs.values()))
        else:
            try:
                predictions = outputs[output_name]
            except KeyError as error:
                raise RuntimeError(
                    f"expected verified YOLOv8 output {output_name!r}, got {sorted(outputs)}"
                ) from error
        return YoloV8.decode_predictions(
            predictions,
            source_width=source_width,
            source_height=source_height,
            confidence_threshold=confidence_threshold,
            nms_threshold=nms_threshold,
        )

    return decode


def raw_yolov8_dfl_decoder(*, confidence_threshold: float = .30,
                           nms_threshold: float = .45, input_size: int = 640) -> Decoder:
    """Decode the three `(1,144,H,W)` raw Ultralytics YOLOv8 Detect heads.

    This is the decoder contract for the compiled Vitis-AI raw-head graph:
    64 DFL channels (4 x 16 bins), then 80 COCO class channels.  It remains
    deliberately separate from runner construction because GraphRunner must
    be used for multi-subgraph xmodels.
    """
    if input_size <= 0:
        raise ValueError("input_size must be positive")

    def decode(outputs: Mapping[str, np.ndarray], source_width: int,
               source_height: int) -> list[dict[str, object]]:
        rows: list[np.ndarray] = []
        bins = np.arange(16, dtype=np.float32).reshape(1, 16, 1, 1)
        for name, value in outputs.items():
            head = np.asarray(value, dtype=np.float32)
            if head.ndim != 4 or head.shape[0] != 1 or head.shape[1] != 144:
                raise ValueError(f"raw YOLOv8 head {name!r} must be (1,144,H,W), got {head.shape}")
            _, _, height, width = head.shape
            if input_size % height or input_size % width:
                raise ValueError(f"raw YOLOv8 head {name!r} has incompatible grid {height}x{width}")
            stride_x, stride_y = input_size / width, input_size / height
            logits = head[:, :64].reshape(1, 4, 16, height, width)
            logits = logits - logits.max(axis=2, keepdims=True)
            probabilities = np.exp(logits)
            distances = (probabilities / probabilities.sum(axis=2, keepdims=True) * bins).sum(axis=2)[0]
            grid_x, grid_y = np.meshgrid(np.arange(width), np.arange(height))
            center_x = (grid_x.astype(np.float32) + .5) * stride_x
            center_y = (grid_y.astype(np.float32) + .5) * stride_y
            left, top, right, bottom = distances
            x0 = center_x - left * stride_x
            y0 = center_y - top * stride_y
            x1 = center_x + right * stride_x
            y1 = center_y + bottom * stride_y
            person = head[0, 64]
            for values in zip(x0.ravel(), y0.ravel(), x1.ravel(), y1.ravel(), person.ravel()):
                x_start, y_start, x_end, y_end, score = (float(item) for item in values)
                if score >= confidence_threshold:
                    rows.append(np.array([(x_start + x_end) / 2, (y_start + y_end) / 2,
                                          x_end - x_start, y_end - y_start, score], dtype=np.float32))
        if not rows:
            return []
        # Reuse the existing tested letterbox reversal and NMS boundary.
        return YoloV8.decode_predictions(np.stack(rows)[None, :, :],
                                         source_width=source_width,
                                         source_height=source_height,
                                         confidence_threshold=confidence_threshold,
                                         nms_threshold=nms_threshold)

    return decode


def _tensor_fix_point(tensor: Any) -> int:
    try:
        return int(tensor.get_attr("fix_point"))
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
        return 0


def _tensor_name(tensor: Any, index: int) -> str:
    name = getattr(tensor, "name", None)
    if not name:
        try:
            name = tensor.get_name()
        except AttributeError:
            name = None
    return str(name or f"output_{index}")


def _buffer_tensor(buffer: Any) -> Any:
    """Return the XIR tensor owned by a Vitis AI TensorBuffer."""
    try:
        return buffer.get_tensor()
    except AttributeError as error:
        raise TypeError("GraphRunner buffer does not expose get_tensor()") from error


def _sync_buffer(buffer: Any, direction: str, values: np.ndarray) -> None:
    """Synchronize a TensorBuffer across CPU/DPU memory when the API exposes it.

    GraphRunner's Python bindings normally provide ``sync_for_write/read``.
    The fallback keeps the adapter usable on host-only/fake buffer bindings that
    already use CPU memory and do not expose explicit synchronization methods.
    """
    method = getattr(buffer, f"sync_for_{direction}", None)
    if method is None:
        return
    try:
        method(0, int(values.nbytes))
    except TypeError:
        method()


def _quantized_yolov8_input(input_shape: tuple[int, ...], input_fix_point: int,
                            frame: np.ndarray) -> np.ndarray:
    """Letterbox one BGR camera frame into the signed INT8 YOLOv8 input."""
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError(f"expected BGR HxWx3 frame, received {frame.shape}")
    _, target_height, target_width, _ = input_shape
    source_height, source_width = frame.shape[:2]
    scale = min(target_width / source_width, target_height / source_height)
    resized = cv2.resize(frame, (round(source_width * scale), round(source_height * scale)),
                         interpolation=cv2.INTER_LINEAR)
    canvas = np.full((target_height, target_width, 3), 114, dtype=np.uint8)
    offset_x = (target_width - resized.shape[1]) // 2
    offset_y = (target_height - resized.shape[0]) // 2
    canvas[offset_y:offset_y + resized.shape[0], offset_x:offset_x + resized.shape[1]] = resized
    rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    scale_factor = float(2 ** input_fix_point) / 255.0
    values = np.rint(rgb.astype(np.float32) * scale_factor)
    return np.clip(values, -128, 127).astype(np.int8)[None, ...]


class GraphRunnerYoloV8:
    """Bridge the original multi-subgraph YOLOv8 xmodel to Vitis AI GraphRunner.

    Unlike ``VartYoloV8``, this owns whole-graph TensorBuffers.  Therefore it
    is the required path for the unchanged upstream SiLU YOLOv8n graph, whose
    CPU operators and B512 DPU subgraphs must run in one ordered graph.
    """

    def __init__(self, runner: Any, input_buffers: list[Any], output_buffers: list[Any], *,
                 confidence_threshold: float = .30, nms_threshold: float = .45,
                 decoder: Decoder | None = None) -> None:
        if len(input_buffers) != 1:
            raise ValueError(f"YOLOv8 GraphRunner requires one input buffer, got {len(input_buffers)}")
        if not output_buffers:
            raise ValueError("YOLOv8 GraphRunner has no output buffers")
        self.runner = runner
        self.input_buffers = list(input_buffers)
        self.output_buffers = list(output_buffers)
        self.input_tensor = _buffer_tensor(self.input_buffers[0])
        self.output_tensors = [_buffer_tensor(buffer) for buffer in self.output_buffers]
        self.input_shape = tuple(int(value) for value in self.input_tensor.dims)
        if len(self.input_shape) != 4 or self.input_shape[0] != 1 or self.input_shape[-1] != 3:
            raise ValueError("GraphRunner YOLOv8 input must be batch-one NHWC RGB")
        self.input_fix_point = _tensor_fix_point(self.input_tensor)
        self.output_names = [_tensor_name(tensor, index)
                             for index, tensor in enumerate(self.output_tensors)]
        if len(set(self.output_names)) != len(self.output_names):
            raise ValueError("GraphRunner output tensor names must be unique")
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.decoder = decoder

    @classmethod
    def from_graph_runner(cls, runner: Any, *, confidence_threshold: float = .30,
                          nms_threshold: float = .45,
                          decoder: Decoder | None = None) -> "GraphRunnerYoloV8":
        return cls(runner, list(runner.get_inputs()), list(runner.get_outputs()),
                   confidence_threshold=confidence_threshold, nms_threshold=nms_threshold,
                   decoder=decoder)

    @classmethod
    def from_xmodel(cls, xmodel: str | Path, *, confidence_threshold: float = .30,
                    nms_threshold: float = .45, decoder: Decoder | None = None) -> "GraphRunnerYoloV8":
        path = Path(xmodel)
        if not path.is_file() or path.suffix != ".xmodel":
            raise FileNotFoundError(f"compiled .xmodel is required: {path}")
        try:
            import vitis_ai_library
            import xir
        except ImportError as error:
            raise RuntimeError("XIR and vitis_ai_library.GraphRunner are required for YOLOv8 DPU execution") from error
        graph = xir.Graph.deserialize(str(path))
        try:
            runner = vitis_ai_library.GraphRunner.create_graph_runner(graph)
        except AttributeError as error:
            raise RuntimeError("vitis_ai_library.GraphRunner is required for this multi-subgraph YOLOv8 xmodel") from error
        return cls.from_graph_runner(runner, confidence_threshold=confidence_threshold,
                                     nms_threshold=nms_threshold, decoder=decoder)

    def infer_tensors(self, frame: np.ndarray) -> dict[str, np.ndarray]:
        input_data = _quantized_yolov8_input(self.input_shape, self.input_fix_point, frame)
        input_view = np.asarray(self.input_buffers[0])
        if input_view.shape != input_data.shape:
            raise RuntimeError(f"GraphRunner input buffer shape {input_view.shape} does not match {input_data.shape}")
        if not np.issubdtype(input_view.dtype, np.signedinteger):
            raise RuntimeError(f"GraphRunner YOLOv8 input must be signed INT8, got {input_view.dtype}")
        input_view[...] = input_data
        _sync_buffer(self.input_buffers[0], "write", input_view)
        job_id = self.runner.execute_async(self.input_buffers, self.output_buffers)
        status = self.runner.wait(job_id)
        if status not in (0, None):
            raise RuntimeError(f"GraphRunner job {job_id} failed with status {status}")
        values: dict[str, np.ndarray] = {}
        for name, buffer, tensor in zip(self.output_names, self.output_buffers, self.output_tensors):
            raw = np.asarray(buffer)
            _sync_buffer(buffer, "read", raw)
            values[name] = raw.astype(np.float32, copy=True) / float(2 ** _tensor_fix_point(tensor))
        return values

    def infer(self, frame: np.ndarray) -> list[dict[str, object]]:
        if self.decoder is None:
            raise RuntimeError("no model-specific GraphRunner decoder is registered")
        height, width = frame.shape[:2]
        return self.decoder(self.infer_tensors(frame), width, height)


class VartYoloV8:
    """Run one compiled B512 DPU graph and expose its real output tensors.

    ``infer_tensors`` is usable once VART/XIR and an exact `.xmodel` exist.
    ``infer`` additionally needs a decoder bound to the compiled graph's real
    output tensors; it otherwise raises rather than returning guessed boxes.
    """

    def __init__(self, runner: Any, input_tensor: Any, output_tensors: list[Any], *,
                 confidence_threshold: float = .30, nms_threshold: float = .45,
                 decoder: Decoder | None = None) -> None:
        dimensions = tuple(int(value) for value in input_tensor.dims)
        if len(dimensions) != 4 or dimensions[0] != 1 or dimensions[-1] != 3:
            raise ValueError("VART YOLOv8 input must be batch-one NHWC RGB")
        if not output_tensors:
            raise ValueError("VART graph has no output tensors")
        self.runner = runner
        self.input_tensor = input_tensor
        self.output_tensors = list(output_tensors)
        self.input_shape = dimensions
        self.input_fix_point = _tensor_fix_point(input_tensor)
        self.output_names = [_tensor_name(tensor, index)
                             for index, tensor in enumerate(output_tensors)]
        if len(set(self.output_names)) != len(self.output_names):
            raise ValueError("VART graph output tensor names must be unique")
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.decoder = decoder

    @classmethod
    def from_runner(cls, runner: Any, *, input_tensor: Any, output_tensors: list[Any],
                    confidence_threshold: float = .30, nms_threshold: float = .45,
                    decoder: Decoder | None = None) -> "VartYoloV8":
        """Construct from injected tensors; used by hardware-free contract tests."""
        return cls(runner, input_tensor, output_tensors,
                   confidence_threshold=confidence_threshold, nms_threshold=nms_threshold,
                   decoder=decoder)

    @classmethod
    def from_xmodel(cls, xmodel: str | Path, *, confidence_threshold: float = .30,
                    nms_threshold: float = .45, decoder: Decoder | None = None) -> "VartYoloV8":
        """Load the only DPU subgraph from a compiled XIR model on the board."""
        path = Path(xmodel)
        if not path.is_file() or path.suffix != ".xmodel":
            raise FileNotFoundError(f"compiled .xmodel is required: {path}")
        try:
            import vart
            import xir
        except ImportError as error:
            raise RuntimeError("VART and XIR are required for the DPU backend") from error
        graph = xir.Graph.deserialize(str(path))
        root = graph.get_root_subgraph()
        dpu_subgraphs = []
        for subgraph in root.toposort_child_subgraph():
            try:
                device = subgraph.get_attr("device")
            except (AttributeError, RuntimeError):
                continue
            if str(device).upper() == "DPU":
                dpu_subgraphs.append(subgraph)
        if len(dpu_subgraphs) != 1:
            raise RuntimeError(f"expected exactly one DPU subgraph, found {len(dpu_subgraphs)}")
        runner = vart.Runner.create_runner(dpu_subgraphs[0], "run")
        return cls(runner, list(runner.get_input_tensors())[0],
                   list(runner.get_output_tensors()),
                   confidence_threshold=confidence_threshold, nms_threshold=nms_threshold,
                   decoder=decoder)

    def _quantized_input(self, frame: np.ndarray) -> np.ndarray:
        return _quantized_yolov8_input(self.input_shape, self.input_fix_point, frame)

    def infer_tensors(self, frame: np.ndarray) -> dict[str, np.ndarray]:
        """Run VART and return outputs converted from their fixed-point form."""
        input_data = self._quantized_input(frame)
        raw_outputs = [np.empty(tuple(int(value) for value in tensor.dims), dtype=np.int8)
                       for tensor in self.output_tensors]
        job_id = self.runner.execute_async([input_data], raw_outputs)
        status = self.runner.wait(job_id)
        if status not in (0, None):
            raise RuntimeError(f"VART job {job_id} failed with status {status}")
        return {
            name: raw.astype(np.float32) / float(2 ** _tensor_fix_point(tensor))
            for name, raw, tensor in zip(self.output_names, raw_outputs, self.output_tensors)
        }

    def infer(self, frame: np.ndarray) -> list[dict[str, object]]:
        """Return person detections only when a tested compiled-model decoder exists."""
        if self.decoder is None:
            raise RuntimeError(
                "no model-specific VART decoder is registered; inspect the compiled .xmodel "
                "outputs and bind a tested decoder before requesting person detections"
            )
        height, width = frame.shape[:2]
        return self.decoder(self.infer_tensors(frame), width, height)
