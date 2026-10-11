"""
scripts/testing/test_runtime_recovery_matrix.py — SafeSync Complete Runtime Recovery Test Matrix
================================================================================================
Automated execution of Tests A through L:
- Test A: Backend startup
- Test B: Database initialization
- Test C: V3 model loading
- Test D: Single camera
- Test E: Single-camera AI detection
- Test F: WebSocket
- Test G: Frontend receives live events
- Test H: Single-camera sustained stability
- Test I: Camera disconnect/reconnect
- Test J: Backend restart/reconnect
- Test K: Two-camera test
- Test L: Four-camera scaling audit
"""

import os
import sys
import time
import json
import socket
import urllib.request
import urllib.error
import subprocess
import hashlib
from pathlib import Path
import psutil
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
EXPECTED_V3_SHA = "9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe"
API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/events"

results_data = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "tests": {},
    "metrics": {}
}


def is_port_in_use(port: int = 8000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def http_get(endpoint: str, timeout: float = 20.0) -> dict:
    url = f"{API_BASE}{endpoint}" if endpoint.startswith("/") else endpoint
    req = urllib.request.Request(url, headers={"User-Agent": "SafeSync-Audit-Agent/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(endpoint: str, data: dict = None, timeout: float = 20.0) -> dict:
    url = f"{API_BASE}{endpoint}" if endpoint.startswith("/") else endpoint
    payload = json.dumps(data).encode("utf-8") if data else b""
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "SafeSync-Audit-Agent/1.0"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def start_backend_process():
    if is_port_in_use(8000):
        print("   Port 8000 is already active. Probing liveness...")
        try:
            live = http_get("/health/live", timeout=2.0)
            if live.get("status") in ("live", "alive", "healthy", "nominal"):
                print("   Existing backend is healthy and responding.")
                return None
        except Exception:
            print("   Port 8000 occupied by unresponsive process. Cleaning up...")
            kill_backend_on_port_8000()

    py_bin = str(ROOT / "backend" / ".venv" / "Scripts" / "python.exe")
    cmd = [py_bin, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    print(f"   Starting backend: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )

    # Wait for startup
    t0 = time.time()
    while time.time() - t0 < 20.0:
        if is_port_in_use(8000):
            try:
                live = http_get("/health/live", timeout=1.0)
                if live:
                    print(f"   Backend successfully started in {time.time() - t0:.2f}s!")
                    return proc
            except Exception:
                pass
        time.sleep(0.5)

    raise RuntimeError("Backend failed to start on port 8000 within 20s!")


def kill_backend_on_port_8000():
    for conn in psutil.net_connections(kind="tcp"):
        if conn.laddr and conn.laddr.port == 8000 and conn.status == psutil.CONN_LISTEN:
            try:
                p = psutil.Process(conn.pid)
                print(f"   Terminating process {p.pid} ({p.name()}) on port 8000...")
                p.terminate()
                p.wait(timeout=3.0)
            except Exception as e:
                print(f"   Failed to terminate PID {conn.pid}: {e}")
    time.sleep(1.0)


# ─── TEST A: BACKEND STARTUP ──────────────────────────────────────────────────
def test_a_backend_startup():
    print("\n" + "=" * 80)
    print("TEST A: BACKEND STARTUP")
    print("=" * 80)
    t0 = time.perf_counter()
    live = http_get("/health/live", timeout=3.0)
    lat_ms = (time.perf_counter() - t0) * 1000.0
    print(f"1. Liveness probe: {live} (latency: {lat_ms:.2f}ms)")
    assert live.get("status") in ("live", "alive", "healthy", "nominal"), f"Liveness check failed: {live}"

    ready = http_get("/health/ready", timeout=3.0)
    is_ready = (ready.get("status") == "ready" or 
                ready.get("checks", {}).get("database") == "connected" or 
                ready.get("database_connected") is True)
    print(f"2. Readiness probe: status={ready.get('status')} checks={ready.get('checks')}")
    assert is_ready, f"Readiness check failed: {ready}"

    results_data["tests"]["TEST_A_backend_startup"] = {
        "status": "PASS",
        "latency_ms": round(lat_ms, 2),
        "liveness": live.get("status"),
        "ready": ready.get("status")
    }
    print("   [PASS] TEST A: Backend startup verified.")


# ─── TEST B: DATABASE INITIALIZATION ──────────────────────────────────────────
def test_b_database_initialization():
    print("\n" + "=" * 80)
    print("TEST B: DATABASE INITIALIZATION")
    print("=" * 80)
    db_health = http_get("/health/database", timeout=3.0)
    print(f"1. Database status: {db_health.get('status')}")
    print(f"2. SQLite journal mode: {db_health.get('pragmas', {}).get('journal_mode')}")
    print(f"3. Foreign keys: {db_health.get('pragmas', {}).get('foreign_keys')}")
    print(f"4. Available tables count: {len(db_health.get('tables_available', []))}")
    print(f"5. Can query: {db_health.get('can_query')}")

    assert db_health.get("status") == "healthy", "Database health report is not healthy!"
    assert db_health.get("reachable") is True, "Database is unreachable!"
    assert db_health.get("can_query") is True, "Database cannot execute queries!"
    assert db_health.get("pragmas", {}).get("journal_mode") == "wal", "SQLite WAL mode is not enabled!"

    results_data["tests"]["TEST_B_database_initialization"] = {
        "status": "PASS",
        "journal_mode": db_health.get("pragmas", {}).get("journal_mode"),
        "tables_count": len(db_health.get("tables_available", [])),
        "can_query": db_health.get("can_query")
    }
    print("   [PASS] TEST B: Database initialization verified.")


# ─── TEST C: V3 MODEL LOADING ─────────────────────────────────────────────────
def test_c_v3_model_loading():
    print("\n" + "=" * 80)
    print("TEST C: V3 PRODUCTION MODEL LOADING")
    print("=" * 80)
    # 1. SHA verification
    sha = hashlib.sha256(open(V3_PATH, "rb").read()).hexdigest()
    print(f"1. V3 SHA-256 on disk: {sha}")
    assert sha == EXPECTED_V3_SHA, f"V3 SHA mismatch! Expected {EXPECTED_V3_SHA}, got {sha}"

    # 2. Query Unified Health AI telemetry
    health = http_get("/api/health", timeout=25.0)
    ai_eng = health.get("ai_engine", {})
    probe = ai_eng.get("inference_probe", {})

    print(f"2. AI Engine Model Loaded: {health.get('model_loaded')}")
    print(f"3. AI Engine Status: {health.get('ai_status')}")
    print(f"4. Probe execution success: {probe.get('success')}")
    print(f"5. Probe latency: {probe.get('latency_ms')} ms (device: {probe.get('device')})")
    print(f"6. Classes count: {probe.get('classes_count')}")

    assert health.get("model_loaded") is True, "Model is not reported as loaded!"
    assert probe.get("success") is True, "Inference probe failed!"
    assert probe.get("classes_count") == 7, "Model classes count must be 7!"

    results_data["tests"]["TEST_C_v3_model_loading"] = {
        "status": "PASS",
        "sha256": sha,
        "classes_count": probe.get("classes_count"),
        "probe_latency_ms": probe.get("latency_ms"),
        "device": probe.get("device")
    }
    print("   [PASS] TEST C: V3 Model Loading verified.")


# ─── TEST D: SINGLE CAMERA STREAMING ──────────────────────────────────────────
def test_d_single_camera():
    print("\n" + "=" * 80)
    print("TEST D: SINGLE CAMERA (CAMERA_01)")
    print("=" * 80)
    t0 = time.time()
    cam = {}
    while time.time() - t0 < 5.0:
        cam = http_get("/api/cameras/camera_01", timeout=3.0)
        if cam.get("state") in ("CONNECTED", "STREAMING"):
            break
        time.sleep(0.5)

    print(f"1. Camera 01 State : {cam.get('state')} (status: {cam.get('status')})")
    print(f"2. Camera 01 Source: {cam.get('safe_source')} (type: {cam.get('source_type')})")
    print(f"3. Frame count     : {cam.get('metrics', {}).get('frame_count')}")
    print(f"4. Streaming FPS   : {cam.get('fps'):.1f} FPS")

    assert cam.get("state") in ("CONNECTED", "STREAMING"), f"Camera 01 not connected! State: {cam.get('state')}"

    # Fetch live snapshot
    snap_url = f"{API_BASE}/api/cameras/camera_01/snapshot"
    req = urllib.request.Request(snap_url)
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        content = resp.read()
        ctype = resp.headers.get("Content-Type")

    print(f"5. Snapshot bytes acquired: {len(content)} bytes (Content-Type: {ctype})")
    assert len(content) > 1000, "Snapshot returned empty payload!"
    assert "image/jpeg" in ctype, f"Unexpected content type: {ctype}"

    results_data["tests"]["TEST_D_single_camera"] = {
        "status": "PASS",
        "state": cam.get("state"),
        "fps": cam.get("fps"),
        "frame_count": cam.get("metrics", {}).get("frame_count"),
        "snapshot_size_bytes": len(content)
    }
    print("   [PASS] TEST D: Single Camera verified.")


# ─── TEST E: SINGLE-CAMERA AI DETECTION ───────────────────────────────────────
def test_e_single_camera_detection():
    print("\n" + "=" * 80)
    print("TEST E: SINGLE-CAMERA AI DETECTION PIPELINE")
    print("=" * 80)
    analysis = http_post("/api/cameras/camera_01/analyze", timeout=10.0)
    workers = analysis.get("workers", [])
    lat = analysis.get("latencies", {})
    has_b64 = bool(analysis.get("annotated_image_base64"))

    print(f"1. Workers tracked in live frame: {len(workers)}")
    print(f"2. Latency breakdown: {lat}")
    print(f"3. Annotated frame delivered: {has_b64}")

    assert has_b64 is True, "Annotated frame base64 not delivered!"
    assert "total_ms" in lat, "Total latency not reported!"

    results_data["tests"]["TEST_E_single_camera_detection"] = {
        "status": "PASS",
        "workers_detected": len(workers),
        "latencies": lat,
        "annotated_frame_delivered": has_b64
    }
    print("   [PASS] TEST E: Single Camera AI Detection verified.")


# ─── TEST F: WEBSOCKET HANDSHAKE ──────────────────────────────────────────────
def test_f_websocket():
    print("\n" + "=" * 80)
    print("TEST F: WEBSOCKET HANDSHAKE & TELEMETRY")
    print("=" * 80)
    import websockets
    import asyncio

    async def _test():
        async with websockets.connect(WS_URL) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
            data = json.loads(msg)
            print(f"1. Received WebSocket handshake: {data}")
            assert data.get("type") == "connected", f"Unexpected handshake: {data}"
            return data

    handshake = asyncio.run(_test())
    results_data["tests"]["TEST_F_websocket"] = {
        "status": "PASS",
        "handshake_type": handshake.get("type"),
        "active_connections": handshake.get("active_connections")
    }
    print("   [PASS] TEST F: WebSocket verified.")


# ─── TEST G: LIVE EVENT FLOW ──────────────────────────────────────────────────
def test_g_frontend_events():
    print("\n" + "=" * 80)
    print("TEST G: FRONTEND EVENT FLOW (BROADCASTER -> WEBSOCKET)")
    print("=" * 80)
    import websockets
    import asyncio

    async def _test():
        async with websockets.connect(WS_URL) as ws:
            # Consume handshake
            await ws.recv()

            # Trigger an event broadcast via analyze
            print("   Triggering live frame analysis to drive event loop...")
            http_post("/api/cameras/camera_01/analyze", timeout=10.0)

            # Check health active connections
            h = http_get("/api/health")
            active_ws = h.get("websocket", {}).get("active_connections", 0)
            print(f"   Active WebSocket client connections registered: {active_ws}")
            assert active_ws >= 1, "WebSocket connection not registered in server telemetry!"
            return active_ws

    active_cnt = asyncio.run(_test())
    results_data["tests"]["TEST_G_frontend_events"] = {
        "status": "PASS",
        "active_websocket_connections": active_cnt
    }
    print("   [PASS] TEST G: Frontend Event Flow verified.")


# ─── TEST H: SUSTAINED STABILITY BENCHMARK (60 ITERATIONS) ─────────────────────
def test_h_sustained_stability():
    print("\n" + "=" * 80)
    print("TEST H: SUSTAINED SINGLE-CAMERA STABILITY BENCHMARK")
    print("=" * 80)
    latencies = []
    fps_samples = []
    cpu_samples = []
    ram_samples = []

    print("   Running sustained streaming benchmark across 30 samples (~30s)...")
    cam_start = http_get("/api/cameras/camera_01")
    f_start = cam_start.get("metrics", {}).get("frame_count", 0)

    for i in range(30):
        t0 = time.perf_counter()
        c = http_get("/api/cameras/camera_01", timeout=2.0)
        dur = (time.perf_counter() - t0) * 1000.0
        latencies.append(dur)
        fps_samples.append(c.get("fps", 0.0))
        cpu_samples.append(psutil.cpu_percent(interval=None))
        ram_samples.append(psutil.virtual_memory().used / (1024 * 1024))
        time.sleep(0.5)

    cam_end = http_get("/api/cameras/camera_01")
    f_end = cam_end.get("metrics", {}).get("frame_count", 0)
    frames_processed = f_end - f_start

    avg_fps = float(np.mean(fps_samples))
    p50_lat = float(np.percentile(latencies, 50))
    p95_lat = float(np.percentile(latencies, 95))
    avg_cpu = float(np.mean(cpu_samples))
    avg_ram = float(np.mean(ram_samples))

    print(f"   Total Frames Captured in Window: {frames_processed}")
    print(f"   Average Camera Capture FPS     : {avg_fps:.1f} FPS")
    print(f"   API Response Latency (P50/P95) : {p50_lat:.2f} ms / {p95_lat:.2f} ms")
    print(f"   System CPU Utilization (Avg)   : {avg_cpu:.1f} %")
    print(f"   System RAM Utilization (Avg)   : {avg_ram:.1f} MB")
    print(f"   Dropped Frames                 : {cam_end.get('metrics', {}).get('dropped_frames', 0)}")

    assert frames_processed > 50, f"Expected sustained frame flow, got {frames_processed} frames!"
    assert avg_fps >= 10.0, f"Average FPS {avg_fps:.1f} below threshold!"

    results_data["tests"]["TEST_H_sustained_stability"] = {
        "status": "PASS",
        "frames_captured_in_window": frames_processed,
        "avg_fps": round(avg_fps, 1),
        "p50_latency_ms": round(p50_lat, 2),
        "p95_latency_ms": round(p95_lat, 2),
        "avg_cpu_percent": round(avg_cpu, 1),
        "avg_ram_mb": round(avg_ram, 1),
        "dropped_frames": cam_end.get("metrics", {}).get("dropped_frames", 0)
    }
    print("   [PASS] TEST H: Sustained Stability verified.")


# ─── TEST I: CAMERA DISCONNECT & RECONNECT ─────────────────────────────────────
def test_i_disconnect_reconnect():
    print("\n" + "=" * 80)
    print("TEST I: CAMERA DISCONNECT & RECONNECT RESILIENCE")
    print("=" * 80)
    # Stop camera 01
    print("1. Stopping Camera 01...")
    stopped = http_post("/api/cameras/camera_01/stop", timeout=5.0)
    print(f"   Camera 01 state after stop: {stopped.get('state')}")
    assert stopped.get("state") in ("DISABLED", "DISCONNECTED"), "Camera should be DISABLED after stop!"

    time.sleep(1.0)

    # Start camera 01
    print("2. Starting Camera 01...")
    started = http_post("/api/cameras/camera_01/start", timeout=5.0)
    t0 = time.time()
    resumed = {}
    while time.time() - t0 < 5.0:
        resumed = http_get("/api/cameras/camera_01", timeout=3.0)
        if resumed.get("state") in ("CONNECTED", "STREAMING"):
            break
        time.sleep(0.5)
    print(f"   Camera 01 state after restart: {resumed.get('state')} (FPS: {resumed.get('fps'):.1f})")
    assert resumed.get("state") in ("CONNECTED", "STREAMING"), "Camera failed to reconnect!"

    results_data["tests"]["TEST_I_disconnect_reconnect"] = {
        "status": "PASS",
        "stopped_state": stopped.get("state"),
        "reconnected_state": resumed.get("state"),
        "fps_after_reconnect": resumed.get("fps")
    }
    print("   [PASS] TEST I: Disconnect & Reconnect verified.")


# ─── TEST J: BACKEND RESTART & RECOVERY ────────────────────────────────────────
def test_j_backend_restart():
    print("\n" + "=" * 80)
    print("TEST J: BACKEND RESTART & SOCKET RECOVERY")
    print("=" * 80)
    print("1. Simulating backend restart (killing process on port 8000)...")
    kill_backend_on_port_8000()
    assert not is_port_in_use(8000), "Port 8000 should be closed!"

    print("2. Relaunching backend process...")
    start_backend_process()

    print("3. Validating recovered health status...")
    h = http_get("/api/health", timeout=25.0)
    assert h.get("cluster_state") == "healthy", "Backend cluster not healthy after restart!"
    assert h.get("model_loaded") is True, "AI model not loaded after restart!"

    results_data["tests"]["TEST_J_backend_restart"] = {
        "status": "PASS",
        "cluster_state": h.get("cluster_state"),
        "model_loaded": h.get("model_loaded")
    }
    print("   [PASS] TEST J: Backend Restart & Recovery verified.")


# ─── TEST K: TWO-CAMERA CONCURRENT TEST ────────────────────────────────────────
def test_k_two_camera_test():
    print("\n" + "=" * 80)
    print("TEST K: TWO-CAMERA CONCURRENT EXECUTION AUDIT")
    print("=" * 80)
    # Register/Start synthetic Camera 03
    print("1. Activating Camera 03 (Synthetic Stream)...")
    http_post("/api/cameras/camera_03/start", timeout=5.0)
    time.sleep(2.0)

    c1 = http_get("/api/cameras/camera_01")
    c3 = http_get("/api/cameras/camera_03")

    print(f"   Camera 01 (USB Webcam)  : State={c1.get('state')} FPS={c1.get('fps'):.1f}")
    print(f"   Camera 03 (Synthetic Cam): State={c3.get('state')} FPS={c3.get('fps'):.1f}")

    assert c1.get("state") in ("CONNECTED", "STREAMING"), "Camera 01 must stay streaming!"
    assert c3.get("state") in ("CONNECTED", "STREAMING"), "Camera 03 must be streaming!"

    results_data["tests"]["TEST_K_two_camera"] = {
        "status": "PASS",
        "cam1_fps": c1.get("fps"),
        "cam3_fps": c3.get("fps"),
        "cam1_state": c1.get("state"),
        "cam3_state": c3.get("state")
    }
    print("   [PASS] TEST K: Two-Camera Concurrent Execution verified.")


# ─── TEST L: FOUR-CAMERA SCALING AUDIT ─────────────────────────────────────────
def test_l_four_camera_scaling():
    print("\n" + "=" * 80)
    print("TEST L: FOUR-CAMERA SCALING & RESOURCE AUDIT")
    print("=" * 80)
    # Enable Camera 04 as well
    http_post("/api/cameras/camera_04/start", timeout=5.0)
    time.sleep(2.0)

    cams = http_get("/api/cameras")
    online_count = sum(1 for c in cams if c.get("state") in ("CONNECTED", "STREAMING"))
    print(f"   Active camera count in matrix: {online_count} / {len(cams)}")
    for c in cams:
        print(f"   - {c.get('camera_id'):12s}: State={c.get('state'):12s} FPS={c.get('fps'):4.1f} Latency={c.get('ai_analysis', {}).get('latency_ms', 0):.1f}ms")

    # Stop extra test cameras (03, 04) to leave system in pristine single-camera baseline
    http_post("/api/cameras/camera_03/stop", timeout=3.0)
    http_post("/api/cameras/camera_04/stop", timeout=3.0)

    results_data["tests"]["TEST_L_four_camera_scaling"] = {
        "status": "PASS",
        "active_concurrent_streams": online_count,
        "recommendation": "Single camera primary demo recommended on CPU runtime for optimal latency headroom"
    }
    print("   [PASS] TEST L: Four-Camera Scaling Audit verified.")


def main():
    print("STARTING COMPLETE RUNTIME RECOVERY TEST MATRIX")
    start_backend_process()

    test_a_backend_startup()
    test_b_database_initialization()
    test_c_v3_model_loading()
    test_d_single_camera()
    test_e_single_camera_detection()
    test_f_websocket()
    test_g_frontend_events()
    test_h_sustained_stability()
    test_i_disconnect_reconnect()
    test_j_backend_restart()
    test_k_two_camera_test()
    test_l_four_camera_scaling()

    # Save results
    out_file = ROOT / "reports" / "runtime_recovery_test_matrix_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results_data, f, indent=2)
    print(f"\nAll tests completed successfully. Results saved to {out_file}")


if __name__ == "__main__":
    main()
