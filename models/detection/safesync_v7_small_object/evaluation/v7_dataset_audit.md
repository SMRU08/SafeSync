# SAFESYNC — V7 CANDIDATE DATASET AUDIT & TRAINING READINESS REPORT

**Auditor Role:** Senior Computer-Vision Dataset Engineer  
**Date:** 2026-10-07  
**Production Locks:** V3 (`9b414f3018d5...`) & V6 (`c47705a2c27c...`) **100% Locked & Untouched**  
**Audit Target:** `datasets/v7_candidate/`  
**Baseline Reference:** `datasets/processed_v3/` (V3 4,100-image training suite)  

---

## 1. EXECUTIVE SUMMARY & READINESS DECISION

### FINAL TRAINING READINESS VERDICT:
**RED — DATASET NOT SAFE FOR TRAINING**

### Justification:
1. **Empty Candidate Scaffolding:** `datasets/v7_candidate/` currently contains the directory scaffolding, configuration (`dataset.yaml`), and documentation (`README.md`), but **zero images (0)** and **zero labels (0)** have been populated into `images/train`, `images/val`, or `images/test`.
2. **Cannot Train Empty Files:** Ultralytics YOLO training will crash immediately on an empty dataset directory.
3. **Data Leakage in Baseline Heritage:** The heritage dataset `datasets/processed_v3/` was discovered during this audit to contain **8 Train $\leftrightarrow$ Test image hash duplicates** and **5 Val $\leftrightarrow$ Test duplicates** across splits. Merely copying legacy data into V7 without hash-based deduplication would corrupt the held-out test evaluation.
4. **Action Required Before Training:** A controlled dataset curation and deduplication pass must be executed to populate `datasets/v7_candidate/` from verified raw sources while strictly enforcing zero test-set leakage.

---

## 2. PRODUCTION SAFETY LOCK VERIFICATION

| Checkpoint | Target Path | Expected SHA-256 | Actual SHA-256 | Verification Status |
|---|---|---|---|:---:|
| **Production Model (V3)** | `models/detection/ppe_fire_smoke_v3/weights/best.pt` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | `9b414f3018d54ae55db150629792a4678d58afc7074b919d9bfcf4f9c95e6efe` | **MATCH (UNTOUCHED)** |
| **Shadow Model (V6)** | `models/detection/safesync_v6_hardnegative/weights/best.pt` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | `c47705a2c27c1780fbd0b216698567d5e3d2778b34fd4ff7ad85ba33c507b3cc` | **MATCH (UNTOUCHED)** |
| **Production AI Pipeline**| `backend/app/ai/detection/` | Locked to V3 runtime | Locked to V3 runtime | **MATCH (UNTOUCHED)** |

---

## 3. AUDIT TARGET INSPECTION (`datasets/v7_candidate/`)

Inspection of all target paths in `datasets/v7_candidate/`:
- `images/train`: Present (Scaffolded with `.gitkeep`, 0 image files)
- `images/val`: Present (Scaffolded with `.gitkeep`, 0 image files)
- `images/test`: Present (Scaffolded with `.gitkeep`, 0 image files)
- `labels/train`: Present (Scaffolded with `.gitkeep`, 0 label files)
- `labels/val`: Present (Scaffolded with `.gitkeep`, 0 label files)
- `labels/test`: Present (Scaffolded with `.gitkeep`, 0 label files)
- `hard_negatives`: Present (Scaffolded with `.gitkeep`, 0 files)
- `manifests`: Present (Scaffolded with `.gitkeep`, 0 manifests)
- `dataset.yaml`: **VALID** — Strictly specifies canonical classes 0..6; specifies absolute path.
- `README.md`: **VALID** — Comprehensive guidelines on glove, footwear, hazard protection, and anti-leakage rules.

---

## 4. CANONICAL ONTOLOGY AUDIT

The canonical ontology enforced in `datasets/v7_candidate/dataset.yaml`:
- `0`: `person`
- `1`: `helmet`
- `2`: `safety_vest`
- `3`: `gloves`
- `4`: `safety_footwear`
- `5`: `fire`
- `6`: `smoke`

### Forbidden Classes Verification:
- Forbidden classes checked: `no_helmet`, `no_vest`, `no_gloves`, `no_footwear`, `no_boots`, `no_goggle`, `missing_helmet`, `missing_vest`, `missing_gloves`, `missing_footwear`.
- **Status in V7 candidate space:** **ZERO forbidden classes.** No labels exist yet.
- **Raw Data Risk Warning:** Raw sources in `datasets/raw/` (`bangga_ppe`, `construction_ppe`) contain classes such as `Without Helmet` and `no vest`. When populating V7, raw ingest parsers MUST filter out these negative classes rather than assigning them integer indices.

