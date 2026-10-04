import os
import sys
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

V3_PATH = ROOT / "models" / "detection" / "ppe_fire_smoke_v3" / "weights" / "best.pt"
V6_PATH = ROOT / "models" / "detection" / "safesync_v6_hardnegative" / "weights" / "best.pt"

uploaded_imgs = [
    r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.user_uploaded\media_1790928859039.jpg",
    r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.user_uploaded\media_1790928859043.jpg",
    r"C:\Users\smrut\.gemini\antigravity\brain\c8c2a490-b991-40ca-b3c4-64711685ed0b\.user_uploaded\media_1790928859056.jpg",
]

CLASS_NAMES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

v3 = YOLO(str(V3_PATH))
v6 = YOLO(str(V6_PATH))

from backend.app.ai.compliance.association import (
    verify_helmet_features,
    verify_safety_vest_features,
    SpatialPPEAssociator,
)
from backend.app.ai.compliance.schemas import PPEItemType

associator = SpatialPPEAssociator()

for img_idx, img_p in enumerate(uploaded_imgs):
    print("=" * 80)
    print(f"DIAGNOSING IMAGE {img_idx+1}: {os.path.basename(img_p)}")
    print("=" * 80)

    frame = cv2.imread(img_p)
    if frame is None:
        print("FAILED TO READ IMAGE")
        continue

    h, w = frame.shape[:2]
    print(f"Image Resolution: {w}x{h}")

    for m_name, model in [("V3 Production", v3), ("V6 Candidate", v6)]:
        print(f"\n--- {m_name} RAW INFERENCE (conf=0.10, imgsz=384) ---")
        res = model.predict(source=frame, imgsz=384, conf=0.10, verbose=False)[0]

        raw_boxes = []
        if res.boxes is not None:
            for b in res.boxes:
                cid = int(b.cls[0].item())
                cname = CLASS_NAMES.get(cid, str(cid))
                conf = float(b.conf[0].item())
                xyxy = [round(float(v), 1) for v in b.xyxy[0].tolist()]
                raw_boxes.append((cname, conf, xyxy))
                print(f"  {cname:16s} | conf: {conf:.3f} | bbox: {xyxy}")

        # Check association against any detected persons
        persons = [b for b in raw_boxes if b[0] == "person"]
        ppes = [b for b in raw_boxes if b[0] in ["helmet", "safety_vest", "gloves", "safety_footwear"]]

        print(f"\n  Found {len(persons)} person boxes and {len(ppes)} PPE boxes.")
        for p_idx, (_, p_conf, p_xyxy) in enumerate(persons):
            p_box_np = np.array(p_xyxy, dtype=float)
            print(f"\n  Person #{p_idx+1} [conf={p_conf:.2f}, bbox={p_xyxy}]:")
            for cname, ppe_conf, ppe_xyxy in ppes:
                ppe_box_np = np.array(ppe_xyxy, dtype=float)
                item_type = PPEItemType(cname)

                # Test feature verifier directly
                if item_type == PPEItemType.HELMET:
                    v_feat = verify_helmet_features(p_box_np, ppe_box_np, frame=frame, confidence=ppe_conf, img_shape=(h, w))
                    print(f"    -> Helmet feature check: {v_feat}")
                elif item_type == PPEItemType.SAFETY_VEST:
                    v_feat = verify_safety_vest_features(p_box_np, ppe_box_np, frame=frame, confidence=ppe_conf, img_shape=(h, w))
                    print(f"    -> Vest feature check: {v_feat}")

                aff = associator.compute_affinity(p_box_np, ppe_box_np, item_type, frame=frame, confidence=ppe_conf, img_shape=(h, w))
                print(f"    -> Affinity to {cname} (conf={ppe_conf:.2f}, bbox={ppe_xyxy}): {aff:.4f}")
