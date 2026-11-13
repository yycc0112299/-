# Two-board Cross-camera Fusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a deployable, conservative metadata-only cross-camera candidate association path for the future two-PYNQ-ZU DPU topology.

**Architecture:** The existing packet schema adds optional normalized two-region appearance features. A small receiver/fusion module retains the latest local and remote observations and reuses `CrossCameraMatcher` for repeated, unambiguous candidate labels. Runtime staging and bundle packaging receive the exact additional source set.

**Tech Stack:** Python 3.9, NumPy, OpenCV, TCP JSON protocol, PetaLinux recipe staging.

**Spec:** `docs/superpowers/specs/2026-11-14-two-board-cross-camera-fusion-design.md`

## Global Constraints

- Preserve `pynq-person-detections-v1` backward compatibility; appearance remains optional.
- Never transfer raw camera frames or use hard-coded board/network values.
- Emit candidates, not identity claims; local tracker IDs remain local.
- No SD image rebuild, board upload or hardware claim in this change.

## Review Focus

- A malformed or non-finite appearance vector must be rejected before fusion.
- Legacy packets without appearance must remain valid but must not match.
- Tentative local tracks must not produce cross-camera candidates.
- Missing remote evidence must break a pending candidate streak.
- Bundle/rootfs source lists must contain fusion dependencies but not the CPU ONNX model.

---

### Task 1: Appearance-carrying peer protocol

**Files:**
- Modify: `person_tracking/peer_protocol.py`
- Modify: `person_tracking/pynq_yolov8_peer.py`
- Create: `person_tracking/appearance_features.py`
- Test: `person_tracking/tests/test_peer_protocol.py`
- Test: `person_tracking/tests/test_yolov8_peer.py`

**Interfaces:**
- Produces optional detection field `appearance: list[list[float]]` with exactly two rows of fifteen finite, non-negative values normalized per row.
- Produces `appearance_features.appearance(frame, box) -> numpy.ndarray`.

- [ ] **Step 1: Write failing packet and sender tests** for valid 2×15 appearance round trip, malformed appearance rejection, and sender packet feature serialization.
- [ ] **Step 2: Run the focused tests** and confirm they fail because the field/helper is absent.
- [ ] **Step 3: Implement only validation, feature extraction and packet serialization** without changing local tracker IDs.
- [ ] **Step 4: Run focused and full person-tracking tests** and confirm pass.
- [ ] **Step 5: Commit task changes.**

### Task 2: Cross-camera fusion service

**Files:**
- Create: `person_tracking/pynq_cross_camera_fusion.py`
- Test: `person_tracking/tests/test_pynq_cross_camera_fusion.py`

**Interfaces:**
- Consumes normalized peer packets and `CrossCameraMatcher`.
- Produces `CrossCameraFusion.update_local(packet)` / `.update_remote(packet)` result dictionaries with candidate labels only.

- [ ] **Step 1: Write failing tests** for repeated unambiguous matches, missing appearance, tentative tracks, and a broken evidence streak.
- [ ] **Step 2: Run focused test** and confirm import failure.
- [ ] **Step 3: Implement the bounded latest-observation service and CLI JSON receiver mode.**
- [ ] **Step 4: Run focused and full person-tracking tests** and confirm pass.
- [ ] **Step 5: Commit task changes.**

### Task 3: Stage and document the future DPU fusion path

**Files:**
- Modify: `vitis/pynq_zu_dpu/linux/prepare_dpu_4_0_petalinux_project.py`
- Modify: `vitis/pynq_zu_dpu/linux/tests/test_prepare_dpu_4_0_petalinux_project.py`
- Modify: `live_site/prepare_pynq_dual_bundle.py`
- Modify: `live_site/tests/test_prepare_pynq_dual_bundle.py`
- Modify: `person_tracking/README.md`

**Interfaces:**
- Consumes Task 1/2 source files.
- Produces rootfs/bundle source lists containing fusion dependencies and no CPU ONNX model in DPU mode.

- [ ] **Step 1: Write failing staging/bundle tests** asserting fusion sources are shipped.
- [ ] **Step 2: Run focused tests** and confirm they fail against current lists.
- [ ] **Step 3: Add only required source files to staging and bundle lists; document start commands.**
- [ ] **Step 4: Run all FPGA/Linux/tracking/live-site tests** and confirm pass.
- [ ] **Step 5: Commit, update mandatory progress records, and push `main`.**
