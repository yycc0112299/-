"""Fit per-camera box-coordinate calibration on one split and test the other."""
import json
from pathlib import Path

import numpy as np

from benchmark_box_stabilizers import iou, center_distance


def pairs(row):
    used = set()
    result = []
    for target in row["ground_truth_boxes"]:
        candidates = [(iou(target, box), index) for index, box in enumerate(row["predicted_boxes"]) if index not in used]
        overlap, index = max(candidates, default=(0, None))
        if overlap >= .5:
            used.add(index); result.append((row["predicted_boxes"][index], target))
    return result


def fit(rows, ridge):
    models = {}
    for camera in range(6):
        samples = [(pred, target) for row in rows if row["camera"] == camera and row["frame"] % 5 != 0 for pred, target in pairs(row)]
        if not samples:
            models[camera] = np.eye(5, 4)
            continue
        x = np.array([list(pred) + [1] for pred, _ in samples], dtype=float)
        y = np.array([target for _, target in samples], dtype=float)
        normal = x.T @ x + ridge * np.eye(5)
        normal[-1, -1] -= ridge
        models[camera] = np.linalg.solve(normal, x.T @ y)
    return models


def evaluate(rows, models):
    matches = misses = false_positives = 0
    ious, centers, edges = [], [], []
    for row in rows:
        if row["frame"] % 5 != 0:
            continue
        predictions = [np.rint(np.array(list(box) + [1]) @ models[row["camera"]]).astype(int).tolist()
                       for box in row["predicted_boxes"]]
        used = set()
        for target in row["ground_truth_boxes"]:
            candidates = [(iou(target, box), index) for index, box in enumerate(predictions) if index not in used]
            overlap, index = max(candidates, default=(0, None))
            if overlap < .5:
                misses += 1; continue
            used.add(index); matches += 1; ious.append(overlap)
            box = predictions[index]; centers.append(center_distance(target, box)); edges.append(max(abs(a - b) for a, b in zip(target, box)))
        false_positives += len(predictions) - len(used)
    return {"matches": matches, "misses": misses, "false_positives": false_positives,
            "recall": round(matches / (matches + misses), 4),
            "precision": round(matches / (matches + false_positives), 4),
            "mean_iou": round(sum(ious) / len(ious), 4),
            "max_center_error_px": round(max(centers), 4), "mean_center_error_px": round(sum(centers) / len(centers), 4),
            "max_edge_error_px": max(edges), "center_under_20": max(centers) < 20}


def run(source, output):
    rows = json.loads(Path(source).read_text(encoding="utf-8"))["cases_detail"]
    results = {}
    for ridge in (0, 1, 10, 100):
        models = fit(rows, ridge)
        results[str(ridge)] = evaluate(rows, models)
    Path(output).write_text(json.dumps({"source": Path(source).name, "results": results}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default="epfl_box_regressor_benchmark.json")
    args = parser.parse_args()
    run(args.source, args.output)