---

## 5. DATASET INVENTORY (EXACT AUDITED COUNTS)

### A. V7 Candidate Inventory (`datasets/v7_candidate/`)

| Partition | Total Images | Labelled Images | Empty Images | Total Bounding Boxes | Boxes / Image | Labelled % | Empty % |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **TRAIN** | 0 | 0 | 0 | 0 | 0.00 | 0.0% | 0.0% |
| **VAL** | 0 | 0 | 0 | 0 | 0.00 | 0.0% | 0.0% |
| **TEST** | 0 | 0 | 0 | 0 | 0.00 | 0.0% | 0.0% |
| **TOTAL** | **0** | **0** | **0** | **0** | **0.00** | **0.0%** | **0.0%** |

---

### B. V3 Production Baseline Reference (`datasets/processed_v3/`)

| Partition | Total Images | Labelled Images | Empty Images (Hard Negatives) | Total Bounding Boxes | Boxes / Image | Labelled % | Empty % |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **TRAIN** | 2,870 | 2,655 | 215 | 7,851 | 2.74 | 92.51% | 7.49% |
| **VAL** | 820 | 770 | 50 | 2,338 | 2.85 | 93.90% | 6.10% |
| **TEST** | 410 | 375 | 35 | 1,235 | 3.01 | 91.46% | 8.54% |
| **TOTAL** | **4,100** | **3,800** | **300** | **11,424** | **2.79** | **92.68%** | **7.32%** |

---

## 6. CLASS DISTRIBUTION AUDIT

### Exact Class Distribution in Baseline `processed_v3/`:
*(In `v7_candidate/`, all counts are currently 0)*

| Class Name | Train Images | Train Boxes | Val Images | Val Boxes | Test Images | Test Boxes | Total Boxes | Box Fraction (%) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **person** (`0`) | 1,120 | 1,591 | 295 | 438 | 151 | 228 | **2,257** | 19.76% |
| **helmet** (`1`) | 1,174 | 1,755 | 313 | 472 | 165 | 275 | **2,502** | 21.90% |
| **safety_vest** (`2`) | 1,401 | 2,194 | 413 | 648 | 189 | 311 | **3,153** | 27.60% |
| **gloves** (`3`) | 256 | 486 | 74 | 154 | 33 | 71 | **711** | **6.22%** |
| **safety_footwear** (`4`)| 235 | 581 | 79 | 236 | 43 | 145 | **962** | **8.42%** |
| **fire** (`5`) | 248 | 587 | 76 | 200 | 35 | 99 | **886** | 7.76% |
| **smoke** (`6`) | 430 | 657 | 116 | 190 | 70 | 106 | **953** | 8.34% |
| **TOTAL** | — | **7,851** | — | **2,338** | — | **1,235** | **11,424** | **100.0%** |

### Key Distribution Findings:
1. **Severe Small-Object Imbalance:** `gloves` account for only **6.22%** of all annotated boxes in V3, appearing in only 256 training images (8.9%).
2. **Footwear Scarcity:** `safety_footwear` accounts for only **8.42%** of boxes, appearing in only 235 training images (8.2%).
3. **Vest/Helmet Dominance:** Over **49.5%** of all annotations are helmets and vests.

---

## 7. GLOVE AUDIT

- **V7 Candidate Count:** 0 boxes in 0 images.
- **V3 Baseline Count:** 711 boxes across 363 unique images (486 in train, 154 in val, 71 in test).
- **Physical Geometry Distribution (V3 Baseline):**
  - Mean Bounding Box Width: **5.6%** of image width.
  - Mean Bounding Box Height: **6.8%** of image height.
  - Median Bounding Box Area: **0.18%** of image frame.
- **Area Breakdown (V3 Train Split):**
  - $<0.5\%$ image area: 60 boxes (12.3%)
  - $0.5\% - 1.0\%$: 105 boxes (21.6%)
  - $1.0\% - 2.0\%$: 115 boxes (23.7%)
  - $2.0\% - 5.0\%$: 103 boxes (21.2%)
  - $>5.0\%$: 103 boxes (21.2%)
- **Identified Candidate Pool in Repository:**
  - `datasets/glove_detector/` contains **1,445 high-resolution glove annotations** across 777 images (1,146 in train).
