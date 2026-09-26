"""
create_balanced_manifest.py — Generates a class-balanced training manifest for Phase 3.1 V2
Guarantees high representation for minority classes (footwear, gloves, person, vest)
alongside environmental hazard classes (fire, smoke) and helmet.
Saves absolute image paths to datasets/processed/train_balanced.txt
"""

import os
import random
from pathlib import Path
from collections import defaultdict

ROOT = Path("D:/Additional/PROJECT/SafeSync")
PROCESSED_DIR = ROOT / "datasets" / "processed"
TRAIN_IMG_DIR = PROCESSED_DIR / "images" / "train"
TRAIN_LBL_DIR = PROCESSED_DIR / "labels" / "train"

CANONICAL_CLASSES = {
    0: "person",
    1: "helmet",
    2: "safety_vest",
    3: "gloves",
    4: "safety_footwear",
    5: "fire",
    6: "smoke",
}

def create_balanced_manifest():
    random.seed(42)
    print("Indexing training images and labels...")
    
    # Map class_id -> list of image paths
    class_to_images = defaultdict(list)
    
    # Find all images in train
    all_images = list(TRAIN_IMG_DIR.glob("*.*"))
    print(f"Found {len(all_images)} images in train.")
    
    img_by_stem = {p.stem: p for p in all_images}
    
    for lbl_p in TRAIN_LBL_DIR.glob("*.txt"):
        stem = lbl_p.stem
        if stem not in img_by_stem:
            continue
        img_p = img_by_stem[stem]
        
        seen_cids = set()
        with open(lbl_p, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    try:
                        cid = int(parts[0])
                        seen_cids.add(cid)
                    except ValueError:
                        pass
                        
        for cid in seen_cids:
            class_to_images[cid].append(img_p)
            
    print("Images available per class in train:")
    for cid in range(len(CANONICAL_CLASSES)):
        print(f"  Class {cid} ({CANONICAL_CLASSES[cid]}): {len(class_to_images[cid])} images")
        
    # Strategy:
    # 1. Take 100% of footwear images (Class 4, rarest)
    # 2. Take 100% of gloves images (Class 3)
    # 3. Take up to 1,200 person images (Class 0)
    # 4. Take up to 1,000 vest images (Class 2)
    # 5. Take up to 1,000 helmet images (Class 1)
    # 6. Take up to 800 fire images (Class 5)
    # 7. Take up to 800 smoke images (Class 6)
    
    selected_set = set()
    
    # 100% footwear
    for p in class_to_images[4]:
        selected_set.add(p)
        
    # 100% gloves
    for p in class_to_images[3]:
        selected_set.add(p)
        
    # Sample person
    person_imgs = [p for p in class_to_images[0] if p not in selected_set]
    random.shuffle(person_imgs)
    selected_set.update(person_imgs[:1200])
    
    # Sample vest
    vest_imgs = [p for p in class_to_images[2] if p not in selected_set]
    random.shuffle(vest_imgs)
    selected_set.update(vest_imgs[:800])
    
    # Sample helmet
    helmet_imgs = [p for p in class_to_images[1] if p not in selected_set]
    random.shuffle(helmet_imgs)
    selected_set.update(helmet_imgs[:600])
    
    # Sample fire
    fire_imgs = [p for p in class_to_images[5] if p not in selected_set]
    random.shuffle(fire_imgs)
    selected_set.update(fire_imgs[:800])
    
    # Sample smoke
    smoke_imgs = [p for p in class_to_images[6] if p not in selected_set]
    random.shuffle(smoke_imgs)
    selected_set.update(smoke_imgs[:800])
    
    selected_list = sorted(list(selected_set))
    print(f"\nTotal selected balanced training images: {len(selected_list)}")
    
    # Verify class instance counts in selected_list
    final_instance_counts = defaultdict(int)
    for img_p in selected_list:
        lbl_p = TRAIN_LBL_DIR / f"{img_p.stem}.txt"
        if lbl_p.exists():
            with open(lbl_p, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        final_instance_counts[int(parts[0])] += 1
                        
    print("\nActual ground-truth instance counts in balanced dataset:")
    for cid in range(len(CANONICAL_CLASSES)):
        cname = CANONICAL_CLASSES[cid]
        cnt = final_instance_counts[cid]
        print(f"  Class {cid} ({cname:15s}): {cnt:6d} instances")
        
    out_manifest = PROCESSED_DIR / "train_balanced.txt"
    with open(out_manifest, "w", encoding="utf-8") as f:
        for p in selected_list:
            f.write(f"{p.as_posix()}\n")
            
    print(f"\nSaved balanced manifest to: {out_manifest}")
    return out_manifest

if __name__ == "__main__":
    create_balanced_manifest()
