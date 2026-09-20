# RAKSHYA VISION — Dataset Source Registry

This registry catalogues all approved and candidate datasets for the RAKSHYA VISION project in compliance with Phase 2 specifications.

---

## 1. PPE Detection & Compliance
- **Dataset Name:** PPE Detection & Compliance
- **Source:** Roboflow Universe
- **URL:** https://universe.roboflow.com/izanagi/ppe-detection-and-compliance
- **License:** CC BY 4.0
- **License URL:** https://creativecommons.org/licenses/by/4.0/
- **Version:** Not verified (dynamic export on Universe)
- **Download Method:** Roboflow Python SDK / API (`roboflow.workspace().project().version().download("yolov8")`)
- **Image Count:** Not verified (dependent on version snapshot)
- **Class List:** `person`, `helmet`, `NO-Helmet`, `vest`, `NO-Vest`, `gloves`, `NO-Gloves`, `boots`, `NO-Boots`
- **Annotation Format:** YOLO / COCO / Pascal VOC (exportable)
- **Download Date:** Not verified
- **Download Status:** PENDING
- **Verification Status:** Not verified
- **Purpose:** Primary multi-class PPE detection dataset covering full body, extremities, and non-compliance examples.
- **Notes:** Requires a Roboflow API key (`ROBOFLOW_API_KEY`) to export.

---

## 2. Construction PPE
- **Dataset Name:** Construction PPE
- **Source:** Roboflow Universe
- **URL:** https://universe.roboflow.com/skcet-g4h72/construction-ppe-rdhzo
- **License:** CC BY 4.0
- **License URL:** https://creativecommons.org/licenses/by/4.0/
- **Version:** Not verified
- **Download Method:** Roboflow Python SDK / API
- **Image Count:** ~8,845 total (~7,602 train, 851 val, 392 test in base version)
- **Class List:** `helmet`, `vest`, `gloves`, `Safety Boot`, `no gloves`, `no boots`, `no hat`, `no vest`
- **Annotation Format:** YOLO / COCO
- **Download Date:** Not verified
- **Download Status:** PENDING
- **Verification Status:** Not verified
- **Purpose:** Supplementary construction-specific PPE diversity and boots/gloves representation.
- **Notes:** Requires `ROBOFLOW_API_KEY`.

---

## 3. Hard Hat Workers
- **Dataset Name:** Hard Hat Workers
- **Source:** Roboflow Public Dataset / Harvard Dataverse
- **URL:** https://public.roboflow.com/object-detection/hard-hat-workers
- **License:** CC0: Public Domain
- **License URL:** https://creativecommons.org/publicdomain/zero/1.0/
- **Version:** v2 (raw) / v10
- **Download Method:** Roboflow Python SDK / curl export
- **Image Count:** 7,035 images
- **Class List:** `helmet`, `head`, `person`
- **Annotation Format:** YOLOv5 / YOLOv8 PyTorch format
- **Download Date:** Not verified
- **Download Status:** PENDING
- **Verification Status:** Not verified
- **Purpose:** Core worker/person detection and head/helmet spatial relationship modeling.
- **Notes:** Created by Northeastern University (China). Public Domain (CC0).

---

## 4. D-Fire
- **Dataset Name:** D-Fire: an image dataset for fire and smoke detection
- **Source:** GitHub (GAIA Solutions on Demand)
- **URL:** https://github.com/gaia-solutions-on-demand/DFireDataset
- **License:** GNU General Public License v3.0 (GPL-3.0)
- **License URL:** https://raw.githubusercontent.com/gaia-solutions-on-demand/DFireDataset/master/LICENSE
- **Version:** 1.0
- **Download Method:** Official OneDrive archive / Official Kaggle mirror (`sayedgamal99/smoke-fire-detection-yolo`)
- **Image Count:** 21,527 images (1,164 fire only, 5,867 smoke only, 4,658 fire and smoke, 9,838 none/negative)
- **Class List:** `0: Fire` (14,692 boxes), `1: Smoke` (11,865 boxes)
- **Annotation Format:** YOLO format (`class_id center_x center_y width height`, normalized 0-1)
- **Download Date:** Not verified
- **Download Status:** PENDING
- **Verification Status:** Not verified
- **Purpose:** Environmental hazard detection (fire and smoke) and hard-negative false-alarm reduction.
- **Notes:** Upstream OneDrive link has dynamic session gating; Kaggle mirror or manual archive download supported.