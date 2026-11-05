"""Search a camera calibration for box coordinates, then evaluate held-out frames."""
import itertools, json
from pathlib import Path


def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def transform(box, p):
    sx, sy, dx, dy = p
    return [round(sx * box[0] + dx), round(sy * box[1] + dy),
            round(sx * box[2] + dx), round(sy * box[3] + dy)]


def score(rows, params, split):
    errors, overlaps, misses, false_positives = [], [], 0, 0
    for row in rows:
        if split is not None and row["frame"] % 5 != split:
            continue
        if split is None and row["frame"] % 5 == 0:
            continue
        predictions = [transform(box, params[row["camera"]]) for box in row["predicted_boxes"]]
        used = set()
        for target in row["ground_truth_boxes"]:
            candidates = [(iou(target, box), index) for index, box in enumerate(predictions) if index not in used]
            overlap, index = max(candidates, default=(0, None))
            if overlap < .5:
                misses += 1
                continue
            used.add(index); overlaps.append(overlap)
            errors.append(max(abs(a - b) for a, b in zip(target, predictions[index])))
        false_positives += len(predictions) - len(used)
    return {"matches": len(errors), "misses": misses, "false_positives": false_positives,
            "max_error": max(errors) if errors else None,
            "mean_error": round(sum(errors) / len(errors), 4) if errors else None,
            "mean_iou": round(sum(overlaps) / len(overlaps), 4) if overlaps else None,
            "recall": round(len(errors) / (len(errors) + misses), 4) if errors or misses else 0,
            "precision": round(len(errors) / (len(errors) + false_positives), 4) if errors or false_positives else 0}


def run(source, output):
    rows = json.loads(Path(source).read_text(encoding="utf-8"))["cases_detail"]
    baseline = [(1, 1, 0, 0)] * 6
    params = [(1, 1, 0, 0)] * 6
    values = [(sx, sy, dx, dy) for sx, sy, dx, dy in itertools.product(
        (.94, .97, 1.0, 1.03, 1.06), (.94, .97, 1.0, 1.03, 1.06), range(-8, 9, 4), range(-8, 9, 4))]
    for camera in range(6):
        candidates = []
        for value in values:
            trial = list(params); trial[camera] = value
            result = score(rows, trial, None)
            candidates.append((result["max_error"] or 9999, result["misses"], -(result["mean_iou"] or 0), value, result))
        params[camera] = min(candidates)[3]
    result = {"baseline_validation": score(rows, baseline, 0),
              "calibrated_validation": score(rows, params, 0),
              "calibrated_training": score(rows, params, None),
              "camera_params": [list(p) for p in params],
              "split": "frame % 5 == 0 is validation; other frames are calibration"}
    Path(output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default="epfl_calibration_search.json")
    args = parser.parse_args()
    run(args.source, args.output)
