"""Loopback-only dual USB-camera tracking dashboard. Frames remain in memory."""
import argparse
import base64
import json
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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
        self.state = self._state("stopped", "尚未啟動雙鏡頭")
        threading.Thread(target=self.capture, daemon=True).start()
        threading.Thread(target=self.process, daemon=True).start()

    @staticmethod
    def _state(status, message):
        return dict(status=status, message=message, cameras=[0, 1], people=[[], []],
                    pairs=[], fps=0, latency_ms=0, frame_id=0)

    def control(self, enabled, camera_a=0, camera_b=1):
        if camera_a == camera_b:
            raise ValueError("請選擇兩個不同的鏡頭編號")
        with self.lock:
            self.enabled = enabled
            self.cameras = (camera_a, camera_b)
            self.epoch += 1
            self.raw = None
            self.images = [None, None]
            self.heartbeat = time.monotonic()
            self.state = self._state("connecting" if enabled else "stopped",
                                     "正在連接兩台 USB 攝影機…" if enabled else "雙鏡頭已停止")
            self.state["cameras"] = list(self.cameras)

    def snapshot(self):
        with self.lock:
            self.heartbeat = time.monotonic()
            return dict(self.state, images=list(self.images), enabled=self.enabled)

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
            self.server.engine.control(self.path == "/api/start", camera_a, camera_b)
        except (ValueError, TypeError):
            return self.send_body(400, {"error": "Invalid request; choose two different camera indexes"})
        if self.path not in {"/api/start", "/api/stop"}:
            return self.send_body(404, {"error": "Not found"})
        self.send_body(200, {"ok": True})


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
