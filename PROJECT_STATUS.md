# RAKSHYA VISION — Project Status

## Project Overview
- **Project Name:** RAKSHYA VISION
- **Tagline:** AI Vision-Based Safety Monitoring
- **Current Phase:** Phase 2 — Dataset Collection & Preparation (Completed & Verified)

---

## 1. Phase 1 Foundation Status
- **Backend:** Operational (FastAPI + SQLAlchemy + SQLite, pytest 4/4 passing).
- **Frontend:** Built and operational (React 18 + TypeScript + Vite, live health connection).
- **Git:** Initial commit `ee2ded0` established.

---

## 2. Phase 2 Dataset Pipeline Status

### Raw Dataset Preservation (`datasets/raw/`)
All raw datasets were downloaded, checksummed, and preserved untouched:
1. **`construction_ppe/`**: 1,124 images (hat, vest, no-hat, no-vest).
2. **`hard_hat_workers/`**: 7,035 images (helmet, head, person). SHA-256: `131b731c7391b71d9b0ece1798b1143a717fcef07f8d3e511008cc6dcfe3c5b1`.
3. **`ppe_detection_compliance/`**: 9,663 images (Boots, Gloves, Goggles, Helmet, Mask, Person, Vest, and absence classes). SHA-256: `806cda2009852f3f7736b14f01e689158fa7053b0a6782728ce057c765b45855`.
4. **`d_fire/`**: Cloned official repository (`repo/`) + Fire & Smoke dataset (`fire_smoke/` with 4,631 images). SHA-256: `0ed3b4011469870ff8401445efccae9b4c3de3bef8c1a2c4898ee3e1379319ca`.
- **Total Raw Images:** 22,453 images across all 4 datasets.

### Processed Training-Ready Dataset (`datasets/processed/`)
- **Normalized Schema (0..6):**
  - `0: person`
  - `1: helmet`
  - `2: safety_vest`
  - `3: gloves`
  - `4: safety_footwear`
  - `5: fire`
  - `6: smoke`
- **Leakage-Safe Splitting:**
  - Near-duplicate and exact-duplicate images clustered into groups before splitting.
  - **Train Split (70%):** 15,717 images
  - **Validation Split (20%):** 4,490 images
  - **Test Split (10%):** 2,246 images
  - **Total Processed Images:** 22,453 images
- **YOLO Configuration:** [`datasets/processed/data.yaml`](./datasets/processed/data.yaml) generated and path-verified.

### Dataset Quality & Verification Metrics
- **Annotation Validation:** 22,453 / 22,453 valid labels (100% valid; 0 invalid boxes; polygon segmentation masks safely converted to bounding boxes; 0 out-of-bounds coordinates).
- **Image Quality Check:** 22,453 images scanned; 0 corrupted images, 0 zero-byte files, 0 unreadable images.
- **Duplicate Detection:** 62 exact duplicates and 1,228 near-duplicates identified and constrained to unified splits to avoid train/val/test data leakage.
- **Class Imbalance Analysis:**
  - `helmet`: 24,531 boxes (47.92%) - primary industrial head protection.
  - `safety_vest`: 6,272 boxes (12.25%)
  - `person`: 5,545 boxes (10.83%)
  - `smoke`: 5,373 boxes (10.50%)
  - `fire`: 5,333 boxes (10.42%)
  - `gloves`: 2,634 boxes (5.15%)
  - `safety_footwear`: 1,507 boxes (2.94%)
  - *Total Bounding Boxes:* 51,195
  - *Note:* In accordance with Phase 2 rules, no synthetic duplication or augmentation was performed. Weighted sampling or Mosaic augmentation will be addressed in Phase 3.
- **Visual Inspection:** Representative sample images for all 7 canonical classes generated with color-coded bounding boxes in `datasets/reports/samples/`.

---

## 3. Strict Compliance Audit
- [x] No YOLO or model training initiated.
- [x] No mAP, precision, or recall fabricated.
- [x] No fake images, labels, or statistics generated.
- [x] Raw data preserved unmodified in `datasets/raw/`.
- [x] Stop at end of Phase 2 awaiting explicit user approval before Phase 3.