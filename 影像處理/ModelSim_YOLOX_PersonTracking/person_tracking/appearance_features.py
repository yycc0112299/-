"""Small, serializable appearance descriptor for conservative cross-camera candidates."""

from __future__ import annotations

import cv2
import numpy as np


APPEARANCE_REGIONS = 2
APPEARANCE_BINS = 15


def appearance(frame: np.ndarray, box: list[int]) -> np.ndarray:
    """Return normalized upper/lower 15-bin descriptors for one detected person box."""
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("frame must be a BGR HxWx3 image")
    if len(box) != 4:
        raise ValueError("box must have four coordinates")
    x0, y0, x1, y1 = (int(value) for value in box)
    if not (0 <= x0 < x1 <= frame.shape[1] and 0 <= y0 < y1 <= frame.shape[0]):
        raise ValueError("box is outside the frame")
    margin = (x1 - x0) // 5
    roi = frame[y0:y1, x0 + margin:x1 - margin]
    if roi.size == 0:
        raise ValueError("box is too narrow for an appearance descriptor")
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV).astype(np.float32)
    split = max(1, hsv.shape[0] // 2)
    rows: list[np.ndarray] = []
    for part in (hsv[:split], hsv[split:]):
        if part.size == 0:
            part = hsv[:split]
        hue, saturation, value = (channel.ravel() for channel in cv2.split(part))
        neutral = np.clip((80 - saturation) / 40, 0, 1)
        neutral = np.maximum(neutral, np.clip((65 - value) / 30, 0, 1))
        dark = np.clip((150 - value) / 80, 0, 1)
        light = np.clip((value - 150) / 80, 0, 1)
        histogram = np.zeros(APPEARANCE_BINS, dtype=float)
        histogram[0] = np.sum(neutral * dark)
        histogram[1] = np.sum(neutral * (1 - dark - light))
        histogram[2] = np.sum(neutral * light)
        hue_position = hue / 15
        left = np.floor(hue_position).astype(np.int32) % 12
        fraction = hue_position - np.floor(hue_position)
        chromatic = 1 - neutral
        histogram[3:] += np.bincount(left, weights=chromatic * (1 - fraction), minlength=12)
        histogram[3:] += np.bincount((left + 1) % 12, weights=chromatic * fraction, minlength=12)
        histogram /= max(float(histogram.sum()), 1e-12)
        rows.append(histogram)
    return np.asarray(rows)
