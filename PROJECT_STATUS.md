# RAKSHYA VISION — Project Status

## Project Overview
- **Project Name:** RAKSHYA VISION
- **Tagline:** AI Vision-Based Safety Monitoring
- **Current Phase:** Phase 2 — Dataset Collection & Preparation (Scaffolding & Tooling Ready)

---

## 1. Phase 1 Foundation Status
- **Backend:** Operational (FastAPI + SQLAlchemy + SQLite, pytest 4/4 passing).
- **Frontend:** Built and operational (React 18 + TypeScript + Vite, live health connection).
- **Git:** Version control active, clean initial commit (`ee2ded0`).

---

## 2. Phase 2 Dataset Pipeline Status

### Directory Layout
- `datasets/raw/ppe_detection_compliance/`: Target directory for raw PPE compliance dataset.
- `datasets/raw/construction_ppe/`: Target directory for construction PPE dataset.
- `datasets/raw/hard_hat_workers/`: Target directory for Hard Hat Workers dataset.
- `datasets/raw/d_fire/`: Target directory for D-Fire dataset (`repo/` cloned, LICENSE/README verified).
- `datasets/processed/`: Target YOLO structure (`images/{train,val,test}`, `labels/{train,val,test}`, `data.yaml`).
- `datasets/manifests/`: `class_mapping.yaml`, `dataset_versions.yaml`, `checksums.sha256`, `DATASET_MANIFEST.json`, `corrections.md`.
- `datasets/reports/`: `download_log.md`, `class_distribution.json`, `class_distribution.csv`, `image_quality.json`, `annotation_validation.json`, `duplicates.json`, `unmapped_classes.json`, `samples/`.
- `docs/`: `dataset_strategy.md`.

### Dataset Tooling Scripts (`scripts/dataset/`)
- `adapters/roboflow_adapter.py`: Roboflow SDK interface.
- `adapters/github_adapter.py`: Git clone and submodule handling.
- `adapters/d_fire_adapter.py`: D-Fire archive extractor and validator.
- `download_dataset.py`: Multi-source dataset downloader.
- `inspect_dataset.py`: Directory and image format inspection.
- `validate_annotations.py`: YOLO format normalization and bounds validation.
- `normalize_classes.py`: Maps dataset classes to canonical schema (0..6).
- `remove_duplicates.py`: Exact SHA-256 and perceptual difference duplicate detection.
- `split_dataset.py`: Reproducible 70/20/10 train/val/test splitting.
- `generate_yaml.py`: Generates verified `datasets/processed/data.yaml`.
- `dataset_report.py`: Generates class distribution and quality reports.
- `generate_samples.py`: Renders bounding boxes and labels for visual inspection.

### Source Verification & Download Audit
1. **PPE Detection & Compliance (`izanagi/ppe-detection-and-compliance`)**:
   - Source: Roboflow Universe.
   - Status: PENDING (Roboflow API key required to execute export).
2. **Construction PPE (`skcet-g4h72/construction-ppe-rdhzo`)**:
   - Source: Roboflow Universe.
   - Status: PENDING (Roboflow API key required to execute export).
3. **Hard Hat Workers (`public.roboflow.com/object-detection/hard-hat-workers`)**:
   - Source: Roboflow Public / Northeastern University China.
   - Status: PENDING (Roboflow API key required to execute export).
4. **D-Fire (`gaia-solutions-on-demand/DFireDataset`)**:
   - Source: GitHub / GAIA.
   - Repository: Cloned into `datasets/raw/d_fire/repo` (verified license GPL-3.0).
   - Upstream Archive: Direct OneDrive link returned 404/gated session; official Kaggle mirror (`sayedgamal99/smoke-fire-detection-yolo`) documented.

---

## 3. Strict Compliance Notes
- No fake images or labels created.
- No synthetic numbers fabricated in distribution reports.
- No model training started (YOLO training deferred to Phase 3).