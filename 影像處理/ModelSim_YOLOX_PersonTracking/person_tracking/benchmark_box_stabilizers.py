"""Compare raw boxes with simple temporal box stabilizers on saved EPFL output."""
import json, math
from pathlib import Path


def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x1 - x0) * max(0, y1 - y0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0


def center_distance(a, b):
    return math.hypot((a[0] + a[2] - b[0] - b[2]) / 2, (a[1] + a[3] - b[1] - b[3]) / 2)


def smooth_rows(rows, method):
    output, tracks, histories = [], {}, {}
    for row in sorted(rows, key=lambda x: (x["camera"], x["frame"])):
        if row["camera"] not in tracks:
            tracks[row["camera"]], histories[row["camera"]] = {}, {}
        active, active_history = tracks[row["camera"]], histories[row["camera"]]
        boxes = []
        for raw in row["predicted_boxes"]:
            candidates = [(center_distance(raw, previous), track_id) for track_id, previous in active.items()
                          if iou(raw, previous) > .05 or center_distance(raw, previous) < 100]
            if candidates:
                _, track_id = min(candidates)
            else:
                track_id = max(active, default=0) + 1
            previous = active.get(track_id, raw)
            history = active_history.setdefault(track_id, [])
            if method.startswith("ema"):
                alpha = float(method[3:])
                box = [round(alpha * current + (1 - alpha) * old) for current, old in zip(raw, previous)]
            elif method == "median3":
                values = (history + [raw])[-3:]
                box = [round(sorted(value[index] for value in values)[len(values) // 2]) for index in range(4)]
            else:
                box = raw
            active[track_id] = box
            active_history[track_id] = (history + [raw])[-3:]
            boxes.append(box)
        output.append({**row, "predicted_boxes": boxes})
    return output


def evaluate(rows):
    matches = misses = false_positives = 0
    center_errors, edge_errors, overlaps = [], [], []
    for row in rows:
        used = set()
        for target in row["ground_truth_boxes"]:
            candidates = [(iou(target, box), index) for index, box in enumerate(row["predicted_boxes"]) if index not in used]
            overlap, index = max(candidates, default=(0, None))
            if overlap < .5:
                misses += 1
                continue
            used.add(index); matches += 1; overlaps.append(overlap)
            box = row["predicted_boxes"][index]
            center_errors.append(center_distance(target, box))
            edge_errors.append(max(abs(a - b) for a, b in zip(target, box)))
        false_positives += len(row["predicted_boxes"]) - len(used)
    return {"matches": matches, "misses": misses, "false_positives": false_positives,
            "recall": round(matches / (matches + misses), 4),
            "precision": round(matches / (matches + false_positives), 4),
            "mean_iou": round(sum(overlaps) / len(overlaps), 4),
            "max_center_error_px": round(max(center_errors), 4),
            "mean_center_error_px": round(sum(center_errors) / len(center_errors), 4),
            "max_edge_error_px": max(edge_errors),
            "center_under_20": max(center_errors) < 20}


def run(source, output):
    rows = json.loads(Path(source).read_text(encoding="utf-8"))["cases_detail"]
    methods = ["raw", "ema0.25", "ema0.5", "ema0.75", "median3"]
    results = {method: evaluate(smooth_rows(rows, method)) for method in methods}
    Path(output).write_text(json.dumps({"source": Path(source).name, "results": results}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default="box_stabilizer_benchmark.json")
    args = parser.parse_args()
    run(args.source, args.output)
