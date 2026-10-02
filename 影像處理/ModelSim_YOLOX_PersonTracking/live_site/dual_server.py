"""Loopback-only dual USB-camera dashboard with local person snapshots."""
import argparse
import base64
import json
import re
import sys
import threading
import time
import webbrowser
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np

ROOT = Path(__file__).resolve().parent
CAPTURE_ROOT = ROOT.parent / "person_tracking" / "live_captures"
sys.path.insert(0, str(ROOT.parent / "person_tracking"))
import pipeline as p
from cross_camera import CrossCameraMatcher
from dual_camera import appearance

FACE_CASCADE = p.cv2.CascadeClassifier(
    str(Path(p.cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))


def snapshot_quality(frame, box, confidence, check_face=True):
    """Score a person crop; frontal-face detection improves review photos only."""
    height, width = frame.shape[:2]
    x0, y0, x1, y1 = [int(n) for n in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)
    if x1 - x0 < 8 or y1 - y0 < 8:
        return None
    crop = frame[y0:y1, x0:x1]
    gray = p.cv2.cvtColor(crop, p.cv2.COLOR_BGR2GRAY)
    sharpness = float(p.cv2.Laplacian(gray, p.cv2.CV_64F).var())
    face_found = False
    if check_face and not FACE_CASCADE.empty() and crop.shape[0] >= 60 and crop.shape[1] >= 40:
        upper = gray[: max(1, int(gray.shape[0] * .65))]
        scale = min(1.0, 180 / max(upper.shape))
        resized = p.cv2.resize(upper, None, fx=scale, fy=scale) if scale < 1 else upper
        faces = FACE_CASCADE.detectMultiScale(resized, scaleFactor=1.1, minNeighbors=4,
                                               minSize=(18, 18))
        face_found = len(faces) > 0
    area = (x1 - x0) * (y1 - y0) / (width * height)
    complete = int(x0 > 2 and y0 > 2 and x1 < width - 2 and y1 < height - 2)
    quality = (1.5 * face_found + .8 * min(1.0, area / .30)
               + .35 * min(1.0, sharpness / 180) + .3 * complete
               + .25 * float(confidence))
    return crop, quality, face_found


class AppearanceHistory:
    """Smooth recent clothing features without retaining full video frames."""
    def __init__(self, length=5):
        self.length = length
        self.samples = {}

    def update(self, side, track_id, feature):
        key = (side, track_id)
        samples = self.samples.setdefault(key, deque(maxlen=self.length))
        samples.append(feature)
        return .5 * feature + .5 * np.mean(samples, axis=0)


class DualEngine:
    def __init__(self):
        self.lock = threading.RLock()
        self.enabled = False
        self.cameras = (0, 1)
        self.epoch = 0
        self.heartbeat = 0.0
        self.raw = None
        self.images = [None, None]
        self.capture_id = 0
        self.session_id = None
        self.photos = {}
        self.matched_pairs = {}
        self.photo_observations = {}
        self.latest_crops = {}
        self.state = self._state("stopped", "尚未啟動雙鏡頭")
        threading.Thread(target=self.capture, daemon=True).start()
        threading.Thread(target=self.process, daemon=True).start()

    @staticmethod
    def _state(status, message):
        return dict(status=status, message=message, cameras=[0, 1], people=[[], []],
                    pairs=[], fps=0, latency_ms=0, frame_id=0)

    def _manifest(self):
        if self.session_id is None:
            return
        data = dict(session=self.session_id, cameras=list(self.cameras),
                    people=list(self.photos.values()), pairs=list(self.matched_pairs.values()))
        (CAPTURE_ROOT / self.session_id / "manifest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_people_and_pairs(self, frames, observed, pairs, epoch):
        """Replace weak snapshots with better views and retain reviewable pairs."""
        candidates = []
        for camera, detections in enumerate(observed):
            side = "AB"[camera]
            for item in detections:
                if item["status"] != "confirmed":
                    continue
                track_id = int(item["track_id"])
                key = (side, track_id)
                counter_key = (epoch, side, track_id)
                count = self.photo_observations.get(counter_key, 0) + 1
                self.photo_observations[counter_key] = count
                candidate = snapshot_quality(frames[camera], item["box"],
                                             item.get("confidence", 0),
                                             check_face=(count == 1 or count % 3 == 0))
                if candidate is not None:
                    candidates.append((key, *candidate))
        with self.lock:
            if not self.enabled or self.epoch != epoch or self.session_id is None:
                return
            changed = False
            folder = CAPTURE_ROOT / self.session_id
            self.latest_crops = {key: (crop.copy(), quality, face_found, time.monotonic())
                                 for key, crop, quality, face_found in candidates}
            for (side, track_id), crop, quality, face_found in candidates:
                key = (side, track_id)
                current = self.photos.get(key)
                frozen = any(record.get("review") is not None and
                             (record["a_id"] == track_id if side == "A" else record["b_id"] == track_id)
                             for record in self.matched_pairs.values())
                if frozen or (current and (current.get("locked") or quality < current.get("quality", -1) + .08)):
                    continue
                ok, jpeg = p.cv2.imencode(".jpg", crop, [p.cv2.IMWRITE_JPEG_QUALITY, 90])
                if not ok:
                    continue
                filename = f"{side}_{track_id:04d}.jpg"
                (folder / filename).write_bytes(jpeg.tobytes())
                revision = (current or {}).get("revision", 0) + 1
                self.photos[key] = dict(camera=side, track_id=track_id,
                                        photo_url=f"/api/photo/{side}/{track_id}?v={revision}",
                                        file=filename, captured_at=datetime.now().isoformat(timespec="seconds"),
                                        revision=revision, quality=round(quality, 3), face_detected=face_found,
                                        locked=False)
                for record in self.matched_pairs.values():
                    if record["a_id"] == track_id and side == "A":
                        record["photo_a_url"] = self.photos[key]["photo_url"]
                    if record["b_id"] == track_id and side == "B":
                        record["photo_b_url"] = self.photos[key]["photo_url"]
                changed = True
            for pair in pairs:
                if pair["status"] != "confirmed_candidate" or not pair.get("pair_label"):
                    continue
                photo_a = self.photos.get(("A", pair["a_id"]))
                photo_b = self.photos.get(("B", pair["b_id"]))
                if not photo_a or not photo_b:
                    continue
                existing = next((record for record in self.matched_pairs.values()
                                 if record["a_id"] == pair["a_id"] and record["b_id"] == pair["b_id"]), None)
                if existing is not None:
                    if existing["score"] is None:
                        existing["score"] = pair["score"]
                        changed = True
                    continue
                label = pair["pair_label"]
                record = dict(pair_label=label, a_id=pair["a_id"], b_id=pair["b_id"],
                              score=pair["score"], source="auto", review=None,
                              photo_a_url=photo_a["photo_url"],
                              photo_b_url=photo_b["photo_url"],
                              matched_at=datetime.now().isoformat(timespec="seconds"))
                if label not in self.matched_pairs:
                    self.matched_pairs[label] = record
                    changed = True
            if changed:
                self._manifest()

    def add_manual_pair(self, a_id, b_id):
        with self.lock:
            if self.session_id is None or ("A", a_id) not in self.photos or ("B", b_id) not in self.photos:
                raise ValueError("Select two saved person photos from the current session")
            for record in self.matched_pairs.values():
                if record["a_id"] == a_id and record["b_id"] == b_id:
                    return record
            number = 1 + sum(label.startswith("M") for label in self.matched_pairs)
            label = f"M{number}"
            record = dict(pair_label=label, a_id=a_id, b_id=b_id, score=None,
                          source="manual", review=None,
                          photo_a_url=self.photos[("A", a_id)]["photo_url"],
                          photo_b_url=self.photos[("B", b_id)]["photo_url"],
                          matched_at=datetime.now().isoformat(timespec="seconds"))
            self.matched_pairs[label] = record
            self._manifest()
            return record

    def review_pair(self, label, decision):
        with self.lock:
            if decision not in {"same", "different"} or label not in self.matched_pairs:
                raise ValueError("Unknown pair or review decision")
            record = self.matched_pairs[label]
            record["review"] = decision
            record["reviewed_at"] = datetime.now().isoformat(timespec="milliseconds")
            self._manifest()
            return record

    def retake_photo(self, side, track_id):
        """Let the user choose the current processed view, then hold it for review."""
        with self.lock:
            key = (side, track_id)
            record = self.photos.get(key)
            recent = self.latest_crops.get(key)
            if self.session_id is None or not self.enabled or record is None or recent is None:
                raise ValueError("Person is not visible in the current camera analysis")
            crop, quality, face_found, captured = recent
            if time.monotonic() - captured > 3:
                raise ValueError("Current person frame is too old")
            if any(pair.get("review") is not None and
                   (pair["a_id"] == track_id if side == "A" else pair["b_id"] == track_id)
                   for pair in self.matched_pairs.values()):
                raise ValueError("Reviewed pair photos cannot be changed")
            ok, jpeg = p.cv2.imencode(".jpg", crop, [p.cv2.IMWRITE_JPEG_QUALITY, 90])
            if not ok:
                raise ValueError("Could not encode the current person frame")
            (CAPTURE_ROOT / self.session_id / record["file"]).write_bytes(jpeg.tobytes())
            record.update(revision=record["revision"] + 1,
                          photo_url=f"/api/photo/{side}/{track_id}?v={record['revision'] + 1}",
                          captured_at=datetime.now().isoformat(timespec="seconds"),
                          quality=round(quality, 3), face_detected=face_found,
                          locked=True)
            for pair in self.matched_pairs.values():
                if side == "A" and pair["a_id"] == track_id:
                    pair["photo_a_url"] = record["photo_url"]
                if side == "B" and pair["b_id"] == track_id:
                    pair["photo_b_url"] = record["photo_url"]
            self._manifest()
            return record

    def photo(self, side, track_id):
        with self.lock:
            record = self.photos.get((side, track_id))
            if record is None or self.session_id is None:
                return None
            return (CAPTURE_ROOT / self.session_id / record["file"]).read_bytes()

    def control(self, enabled, camera_a=0, camera_b=1):
        if camera_a == camera_b:
            raise ValueError("請選擇兩個不同的鏡頭編號")
        with self.lock:
            if enabled:
                self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                (CAPTURE_ROOT / self.session_id).mkdir(parents=True, exist_ok=False)
                self.photos = {}
                self.matched_pairs = {}
                self.photo_observations = {}
                self.latest_crops = {}
            self.enabled = enabled
            self.cameras = (camera_a, camera_b)
            self.epoch += 1
            self.raw = None
            self.images = [None, None]
            self.heartbeat = time.monotonic()
            self.state = self._state("connecting" if enabled else "stopped",
                                     "正在連接兩台 USB 攝影機…" if enabled else "雙鏡頭已停止")
            self.state["cameras"] = list(self.cameras)
            if enabled:
                self._manifest()

    def stop_and_clear(self, camera_a=0, camera_b=1):
        """Stop and clear app-named person JPEGs from current and older sessions."""
        with self.lock:
            self.control(False, camera_a, camera_b)
            if CAPTURE_ROOT.is_symlink():
                raise ValueError("Capture root must not be a link")
            root = CAPTURE_ROOT.resolve()
            current = self.session_id
            deleted = 0
            if CAPTURE_ROOT.is_dir():
                for folder in CAPTURE_ROOT.iterdir():
                    if (folder.is_symlink() or not folder.is_dir() or
                            re.fullmatch(r"[0-9]{8}_[0-9]{6}_[0-9]{6}", folder.name) is None or
                            folder.resolve().parent != root):
                        continue
                    manifest_path = folder / "manifest.json"
                    if not manifest_path.is_file() or manifest_path.is_symlink():
                        continue
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        if manifest.get("session") != folder.name or not isinstance(manifest.get("people"), list):
                            continue
                    except (OSError, ValueError, AttributeError):
                        continue
                    filenames = {record.get("file") for record in manifest["people"] if isinstance(record, dict)}
                    for name in filenames:
                        if not isinstance(name, str) or re.fullmatch(r"[AB]_[0-9]{4,}\.jpg", name) is None:
                            continue
                        photo = folder / name
                        if photo.is_file() or photo.is_symlink():
                            photo.unlink()
                            deleted += 1
                    if folder.name == current:
                        (folder / "manifest.json").unlink(missing_ok=True)
                        try:
                            folder.rmdir()  # Leave any unregistered file untouched.
                        except OSError:
                            pass
            self.photos = {}
            self.matched_pairs = {}
            self.photo_observations = {}
            self.latest_crops = {}
            self.session_id = None
            self.state["message"] = f"雙鏡頭已停止；已清除本次及舊工作階段的 {deleted} 張人物照片"
            return deleted

    def snapshot(self):
        with self.lock:
            self.heartbeat = time.monotonic()
            return dict(self.state, images=list(self.images), enabled=self.enabled,
                        session=self.session_id, saved_people=list(self.photos.values()),
                        matched_pairs=list(self.matched_pairs.values()))

    def capture(self):
        while True:
            with self.lock:
                active, epoch, indexes = self.enabled, self.epoch, self.cameras
                if active and time.monotonic() - self.heartbeat > 10:
                    self.control(False, *indexes)
                    active = False
            if not active:
                time.sleep(.1)
                continue
            caps = []
            last_encoded = 0.0
            try:
                for index in indexes:
                    cap = p.cv2.VideoCapture(index, p.cv2.CAP_DSHOW)
                    caps.append(cap)
                    if not cap.isOpened():
                        raise RuntimeError(f"鏡頭 {index} 無法開啟；請確認沒有被其他程式使用")
                    cap.set(p.cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(p.cv2.CAP_PROP_FRAME_HEIGHT, 480)
                while True:
                    with self.lock:
                        if not self.enabled or self.epoch != epoch:
                            break
                    if not all(cap.grab() for cap in caps):
                        raise RuntimeError("雙鏡頭擷取中斷")
                    frames = []
                    for cap in caps:
                        ok, frame = cap.retrieve()
                        if not ok or frame.shape != (480, 640, 3):
                            raise RuntimeError("兩台鏡頭都必須輸出原生 640 × 480")
                        frames.append(frame)
                    now = time.monotonic()
                    images = None
                    if now - last_encoded >= .1:
                        images = []
                        for frame in frames:
                            ok, jpg = p.cv2.imencode(".jpg", frame, [p.cv2.IMWRITE_JPEG_QUALITY, 70])
                            if not ok:
                                raise RuntimeError("影像編碼失敗")
                            images.append(base64.b64encode(jpg).decode("ascii"))
                        last_encoded = now
                    with self.lock:
                        if self.epoch == epoch:
                            self.capture_id += 1
                            self.raw = (frames, now, epoch, self.capture_id)
                            if images is not None:
                                self.images = images
                            self.state.update(frame_id=self.capture_id, cameras=list(indexes))
            except Exception as error:
                with self.lock:
                    if self.epoch == epoch:
                        self.images = [None, None]
                        self.state = self._state("waiting", str(error))
                        self.state["cameras"] = list(indexes)
                time.sleep(2)
            finally:
                for cap in caps:
                    cap.release()

    def process(self):
        detector = None
        trackers = None
        matcher = None
        appearance_history = None
        seen = -1
        generation = -1
        last = time.monotonic()
        while True:
            with self.lock:
                raw, active = self.raw, self.enabled
            if not active or raw is None or raw[3] == seen:
                time.sleep(.02)
                continue
            frames, stamp, epoch, frame_id = raw
            seen = frame_id
            try:
                if detector is None:
                    detector = p.Detector()
                if epoch != generation:
                    trackers, matcher, generation = [p.Tracker(), p.Tracker()], CrossCameraMatcher(), epoch
                    appearance_history = AppearanceHistory()
                    last = time.monotonic()
                started = time.monotonic()
                observed = []
                for camera, frame in enumerate(frames):
                    detections = trackers[camera].update(detector.detect(frame))
                    for item in detections:
                        feature = appearance(frame, item["box"])
                        item["appearance"] = appearance_history.update(camera, item["track_id"], feature)
                    observed.append(detections)
                with self.lock:
                    excluded = {(record["a_id"], record["b_id"])
                                for record in self.matched_pairs.values() if record.get("review") == "different"}
                pairs = matcher.update(*observed, excluded_pairs=excluded)
                self.save_people_and_pairs(frames, observed, pairs, epoch)
                people = []
                for camera, frame in enumerate(frames):
                    clean = []
                    for item in observed[camera]:
                        clean.append({key: value for key, value in item.items() if key not in {"hist", "appearance"}})
                    people.append(clean)
                now = time.monotonic()
                with self.lock:
                    if self.enabled and self.epoch == epoch:
                        self.state.update(status="live", message="雙鏡頭追蹤中；P 標籤只代表外觀候選",
                                          people=people, pairs=pairs, fps=round(1 / max(.001, now - last), 1),
                                          latency_ms=round((now - stamp) * 1000),
                                          cameras=list(self.cameras), inference_ms=round((now - started) * 1000))
                        last = now
            except Exception as error:
                with self.lock:
                    if self.epoch == epoch:
                        self.images = [None, None]
                        self.state.update(status="error", message="偵測暫時無法執行：" + str(error), people=[[], []], pairs=[])
                time.sleep(2)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def allowed(self):
        hosts = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin", f"http://127.0.0.1:{self.server.server_port}")
        return self.headers.get("Host") in hosts and origin in {"http://" + host for host in hosts}

    def send_body(self, code, body, kind="application/json; charset=utf-8"):
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        if not self.allowed():
            return self.send_body(403, {"error": "Local origin required"})
        if self.path == "/api/health":
            return self.send_body(200, {"app": "usb-dual-person-live", "version": 1})
        if self.path == "/api/live":
            return self.send_body(200, self.server.engine.snapshot())
        photo = re.fullmatch(r"/api/photo/([AB])/([1-9][0-9]*)", urlsplit(self.path).path)
        if photo:
            body = self.server.engine.photo(photo.group(1), int(photo.group(2)))
            return self.send_body(200, body, "image/jpeg") if body is not None else self.send_body(404, {"error": "Not found"})
        if self.path == "/":
            return self.send_body(200, (ROOT / "dual_index.html").read_bytes(), "text/html; charset=utf-8")
        self.send_body(404, {"error": "Not found"})

    def do_POST(self):
        if not self.allowed():
            return self.send_body(403, {"error": "Local origin required"})
        if self.headers.get("Content-Type") != "application/json":
            return self.send_body(415, {"error": "JSON required"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size < 1024:
                raise ValueError()
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError()
            if self.path in {"/api/start", "/api/stop"}:
                camera_a, camera_b = data.get("camera_a", 0), data.get("camera_b", 1)
                if type(camera_a) is not int or type(camera_b) is not int or not all(0 <= item <= 9 for item in (camera_a, camera_b)):
                    raise ValueError()
                if self.path == "/api/start":
                    self.server.engine.control(True, camera_a, camera_b)
                    result = {"ok": True}
                else:
                    result = {"ok": True, "deleted_photos": self.server.engine.stop_and_clear(camera_a, camera_b)}
            elif self.path == "/api/manual_pair":
                a_id, b_id = data.get("a_id"), data.get("b_id")
                if type(a_id) is not int or type(b_id) is not int or min(a_id, b_id) < 1:
                    raise ValueError()
                result = {"ok": True, "pair": self.server.engine.add_manual_pair(a_id, b_id)}
            elif self.path == "/api/review":
                label, decision = data.get("pair_label"), data.get("decision")
                if not isinstance(label, str) or not re.fullmatch(r"[PM][1-9][0-9]*", label):
                    raise ValueError()
                result = {"ok": True, "pair": self.server.engine.review_pair(label, decision)}
            elif self.path == "/api/retake":
                side, track_id = data.get("camera"), data.get("track_id")
                if side not in {"A", "B"} or type(track_id) is not int or track_id < 1:
                    raise ValueError()
                result = {"ok": True, "photo": self.server.engine.retake_photo(side, track_id)}
            else:
                return self.send_body(404, {"error": "Not found"})
        except (ValueError, TypeError):
            return self.send_body(400, {"error": "Invalid camera, photo selection, or review request"})
        except OSError:
            return self.send_body(500, {"error": "Could not clear all saved photos; check the local capture folder"})
        self.send_body(200, result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    server.engine = DualEngine()
    url = f"http://127.0.0.1:{args.port}/"
    print("READY " + url, flush=True)
    if args.browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        server.engine.control(False, *server.engine.cameras)
        server.server_close()


if __name__ == "__main__":
    main()
