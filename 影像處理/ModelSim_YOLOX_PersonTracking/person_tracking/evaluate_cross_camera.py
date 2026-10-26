"""Deterministic regression evaluation for the conservative appearance matcher."""
import json
from pathlib import Path

import numpy as np

from cross_camera import CrossCameraMatcher


def person(track_id, color, status="confirmed"):
    appearance = np.zeros((2, 15), dtype=float)
    appearance[:, color] = 1.0
    return {"track_id": track_id, "status": status, "appearance": appearance}


def run():
    cases = [
        ("same_color", [person(1, 2)], [person(7, 2)], True),
        ("different_color", [person(1, 2)], [person(7, 4)], False),
        ("ambiguous_competitor", [person(1, 2)], [person(7, 2), person(8, 2)], False),
    ]
    results = []
    for name, a, b, expected_confirmed in cases:
        matcher = CrossCameraMatcher(min_hits=3)
        observations = [matcher.update(a, b) for _ in range(3)]
        final = observations[-1]
        confirmed = bool(final and final[0]["status"] == "confirmed_candidate")
        results.append({"case": name, "confirmed": confirmed,
                        "expected_confirmed": expected_confirmed, "final": final})
        assert confirmed == expected_confirmed, results[-1]
    summary = {"cases": len(results), "passed": len(results), "results": results}
    output = Path(__file__).with_name("cross_camera_evaluation.json")
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"CROSS_CAMERA_EVALUATION_PASS cases={len(results)} output={output.name}")


if __name__ == "__main__":
    run()
