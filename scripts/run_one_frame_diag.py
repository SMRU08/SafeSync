import os
import cv2
from app.ai.detection.model_loader import ModelLoader
from app.ai.detection.detector import Detector
from app.ai.compliance.compliance_engine import WorkerComplianceEngine

def main():
    frame_path = "outputs/test_1280x720_person.jpg"
    frame = cv2.imread(frame_path)
    if frame is None:
        print(f"Error: Could not load {frame_path}")
        return

    h, w = frame.shape[:2]
    loader = ModelLoader.get_instance()
    detector = Detector(model_loader=loader)
    
    # 1. Detection
    det_resp, _ = detector.detect_image(frame, conf=0.20)

    print("FRAME:")
    print("camera_id: camera_01")
    print(f"resolution: {w}x{h}")
    print("model_input_size: 384x384")

    print("\nRAW DETECTIONS:")
    for rd in det_resp.raw_detections:
        print(f"class_id: {rd['class_id']}, class_name: {rd['class_name']}, confidence: {rd['confidence']:.4f}, bbox: {rd['bbox']}")

    print("\nPOST-NMS:")
    for d in det_resp.detections:
        print(f"class_id: {d.class_id}, class_name: {d.class_name}, confidence: {d.confidence:.4f}, bbox: [{d.bbox.x1}, {d.bbox.y1}, {d.bbox.x2}, {d.bbox.y2}]")

    person_detected = any(d.class_name.lower() == "person" for d in det_resp.detections)
    print("\nPERSON:")
    print(f"detected = {'YES' if person_detected else 'NO'}")

    # 2. Compliance & Tracking
    engine = WorkerComplianceEngine()
    comp_resp, _, _ = engine.process_frame(frame, confidence_threshold=0.20, annotate=True)

    workers = comp_resp.workers
    print("\nTRACKER:")
    print(f"worker_created = {'YES' if len(workers) > 0 else 'NO'}")
    for w_obj in workers:
        print(f"worker_id = {w_obj.track_id}")

    print("\nAPI:")
    print(f"worker_count = {len(workers)}")

if __name__ == "__main__":
    main()