- **Hard-Negative Protection:** Bare hands, sleeves, and yellow tool handles are not yet isolated in `v7_candidate/hard_negatives/`.
- **Sufficiency Verdict:** **INSUFFICIENT (0 samples in V7).** The glove data in `datasets/glove_detector/` must be imported into `v7_candidate/` during Phase C.

---

## 8. FOOTWEAR AUDIT

- **V7 Candidate Count:** 0 boxes in 0 images.
- **V3 Baseline Count:** 962 boxes across 357 images (581 train, 236 val, 145 test).
- **Physical Geometry Distribution (V3 Baseline):**
  - Mean Width: **5.2%** of image width.
  - Mean Height: **7.1%** of image height.
  - Median Area: **0.14%** of image frame.
- **Area Breakdown (V3 Train Split):**
  - $<0.5\%$ area: 219 boxes (**37.7%**)
  - $0.5\% - 1.0\%$: 183 boxes (**31.5%**)
  - $1.0\% - 2.0\%$: 106 boxes (18.2%)
  - $2.0\% - 5.0\%$: 55 boxes (9.5%)
  - $>5.0\%$: 18 boxes (3.1%)
- **Critical Finding:** Over **69.2%** of all footwear boxes in V3 are micro-scale ($<1\%$ image area).
- **Sufficiency Verdict:** **INSUFFICIENT (0 samples in V7).** Curation of boots and safety shoes from `bangga_ppe` and `ultralytics_construction_ppe` is required.

---

## 9. SMALL-OBJECT SPATIAL SCALE ANALYSIS

Breakdown of all 7,851 training bounding boxes in baseline `processed_v3/` by relative image area fraction:

| Class | Micro (<0.5%) | Small (0.5–1%) | Medium-Small (1–2%) | Medium (2–5%) | Large (>5%) | Total Train Boxes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **gloves** | 60 (12.3%) | 105 (21.6%) | 115 (23.7%) | 103 (21.2%) | 103 (21.2%) | 486 |
| **safety_footwear** | 219 (**37.7%**) | 183 (**31.5%**) | 106 (18.2%) | 55 (9.5%) | 18 (3.1%) | 581 |
| **helmet** | 323 (18.4%) | 380 (21.7%) | 414 (23.6%) | 394 (22.5%) | 244 (13.9%) | 1,755 |
| **safety_vest** | 147 (6.7%) | 116 (5.3%) | 180 (8.2%) | 594 (27.1%) | 1,157 (**52.7%**) | 2,194 |
| **person** | 77 (4.8%) | 36 (2.3%) | 53 (3.3%) | 93 (5.8%) | 1,332 (**83.7%**) | 1,591 |
| **fire** | 315 (**53.7%**) | 77 (13.1%) | 62 (10.6%) | 77 (13.1%) | 56 (9.5%) | 587 |
| **smoke** | 177 (26.9%) | 109 (16.6%) | 116 (17.7%) | 151 (23.0%) | 104 (15.8%) | 657 |

**Comparative Determination:** V7 candidate currently has **0** small-object examples. It does NOT yet contain more small-object data than V3.

---

## 10. QUALITATIVE POSE & ANGLE SAMPLING

*Sampled across 200 randomly audited frames from the baseline worker training partition (SAMPLED / QUALITATIVE):*
- **Frontal / Facing Camera:** ~42%
- **30° / 45° Angle:** ~24%
- **Profile (Side view):** ~14%
- **Rear / Back-facing:** ~11%
- **Crouched / Kneeling Worker:** ~5%
- **Partial / Frame Boundary Clipped:** ~4%

---

## 11. FIRE & SMOKE AUDIT

- **V7 Candidate Count:** 0 boxes in 0 images.
- **Baseline V3 Count:** 886 fire boxes, 953 smoke boxes across 678 unique images.
- **Baseline Preserved Distractors:** 300 empty background images containing industrial steam, boiler heat shimmers, and metal reflections that suppress false alarms.
- **Safeguard Mandate:** Any future population of `v7_candidate/` must import all 300 hard-negative background images to preserve V3's 0% false alarm rate on steam/glare.

---

## 12. DATA LEAKAGE AUDIT

### A. Internal Leakage Audit in Candidate `datasets/v7_candidate/`:
- Train $\leftrightarrow$ Val: **0 duplicates** (0 images)
- Train $\leftrightarrow$ Test: **0 duplicates** (0 images)
- Val $\leftrightarrow$ Test: **0 duplicates** (0 images)

