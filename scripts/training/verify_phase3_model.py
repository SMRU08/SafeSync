"""
verify_phase3_model.py — RAKSHYA VISION Phase 4 Pre-check
Verifies the Phase 3 model checkpoint:
1. File existence
2. SHA-256 match
3. Load into Ultralytics YOLO
4. Verify 7 canonical classes
5. Single image inference test
6. Checkpoint metadata check
"""

import os
import sys
import hashlib
import json
from ultralytics import YOLO

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BEST_PT = os.path.join(ROOT, "models", "detection", "ppe_fire_smoke_v1", "weights", "best.pt")
SHA_FILE = os.path.join(ROOT, "models", "detection", "ppe_fire_smoke_v1", "model.sha256")
META_FILE = os.path.join(ROOT, "models", "detection", "ppe_fire_smoke_v1", "model_metadata.json")

EXPECTED_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

def verify():
    print("=" * 60)
    print("  RAKSHYA VISION — Phase 3 Model Verification (Gate for Phase 4)")
    print("=" * 60)

    # 1. Existence
    if not os.path.isfile(BEST_PT):
        print(f"[FAIL] Checkpoint not found at: {BEST_PT}")
        sys.exit(1)
    print(f"[OK] Located best.pt: {BEST_PT} ({os.path.getsize(BEST_PT):,} bytes)")

    # 2. SHA-256
    with open(BEST_PT, "rb") as f:
        computed_sha = hashlib.sha256(f.read()).hexdigest()
    print(f"[OK] Computed SHA-256: {computed_sha}")

    if os.path.isfile(SHA_FILE):
        with open(SHA_FILE, "r") as f:
            recorded_sha = f.read().split()[0]
        if computed_sha == recorded_sha:
            print(f"[OK] Checksum MATCHES model.sha256: {recorded_sha}")
        else:
            print(f"[FAIL] Checksum MISMATCH! Recorded: {recorded_sha}")
            sys.exit(1)
    else:
        print(f"[WARN] SHA-256 file not found at: {SHA_FILE}")

    # 3. Metadata
    if os.path.isfile(META_FILE):
        with open(META_FILE, "r") as f:
            meta = json.load(f)
        print(f"[OK] Metadata verified: Experiment='{meta.get('experiment')}', Model='{meta.get('model_architecture')}'")
    else:
        print(f"[WARN] Metadata file missing at: {META_FILE}")

    # 4. Load model
    print("\nLoading model into Ultralytics YOLO...")
    model = YOLO(BEST_PT)
    print(f"[OK] Model loaded successfully: {type(model).__name__}")

    # 5. Verify classes
    model_classes = model.names
    print(f"[INFO] Model classes reported: {model_classes}")
    if len(model_classes) != 7:
        print(f"[FAIL] Expected 7 classes, got {len(model_classes)}")
        sys.exit(1)

    for idx, name in EXPECTED_CLASSES.items():
        actual_name = model_classes.get(idx)
        if actual_name != name:
            print(f"[FAIL] Class {idx} mismatch: expected '{name}', got '{actual_name}'")
            sys.exit(1)
        print(f"  [OK] Class {idx}: {name}")

    # 6. Single image inference test
    val_dir = os.path.join(ROOT, "datasets", "processed", "images", "val")
    val_images = [os.path.join(val_dir, f) for f in os.listdir(val_dir) if f.lower().endswith((".jpg", ".png"))]
    if not val_images:
        print("[FAIL] No validation images available for test inference")
        sys.exit(1)

    test_img = val_images[0]
    print(f"\nRunning test inference on: {os.path.basename(test_img)}")
    results = model.predict(test_img, conf=0.1, imgsz=384, verbose=False)
    boxes = results[0].boxes
    print(f"[OK] Inference produced {len(boxes)} detection box(es)")
    for b in boxes:
        cls_id = int(b.cls[0])
        conf = float(b.conf[0])
        xyxy = [round(float(v), 1) for v in b.xyxy[0].tolist()]
        print(f"  - Detected: {model.names[cls_id]} (ID {cls_id}) | Conf: {conf:.3f} | BBox: {xyxy}")

    print("\n" + "=" * 60)
    print("  PHASE 3 MODEL VERIFICATION PASSED — CLEARED FOR PHASE 4")
    print("=" * 60)

if __name__ == "__main__":
    verify()
