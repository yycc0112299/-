"""Benchmark camera regression plus image-boundary correction on held-out EPFL frames."""
import json
from pathlib import Path
import numpy as np

from benchmark_box_stabilizers import iou, center_distance
from fit_epfl_box_regressor import fit


def evaluate(rows, models, clamp=None):
    matches = misses = false_positives = 0
    ious = []; centers = []; edges = []
    for row in rows:
        if row["frame"] % 5 != 0:
            continue
        boxes = []
        for raw in row["predicted_boxes"]:
            box = np.rint(np.array(list(raw) + [1]) @ models[row["camera"]]).astype(int).tolist()
            if clamp is not None and box[3] >= clamp:
                box[3] = 480
            boxes.append(box)
        used = set()
        for target in row["ground_truth_boxes"]:
            choices = [(iou(target, box), index) for index, box in enumerate(boxes) if index not in used]
            overlap, index = max(choices, default=(0, None))
            if overlap < .5:
                misses += 1
                continue
            used.add(index); matches += 1; ious.append(overlap)
            box = boxes[index]; centers.append(center_distance(target, box)); edges.append(max(abs(a-b) for a,b in zip(target, box)))
        false_positives += len(boxes) - len(used)
    return {"matches": matches, "misses": misses, "false_positives": false_positives,
            "recall": round(matches/(matches+misses),4), "precision": round(matches/(matches+false_positives),4),
            "mean_iou": round(sum(ious)/len(ious),4), "max_center_error_px": round(max(centers),4),
            "max_edge_error_px": max(edges), "center_under_20": max(centers)<20, "edge_under_20": max(edges)<20}


def run(source, output):
    rows = json.loads(Path(source).read_text(encoding="utf-8"))["cases_detail"]
    models = fit(rows, 100)
    results = {str(clamp): evaluate(rows, models, clamp) for clamp in (None, 420, 430, 440, 450, 460, 470)}
    Path(output).write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--source", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args(); run(args.source, args.output)
