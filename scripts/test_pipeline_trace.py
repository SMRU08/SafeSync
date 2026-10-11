import os, sys, cv2, numpy as np
sys.path.insert(0, os.path.abspath("backend"))

from app.ai.detection.detector import Detector
from app.ai.compliance.compliance_engine import WorkerComplianceEngine
from ultralytics import YOLO

# Take a test image from dataset with a known person
test_img_path = "data/processed/safesync/images/test/cppe_00047.jpg"
base_img = cv2.imread(test_img_path)
print("Base image shape:", base_img.shape)

# Create a 1280x720 frame with this person in the center
canvas = np.full((720, 1280, 3), 40, dtype=np.uint8)
# Resize base image to fit nicely in center
scaled_h = 600
scaled_w = int(base_img.shape[1] * (scaled_h / base_img.shape[0]))
scaled = cv2.resize(base_img, (scaled_w, scaled_h))
# Center it
start_y = (720 - scaled_h) // 2
start_x = (1280 - scaled_w) // 2
canvas[start_y:start_y+scaled_h, start_x:start_x+scaled_w] = scaled
cv2.imwrite("outputs/test_1280x720_person.jpg", canvas)
print("Created outputs/test_1280x720_person.jpg with shape:", canvas.shape)

# Test 1: Direct V3 at various confidences
v3 = YOLO("models/detection/ppe_fire_smoke_v3/weights/best.pt")
for conf in [0.10, 0.15, 0.20, 0.22, 0.25]:
    res = v3.predict(canvas, conf=conf, imgsz=384, verbose=False)
    boxes = res[0].boxes
    person_boxes = [b for b in boxes if int(b.cls[0].item()) == 0]
    print(f"Conf={conf:.2f} -> Total: {len(boxes)}, Persons: {len(person_boxes)}")
    for b in person_boxes:
        print(f"   Person score: {float(b.conf[0].item()):.3f}, box: {[round(x,1) for x in b.xyxy[0].tolist()]}")

# Test 2: Detector.detect_image
det = Detector()
det_resp, _ = det.detect_image(canvas, conf=0.20)
print(f"Detector detect_image total: {det_resp.total_detections}")
for d in det_resp.detections:
    print(f"   {d.class_name}: {d.confidence:.3f}, bbox: [{d.bbox.x1}, {d.bbox.y1}, {d.bbox.x2}, {d.bbox.y2}]")

# Test 3: WorkerComplianceEngine across 3 frames
comp = WorkerComplianceEngine()
for f in range(1, 4):
    resp, _, _ = comp.process_frame(canvas, confidence_threshold=0.20)
    print(f"Frame {f}: Workers count = {len(resp.workers)}")
    for w in resp.workers:
        print(f"   Worker {w.track_id}: status={w.overall_status}, bbox=[{w.bbox.x1}, {w.bbox.y1}, {w.bbox.x2}, {w.bbox.y2}]")
