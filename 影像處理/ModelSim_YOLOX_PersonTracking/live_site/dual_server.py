"""Loopback-only dual USB-camera dashboard with local person snapshots."""
import argparse
import base64
import json
import re
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE_ROOT = ROOT.parent / "person_tracking" / "live_captures"
sys.path.insert(0, str(ROOT.parent / "person_tracking"))
import pipeline as p
from cross_camera import CrossCameraMatcher
from dual_camera import appearance


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
        """Store one crop per confirmed local track and retain confirmed P candidates."""
        with self.lock:
            if not self.enabled or self.epoch != epoch or self.session_id is None:
                return
            changed = False
            folder = CAPTURE_ROOT / self.session_id
            for camera, detections in enumerate(observed):
                frame = frames[camera]
                height, width = frame.shape[:2]
                side = "AB"[camera]
                for item in detections:
                    track_id = int(item["track_id"])
                    key = (side, track_id)
                    if item["status"] != "confirmed" or key in self.photos:
                        continue
                    x0, y0, x1, y1 = [int(n) for n in item["box"]]
                    x0, y0 = max(0, x0), max(0, y0)
                    x1, y1 = min(width, x1), min(height, y1)
                    if x1 - x0 < 8 or y1 - y0 < 8:
                        continue
                    ok, jpeg = p.cv2.imencode(".jpg", frame[y0:y1, x0:x1],
                                              [p.cv2.IMWRITE_JPEG_QUALITY, 90])
                    if not ok:
                        continue
                    filename = f"{side}_{track_id:04d}.jpg"
                    (folder / filename).write_bytes(jpeg.tobytes())
                    self.photos[key] = dict(camera=side, track_id=track_id,
                                            photo_url=f"/api/photo/{side}/{track_id}",
                                            file=filename, captured_at=datetime.now().isoformat(timespec="seconds"))
                    changed = True
            for pair in pairs:
                if pair["status"] != "confirmed_candidate" or not pair.get("pair_label"):
                    continue
                photo_a = self.photos.get(("A", pair["a_id"]))
                photo_b = self.photos.get(("B", pair["b_id"]))
                if not photo_a or not photo_b:
                    continue
                label = pair["pair_label"]
                record = dict(pair_label=label, a_id=pair["a_id"], b_id=pair["b_id"],
                              score=pair["score"], photo_a_url=photo_a["photo_url"],
                              photo_b_url=photo_b["photo_url"],
                              matched_at=datetime.now().isoformat(timespec="seconds"))
                if label not in self.matched_pairs:
                    self.matched_pairs[label] = record
                    changed = True
            if changed:
                self._manifest()

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
        """Stop and delete only JPEGs registered for this session plus its manifest."""
        with self.lock:
            self.control(False, camera_a, camera_b)
            if self.session_id is None:
                self.state["message"] = "雙鏡頭已停止；本次沒有保存的照片"
                return 0
            if re.fullmatch(r"[0-9]{8}_[0-9]{6}_[0-9]{6}", self.session_id) is None:
                raise ValueError("Invalid capture session")
            folder = CAPTURE_ROOT / self.session_id
            filenames = {record["file"] for record in self.photos.values()}
            if any(re.fullmatch(r"[AB]_[0-9]{4,}\.jpg", name) is None for name in filenames):
                raise ValueError("Invalid capture filename")
            deleted = 0
            for name in filenames:
                photo = folder / name
                if photo.exists() or photo.is_symlink():
                    photo.unlink()
                    deleted += 1
            (folder / "manifest.json").unlink(missing_ok=True)
            try:
                folder.rmdir()  # Leave any unregistered file untouched.
            except OSError:
                pass
            self.photos = {}
            self.matched_pairs = {}
            self.session_id = None
            self.state["message"] = f"雙鏡頭已停止；已清除本次保存的 {deleted} 張照片"
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
                    last = time.monotonic()
                started = time.monotonic()
                observed = []
                for camera, frame in enumerate(frames):
                    detections = trackers[camera].update(detector.detect(frame))
                    for item in detections:
                        item["appearance"] = appearance(frame, item["box"])
                    observed.append(detections)
                pairs = matcher.update(*observed)
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
        photo = re.fullmatch(r"/api/photo/([AB])/([1-9][0-9]*)", self.path)
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
            camera_a, camera_b = data.get("camera_a", 0), data.get("camera_b", 1)
            if type(camera_a) is not int or type(camera_b) is not int or not all(0 <= item <= 9 for item in (camera_a, camera_b)):
                raise ValueError()
            if self.path == "/api/start":
                self.server.engine.control(True, camera_a, camera_b)
                result = {"ok": True}
            elif self.path == "/api/stop":
                result = {"ok": True, "deleted_photos": self.server.engine.stop_and_clear(camera_a, camera_b)}
            else:
                return self.send_body(404, {"error": "Not found"})
        except (ValueError, TypeError):
            return self.send_body(400, {"error": "Invalid request; choose two different camera indexes"})
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
