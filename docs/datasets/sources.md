# Dataset Sources & Distribution

This document details the public datasets ingested, split distributions, and licensing metadata supporting SafeSync.

---

## 1. Primary Dataset Sources

| Dataset Name | Domain / Target Classes | Total Ingested Images | Source / Repository Reference |
|---|---|:---:|---|
| **Pictor Construction Safety** | Workers, Helmets, Vests | 1,487 | Pictor Academy Benchmark |
| **Hard Hat Workers** | Workers, Helmets, Vests | 7,035 | Roboflow Universe |
| **Construction Site Safety (CSS)** | Workers, Helmets, Vests, Gloves, Footwear | 9,451 | Roboflow / Kaggle Site Safety |
| **D-Fire Combustion Dataset** | Active Fire, Smoke Plumes | 4,480 | D-Fire Open Research Group |
| **Total Ingested Raw Dataset** | Canonical 7 Classes | **22,453** | **Zero Cross-Split Leakage** |

---

## 2. Split Partitioning & Bounding Box Counts

The normalized dataset is partitioned into deterministic Train, Validation, and Test splits:

```
Total Ingested: 22,453 Images
├── Train Split (70%): 15,717 Images (35,836 Bounding Boxes)
├── Validation Split (20%): 4,490 Images (10,239 Bounding Boxes)
└── Test Split (10%): 2,246 Images (5,120 Bounding Boxes)
```

### 2.1 Bounding Box Class Distribution

| Class ID | Class Name | Train Split | Val Split | Test Split | Total Bounding Boxes |
|---|---|:---:|:---:|:---:|:---:|
| `0` | `person` | 3,881 | 1,107 | 557 | **5,545** |
| `1` | `helmet` | 17,171 | 4,906 | 2,454 | **24,531** |
| `2` | `safety_vest` | 4,390 | 1,254 | 628 | **6,272** |
| `3` | `gloves` | 1,180 | 337 | 169 | **1,686** |
| `4` | `safety_footwear` | 913 | 261 | 131 | **1,305** |
| `5` | `fire` | 4,452 | 1,272 | 636 | **6,360** |
| `6` | `smoke` | 3,849 | 1,102 | 545 | **5,496** |
| **Total** | **All Classes** | **35,836** | **10,239** | **5,120** | **51,195** |

---

## 3. Split Integrity & Leakage Prevention

1. **Hash-Based Partitioning:** Image files are hashed via SHA-256 before partitioning. Duplicate images across raw sources are identified and merged to prevent the same visual frame appearing in both training and test sets.
2. **Video Sequence Separation:** Frames extracted from sequential video clips are kept within the same partition to eliminate temporal data leakage.
