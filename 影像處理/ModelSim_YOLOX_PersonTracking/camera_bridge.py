"""Capture locally, preserve frames, and run adjacent-frame RTL comparison."""
import argparse
import csv
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'camera_deps'))
import cv2
import numpy as np

def write_report(session, rows, records):
    similar = sum(int(row['color_similar']) for row in rows)
    cards = ''.join(f'<figure><img loading="lazy" src="frames/frame_{r["frame"]:06}.png">'
                    f'<figcaption>影格 {r["frame"]} · {r["seconds"]:.3f} 秒</figcaption></figure>' for r in records)
    table = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(row[key]))}</td>' for key in
                    ('frame_a','frame_b','feature_a','feature_b','color_similar')) + '</tr>' for row in rows)
    (session / 'report.html').write_text(f'''<!doctype html><meta charset="utf-8">
<title>USB 攝影機 × ModelSim 逐幀比對</title>
<style>body{{font:16px sans-serif;max-width:1200px;margin:32px auto;padding:20px;background:#f3f5f9;color:#182339}}
.gallery{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}figure{{margin:0;background:white;padding:10px}}
img{{width:100%}}table{{border-collapse:collapse;width:100%;background:white}}td,th{{padding:8px;border:1px solid #ccd3df}}
</style><h1>USB 攝影機 → ModelSim 逐幀比對</h1>
<p>{len(records)} 張真實照片、{len(rows)} 組相鄰影格；{similar} 組顏色相似，{len(rows)-similar} 組不相似。</p>
<p>以完整 640×480（307,200 像素）計算上下半部主色與比例，沒有縮圖，尚未做人物偵測。1 代表顏色特徵相似，不能據此確認人物身分。</p>
<h2>原始影格</h2><div class="gallery">{cards}</div><h2>ModelSim 比對結果</h2>
<table><tr><th>A 影格</th><th>B 影格</th><th>A 特徵 (hex)</th><th>B 特徵 (hex)</th><th>顏色相似</th></tr>{table}</table>''', encoding='utf-8')

