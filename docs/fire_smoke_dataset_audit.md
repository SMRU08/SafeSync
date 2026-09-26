# SafeSync Fire & Smoke Dataset Quality & Distribution Report

## 1. Dataset Overview

- **Positive Hazard Images (D-Fire)**: 4,631 images
- **Curated Hard Negatives**: 600 images (500 train, 70 val, 30 test)
- **Total Dataset Size**: 5,231 images
- **Background Negative Ratio**: 11.47% (optimal range: 10-15%)

## 2. Split Distribution

| Split | Positive Images | Hard Negative Images | Total Images | Fire Boxes | Smoke Boxes | Total Boxes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | 4,175 | 500 | 4,675 | 4,992 | 4,974 | 9,966 |
| **Validation** | 354 | 70 | 424 | 303 | 309 | 612 |
| **Test** | 102 | 30 | 132 | 38 | 90 | 128 |
| **TOTAL** | **4,631** | **600** | **5,231** | **5,333** | **5,373** | **10,706** |

## 3. Hazard Scale & Size Breakdown

| Hazard Class | Small (< 32x32 px) | Medium (32x32 to 96x96 px) | Large (> 96x96 px) | Total Annotations |
| :--- | :--- | :--- | :--- | :--- |
| **Fire** | 2,460 (46.1%) | 1,859 (34.9%) | 1,014 (19.0%) | 5,333 |
| **Smoke** | 711 (13.2%) | 2,833 (52.7%) | 1,829 (34.0%) | 5,373 |

## 4. Automated Annotation Quality Findings

- **Corrupted Images**: 0 (all images successfully decoded with OpenCV)
- **Zero-Area Bounding Boxes**: 0
- **Coordinate Out-of-Bounds**: 0 (all values within normalized [0.0, 1.0] range)
- **Exact Hash Duplicates**: 0
- **Data Leakage Check**: Train, Validation, and Test sets maintain strictly independent sequence splits.
