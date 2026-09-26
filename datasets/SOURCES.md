# SafeSync — Dataset Source Registry

All approved datasets for SafeSync have been downloaded, verified, and preserved in `datasets/raw/`.

---

## 1. PPE Detection & Compliance
- **Dataset Name:** PPE Detection & Compliance
- **Source:** Roboflow Universe
- **URL:** https://universe.roboflow.com/izanagi/ppe-detection-and-compliance
- **License:** CC BY 4.0
- **License URL:** https://creativecommons.org/licenses/by/4.0/
- **Version:** 2
- **Download Method:** Roboflow Python SDK export (`yolov8`)
- **Image Count:** 9,663 images
- **Class List:** `Boots`, `Gloves`, `Goggles`, `Helmet`, `Mask`, `NO-Boots`, `NO-Gloves`, `NO-Goggles`, `NO-Helmet`, `NO-Mask`, `NO-Vest`, `Person`, `Vest`
- **Annotation Format:** YOLO format
- **Download Date:** 2026-09-20
- **Download Status:** DOWNLOADED & EXTRACTED
- **Verification Status:** VERIFIED
- **Purpose:** Primary multi-class PPE detection dataset covering full body, extremities, and non-compliance examples.
- **Notes:** Absence classes preserved in RAW; canonical classes mapped to primary detector.

---

## 2. Construction PPE
- **Dataset Name:** Construction PPE
- **Source:** Roboflow Universe
- **URL:** https://universe.roboflow.com/skcet-g4h72/construction-ppe-rdhzo
- **License:** CC BY 4.0
- **License URL:** https://creativecommons.org/licenses/by/4.0/
- **Version:** 1
- **Download Method:** Roboflow Python SDK export (`yolov8`)
- **Image Count:** 1,124 images
- **Class List:** `hat`, `no hat`, `no vest`, `vest`
- **Annotation Format:** YOLO format
- **Download Date:** 2026-09-20
- **Download Status:** DOWNLOADED & EXTRACTED
- **Verification Status:** VERIFIED
- **Purpose:** Supplementary construction-specific PPE diversity.

---

## 3. Hard Hat Workers
- **Dataset Name:** Hard Hat Workers
- **Source:** Roboflow Public Dataset / Harvard Dataverse
- **URL:** https://public.roboflow.com/object-detection/hard-hat-workers
- **License:** CC0: Public Domain
- **License URL:** https://creativecommons.org/publicdomain/zero/1.0/
- **Version:** 10 (raw_AllClasses)
- **Download Method:** Roboflow streaming zip export (`yolov8`)
- **Image Count:** 7,035 images
- **Class List:** `head`, `helmet`, `person`
- **Annotation Format:** YOLO format
- **Download Date:** 2026-09-20
- **Download Status:** DOWNLOADED & EXTRACTED
- **Verification Status:** VERIFIED
- **Purpose:** Core worker/person detection and head/helmet relationship modeling.

---

## 4. D-Fire (Fire & Smoke)
- **Dataset Name:** D-Fire & Smoke Object Detection Dataset
- **Source:** GitHub (GAIA) / Roboflow Universe
- **URL:** https://github.com/gaia-solutions-on-demand/DFireDataset | https://universe.roboflow.com/test-pzbxl/fire-smoke-yolov8
- **License:** CC BY 4.0 / GPL-3.0
- **License URL:** https://raw.githubusercontent.com/gaia-solutions-on-demand/DFireDataset/master/LICENSE
- **Version:** 1
- **Download Method:** Git clone (repo) + direct export (fire_smoke)
- **Image Count:** 4,631 images
- **Class List:** `Fire`, `Smoke`
- **Annotation Format:** YOLO format (polygons converted to standard bounding boxes)
- **Download Date:** 2026-09-20
- **Download Status:** DOWNLOADED & EXTRACTED
- **Verification Status:** VERIFIED
- **Purpose:** Environmental hazard detection (fire and smoke).