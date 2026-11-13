# Two-board Cross-camera Fusion Design

## Intent

Prepare the later two-PYNQ-ZU topology while the SD card is unavailable. Each
board runs one UVC camera, a local YOLOv8 DPU GraphRunner detector and a local
short-term tracker. Boards exchange only compact person metadata over Wi-Fi;
they do not exchange camera frames.

## Goals

- Carry a stable, JSON-serializable two-region appearance descriptor with each
  confirmed local person observation.
- Associate local and remote confirmed observations conservatively, producing
  a cross-camera **candidate** label only after repeated unambiguous matches.
- Preserve local `track_id` ownership: cross-camera labels do not rewrite a
  board's tracker IDs and do not claim biometric identity.
- Make all files required by the future two-board DPU path available in the
  deployment bundle and PetaLinux runtime staging helper.

## Non-goals

- No face recognition, ReID neural network, calibration, raw video transport
  or physical Wi-Fi configuration.
- No claim that two physical boards, Wi-Fi, UVC or DPU inference has run.
- No regenerated SD image while the card cannot be written.

## Chosen approach

The existing `peer_protocol.py` schema remains version `v1` and adds an
optional `appearance` field to each detection. Old packets remain valid;
cross-camera association ignores detections without the field. The descriptor
is a normalized 2×15 upper/lower HSV/neutral histogram generated from the
existing project method, encoded as JSON lists.

The receiver maintains a bounded latest local and remote observation set and
uses the existing `CrossCameraMatcher` thresholds and repeated-hit policy. A
result is called a `candidate`, never a confirmed person identity. This is
backwards compatible, low bandwidth, and reuse of the project matcher avoids
an unverified second association algorithm.

## Constraints

- Python 3.9 standard library and the target's existing NumPy/OpenCV runtime.
- No camera index, Wi-Fi address, or board ID may be hard-coded.
- The GraphRunner DPU route must be selected explicitly with the compiled
  `/opt/models/yolov8n_b512.xmodel` when used on a target.
- Generated images, model binaries, logs and personal/network credentials are
  not committed.

## Acceptance evidence

- Protocol round trips valid appearance data and rejects malformed shapes or
  non-finite values.
- A real in-process fusion service requires confirmed observations with valid
  appearance, labels an unambiguous repeated pair, and resets a candidate when
  evidence disappears.
- The DPU deployment bundle and staging helper include every fusion runtime
  file and still exclude the CPU ONNX model.
- Host tests pass. Physical board evidence remains a later gate.