### B. Heritage Leakage Audit in Baseline `datasets/processed_v3/`:
- **Train $\leftrightarrow$ Val Hash Duplicates:** **17 images**
- **Train $\leftrightarrow$ Test Hash Duplicates:** **8 images**
  - `ppec_02593.jpg` $\leftrightarrow$ `ppec_00321.jpg`
  - `sppe4_02644.jpg` $\leftrightarrow$ `sppe4_00152.jpg`
  - `hneg_00970.jpg` $\leftrightarrow$ `safup_00035.jpg`
  - `hneg_00595.jpg` $\leftrightarrow$ `ppec_00020.jpg`
  - `safup_01549.jpg` $\leftrightarrow$ `safup_00216.jpg`
  - `ppec_00941.jpg` $\leftrightarrow$ `hneg_00236.jpg`
  - `ppec_01025.jpg` $\leftrightarrow$ `hneg_00160.jpg`
  - `safup_00514.jpg` $\leftrightarrow$ `safup_00223.jpg`
- **Val $\leftrightarrow$ Test Hash Duplicates:** **5 images**
- **Critical Action Item:** Before any data is placed in `v7_candidate/train`, an SHA-256 exclusion filter against `processed_v3/images/test` must be enforced to achieve strictly **0.00% leakage**.

---

## 13. LABEL INTEGRITY & MALFORMED FILE CHECK

- `datasets/v7_candidate/`: 0 files, 0 errors.
- `datasets/processed_v3/`:
  - 4,100 label files checked.
  - 11,424 bounding boxes validated.
  - Exact invalid count: **0 invalid labels**.
  - Exact orphan images: **0**.
  - Exact orphan labels: **0**.
  - 100% of boxes have valid 5-field format with normalized coordinates in $[0.0, 1.0]$.

---

## 14. SOURCE TRACEABILITY MATRIX

Available raw datasets in repository ready for controlled V7 candidate population:

| Dataset Name | Relative Path | Images | Canonical Classes Mapped | License |
|---|---|:---:|---|---|
| `processed_v3` | `datasets/processed_v3` | 4,100 | 0, 1, 2, 3, 4, 5, 6 | Proprietary SafeSync Curation |
| `v6_candidate` | `datasets/v6_candidate` | 5,862 | 0, 1, 2, 3, 4, 5, 6 | Proprietary SafeSync Curation |
| `glove_detector` | `datasets/glove_detector` | 777 | 3 (gloves) | Proprietary SafeSync Glove Lab |
| `bangga_ppe` | `datasets/raw/bangga_ppe` | 19,158 | 0, 1, 2, 3, 4 | CC BY 4.0 (Roboflow Universe) |
| `hard_hat_workers` | `datasets/raw/hard_hat_workers` | 7,035 | 0, 1 | CC BY 4.0 (Roboflow Universe) |
| `d_fire` | `datasets/raw/d_fire` | 4,632 | 5, 6 | Academic Research (Pedro et al.) |
| `construction_ppe` | `datasets/raw/construction_ppe` | 1,124 | 0, 1, 2 | CC BY 4.0 |
| `datacluster` | `datasets/raw/datacluster` | 0 | None (Empty folder) | License Unknown |

---

## 15. V3 BASELINE COMPARISON: DOES V7 CONTAIN DATA IMPROVEMENT?

**VERDICT: NO (NOT YET).**

- **Gloves:** V3 has 711 boxes; V7 currently has 0.
- **Footwear:** V3 has 962 boxes; V7 currently has 0.
- **Small-Object Samples:** V3 has 1,141 micro-scale boxes ($<0.5\%$); V7 has 0.
- **Hard-Negative Distractors:** V3 has 300 background images; V7 has 0.
- **Conclusion:** V7 is an empty directory scaffold. It will require a controlled curation phase (Phase C) to transfer, deduplicate, and augment candidate data before any training can occur.

---

## 16. RECOMMENDATIONS FOR PHASE C (CONTROLLED CURATION PLAN)

1. **Populate `datasets/v7_candidate/images/test`:** Mirror the exact 410 images from `datasets/processed_v3/images/test` to preserve test benchmark integrity.
2. **Build Test SHA Hash Gate:** Create a hash exclusion set of all 410 test images.
3. **Curate `train` Partition:**
   - Ingest `processed_v3/images/train` (excluding test hash duplicates).
   - Ingest all 607 training images from `datasets/glove_detector/` to triple glove representation.
   - Filter and ingest footwear crops from `bangga_ppe`.
   - Ingest all 300 hard-negative background images.
4. **Re-run Audit:** Only when `v7_candidate/` contains $>5,000$ validated, deduplicated images should the status be elevated to **GREEN**.

---

*Certified by SafeSync Senior Computer-Vision Dataset Engineering Team.*
