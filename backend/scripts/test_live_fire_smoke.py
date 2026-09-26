"""
test_live_fire_smoke.py — SafeSync Live Fire & Smoke Diagnostic Test

Captures live frames directly from the webcam and runs the full SafeSync
fire/smoke validation pipeline with immediate console streaming.
"""

import sys
import os
import cv2
import time
import numpy as np

# Add project root and backend to path
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
sys.path.insert(0, BACKEND_DIR)

from app.ai.hazards.hazard_engine import HazardAnalysisEngine
from app.services.safety_engine import SafetyEngine
from app.ai.hazards.schemas import HazardState, is_alert_state


def main():
    print("=" * 65, flush=True)
    print("SafeSync Real-Time Fire & Smoke Live Sensor Test", flush=True)
    print("=" * 65, flush=True)

    print("[1/3] Initializing YOLO Hazard Model & State Machine...", flush=True)
    hazard_engine = HazardAnalysisEngine()
    safety_engine = SafetyEngine()

    print(f"  Configuration:", flush=True)
    print(f"    Fire Candidate Threshold:  {hazard_engine.fire_candidate_conf:.2f}", flush=True)
    print(f"    Smoke Candidate Threshold: {hazard_engine.smoke_candidate_conf:.2f}", flush=True)
    print(f"    Confirmation Frames:       {hazard_engine.state_machine.confirmation_frames}", flush=True)
    print(f"    Min Observation Ratio:     {hazard_engine.state_machine.minimum_observation_ratio:.2f}", flush=True)

    print("[2/3] Opening Camera 0 (Webcam)...", flush=True)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Camera 0 could not be opened. Check permissions or connection.", flush=True)
        return

    # Warmup frames
    for _ in range(5):
        cap.read()

    print("[3/3] Scanning live camera stream for fire / smoke (Running 35 frames)...", flush=True)
    print("=" * 65, flush=True)

    output_dir = os.path.join(BACKEND_DIR, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    evidence_path = os.path.join(output_dir, "test_fire_smoke_capture.jpg")

    detected_any_hazard = False
    confirmed_any_hazard = False

    for frame_idx in range(1, 36):
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        # 1. Inspect raw detector outputs (down to 0.15 confidence)
        det_response, _ = hazard_engine.detector.detect_image(frame, conf=0.15, annotate=False)
        raw_hazards = [d for d in det_response.detections if d.class_name.lower() in ("fire", "smoke")]

        # 2. Process frame through the temporal validation engine
        hazard_resp, annotated_frame, latencies = hazard_engine.process_frame(
            frame=frame,
            camera_id="camera_01",
            annotate=True,
        )

        # 3. Assess scene with Safety Engine
        assessment = safety_engine.assess_scene(
            camera_id="camera_01",
            zone_id="production_floor",
            hazard_response=hazard_resp,
        )

        hazards = hazard_resp.hazards

        if raw_hazards:
            detected_any_hazard = True
            raw_info = ", ".join(f"{d.class_name}({d.confidence:.2f})" for d in raw_hazards)
            print(f"[Frame {frame_idx:02d}] RAW DETECTIONS: {raw_info}", flush=True)

        if hazards:
            for h in hazards:
                print(
                    f"  >>> TRACK {h.event_id}: Type={h.hazard_type.value.upper()} "
                    f"State={h.state.value} "
                    f"RawConf={h.raw_model_confidence:.2f} "
                    f"ValConf={h.validated_confidence:.2f} "
                    f"Detections={h.detection_count}/{hazard_engine.state_machine.confirmation_frames} "
                    f"SpatialScore={h.spatial_consistency_score:.2f}",
                    flush=True
                )
            # Save annotated frame whenever hazards exist
            cv2.imwrite(evidence_path, annotated_frame)

        if assessment.events:
            confirmed_any_hazard = True
            for ev in assessment.events:
                print(
                    f"  🚨 EMERGENCY ALARM TRIGGERED! Type={ev.event_type.value} "
                    f"Priority={ev.details.get('priority')} Rule={ev.details.get('rule')}",
                    flush=True
                )

        if not raw_hazards and not hazards:
            if frame_idx % 5 == 0:
                print(f"[Frame {frame_idx:02d}] Scene clean: No fire/smoke detected (latency: {latencies.get('total_ms', 0):.1f}ms)", flush=True)

        time.sleep(0.04)

    cap.release()
    print("=" * 65, flush=True)
    print("LIVE SENSOR TEST SUMMARY:", flush=True)
    print(f"  Any Fire/Smoke Detected by YOLO:  {'YES' if detected_any_hazard else 'NO'}", flush=True)
    print(f"  Any Hazard Confirmed (Alarm):    {'YES' if confirmed_any_hazard else 'NO'}", flush=True)
    if os.path.exists(evidence_path):
        print(f"  Evidence Capture File:           {evidence_path}", flush=True)
    print("=" * 65, flush=True)


if __name__ == "__main__":
    main()