def reference_feature(rgb):
    bins = [[0]*8, [0]*8]
    half = rgb.shape[1] * (rgb.shape[0]//2)
    for index, pixel in enumerate(rgb.reshape(-1, 3)):
        r, g, b = map(int, pixel)
        mx, mn = max(r, g, b), min(r, g, b)
        if mx < 35: c = 0
        elif mx >= 170 and mx-mn < 45: c = 1
        elif r > 140 and g > 120 and b < 90: c = 5
        elif r > g > b and r > 80 and g-b > 20: c = 6
        elif r > g+35 and r > b+35: c = 2
        elif g > r+30 and g > b+30: c = 3
        elif b > r+30 and b > g+30: c = 4
        else: c = 7
        bins[0 if index < half else 1][c] += 1
    colors = [max(range(8), key=lambda c: histogram[c]) for histogram in bins]
    ratios = [max(histogram)*100//sum(histogram) for histogram in bins]
    return (colors[0]<<20) | (colors[1]<<16) | (ratios[0]<<8) | ratios[1]

def save_image(path, frame):
    ok, data = cv2.imencode('.png', frame)
    if not ok:
        raise RuntimeError('PNG encoding failed')
    data.tofile(str(path))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--frames', type=int, default=90)
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--input-session', type=Path, help='Replay original PNG frames without opening the camera')
    args = parser.parse_args()
    if not 2 <= args.frames <= 3000:
        parser.error('--frames must be between 2 and 3000')
    cap = None
    if not args.input_session:
        cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f'Cannot open camera {args.camera}. Check Windows camera permission and close other camera apps.')
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    try:
        if args.probe and cap is not None:
            ok, frame = cap.read()
            if not ok:
                raise RuntimeError('Camera opened but did not deliver a frame')
            print(json.dumps({'camera': args.camera, 'width': frame.shape[1], 'height': frame.shape[0], 'backend': cap.getBackendName()}))
            return
        session = ROOT / 'camera_runs' / time.strftime('%Y%m%d_%H%M%S')
        session.mkdir(parents=True, exist_ok=False)
        images = session / 'frames'
        images.mkdir()
        records = []
        expected_features = []
        start = time.perf_counter()
        with (session / 'pixels.rgb').open('wb') as mem:
            for index in range(args.frames):
                if cap is not None:
                    ok, frame = cap.read()
                else:
                    original = args.input_session / 'frames' / f'frame_{index:06}.png'
                    frame = cv2.imdecode(np.fromfile(str(original), dtype=np.uint8), cv2.IMREAD_COLOR)
                    ok = frame is not None
                timestamp = time.perf_counter() - start
                if not ok:
                    raise RuntimeError(f'Capture failed at frame {index}; incomplete session: {session}')
                if frame.shape[:2] != (480, 640):
                    raise RuntimeError(f'Expected native 640x480, got {frame.shape[1]}x{frame.shape[0]}; no resizing performed')
                save_image(images / f'frame_{index:06}.png', frame)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                expected_features.append(reference_feature(rgb))
                mem.write(rgb.tobytes())
                records.append({'frame': index, 'seconds': timestamp, 'width': frame.shape[1], 'height': frame.shape[0]})
                if (index+1) % 30 == 0:
                    print(f'Captured {index+1}/{args.frames}', flush=True)
    finally:
        if cap is not None:
            cap.release()
    (session / 'manifest.json').write_text(json.dumps({
        'camera': args.camera, 'mode': 'adjacent_full_frame_color',
        'person_detection': False, 'rgb_width': 640, 'rgb_height': 480,
        'pixels_per_frame': 307200, 'resized': False,
        'input_session': str(args.input_session) if args.input_session else None,
        'frames': records,
        'note': 'Times are processing receipt times (replay times for input-session). All pixels are processed; camera/driver may drop frames.'
    }, indent=2), encoding='utf-8')
    run_dir = Path(tempfile.mkdtemp(prefix='camera_rtl_'))
    for name in ('color_feature_stream.v', 'tb_camera_file.v'):
        shutil.copy2(ROOT / name, run_dir / name)
    shutil.copy2(session / 'pixels.rgb', run_dir / 'pixels.rgb')
    (run_dir / 'camera.do').write_text(
        'onerror {quit -code 1 -force}\n'
        'vlib work\nvmap work work\n'
        'vlog -sv color_feature_stream.v tb_camera_file.v\n'
        f'vsim -onfinish stop -voptargs=+acc -gFRAME_COUNT={args.frames} work.tb_camera_file\n'
        'log /tb_camera_file/feature_valid /tb_camera_file/feature /tb_camera_file/previous_feature /tb_camera_file/color_similar\n'
        'if {![batch_mode]} {add wave /tb_camera_file/feature_valid /tb_camera_file/feature /tb_camera_file/previous_feature /tb_camera_file/color_similar}\n'
        'run -all\n'
        'if {[batch_mode]} {quit -code 0 -force}\n'
        'wave zoom full\n', encoding='ascii')
    simulator = os.environ.get('MODELSIM_VSIM') or shutil.which('vsim.exe') or r'C:\modeltech64_2020.4\win64\vsim.exe'
    result = subprocess.run([simulator, '-c', '-do', 'camera.do'], cwd=run_dir,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=max(120,args.frames*15))
    (session / 'simulation_console.txt').write_bytes(result.stdout)
    for name in ('transcript', 'vsim.wlf', 'comparison.csv'):
        if (run_dir / name).exists():
            shutil.copy2(run_dir / name, session / name)
    if result.returncode or b'CAMERA_RUN_PASS' not in result.stdout:
        raise RuntimeError(f'ModelSim failed; see {session / "simulation_console.txt"}')
    with (session / 'comparison.csv').open(newline='') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != args.frames-1:
        raise RuntimeError('ModelSim did not produce one result per adjacent pair')
    for index, row in enumerate(rows):
        a, b = expected_features[index:index+2]
        expected_same = int(a >> 16 == b >> 16 and
                            abs(((a >> 8) & 255)-((b >> 8) & 255)) <= 35 and
                            abs((a & 255)-(b & 255)) <= 35)
        if (int(row['frame_a']), int(row['frame_b']), int(row['feature_a'],16),
            int(row['feature_b'],16), int(row['color_similar'])) != (index,index+1,a,b,expected_same):
            raise RuntimeError(f'RTL/reference mismatch at pair {index}')
    (session / 'verification.json').write_text(json.dumps({
        'status': 'PASS', 'png_frames': len(records), 'rtl_pairs': len(rows),
        'reference_checked_pairs': len(rows), 'person_detection': False,
        'rgb_width': 640, 'rgb_height': 480, 'pixels_per_frame': 307200,
        'input_bytes': (session / 'pixels.rgb').stat().st_size
    }, indent=2), encoding='utf-8')
    write_report(session, rows, records)
    (session / 'simulation_directory.txt').write_text(str(run_dir), encoding='utf-8')
    (ROOT / 'camera_runs' / 'latest.txt').write_text(str(session), encoding='utf-8')
    print(f'COMPLETE: {args.frames} PNG frames, {len(rows)} RTL comparisons\n{session}', flush=True)
    if args.gui:
        subprocess.Popen([simulator, '-do', 'camera.do'], cwd=run_dir)

if __name__ == '__main__':
    main()
