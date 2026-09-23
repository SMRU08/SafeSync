# RAKSHYA VISION — Dataset Download Issues & Manual Action Guide

This document records datasets requiring manual download or special authentication, exact reasons for manual action, and step-by-step instructions for Sahil.

---

## 1. SH17 PPE Dataset

- **DATASET:** SH17 PPE Dataset
- **URL:** https://github.com/ahmadmughees/SH17dataset | https://www.kaggle.com/datasets/mugheesahmad/sh17-dataset-for-ppe-detection
- **STATUS:** MANUAL DOWNLOAD REQUIRED / AUTHENTICATION REQUIRED
- **REASON:** The GitHub repository contains annotation tools, `sh17.yaml`, and metadata, but the actual image dataset (several gigabytes) is hosted exclusively on Kaggle. Kaggle requires user authentication (`kaggle.json` API token or manual browser download).
- **ACTUAL ERROR:** `Kaggle authentication required: No valid kaggle.json found in ~/.kaggle/ and anonymous HTTP download is blocked by Kaggle Cloudflare.`
- **DOWNLOAD METHOD ATTEMPTED:** GitHub API inspection and direct repository clone. Verified repo contains configuration `sh17.yaml` and scripts, but points to Kaggle for image archives.
- **WHAT IS REQUIRED:** Manual download from Kaggle using browser login, or placing `kaggle.json` in user home directory.
- **MANUAL ACTION FOR SAHIL:**
  1. Open https://www.kaggle.com/datasets/mugheesahmad/sh17-dataset-for-ppe-detection in your web browser.
  2. Log into your Kaggle account.
  3. Click **Download** (archive zip file).
  4. Extract the contents directly into: `D:\Additional\PROJECT\RAKSHYA-VISION\datasets\raw\sh17\`
- **EXPECTED LOCAL DIRECTORY:** `datasets/raw/sh17/`
- **REQUIRED FORMAT:** YOLO format (images in `images/` or `train/val/test`, labels in `labels/` matching `sh17.yaml`).

---

## 2. D-Fire Mirror (FireDataset by wizbeans)

- **DATASET:** D-Fire Mirror
- **URL:** https://github.com/wizbeans/FireDataset
- **STATUS:** DUPLICATE OF EXISTING DATASET (RESOLVED)
- **REASON:** Detailed code, README, and URL audit confirms that `wizbeans/FireDataset` is a direct academic mirror of `gaia-solutions-on-demand/DFireDataset` (by Pedro Vinícius Almeida Borges de Venâncio et al. / GAIA). Both point to the exact same Google Drive file IDs and contain the identical 4,631 images and annotations already preserved in `datasets/raw/d_fire/`.
- **ACTUAL ERROR:** `N/A — Exact upstream duplicate detected.`
- **DOWNLOAD METHOD ATTEMPTED:** Repository inspection, upstream author comparison, and Google Drive URL checksum matching.
- **WHAT IS REQUIRED:** No manual download needed. Content is already 100% available and verified in `datasets/raw/d_fire/`. To avoid data leakage and double-counting, this dataset is merged into `d_fire`.
- **MANUAL ACTION FOR SAHIL:** None.
- **EXPECTED LOCAL DIRECTORY:** `datasets/raw/d_fire/`
- **REQUIRED FORMAT:** YOLO format (already present).

---

## 3. Roboflow Universe Authentication Status

> [!NOTE]
> Sahil provided the Roboflow API key via prompt. With this key, the following datasets are being automatically downloaded directly into `datasets/raw/` via the Roboflow SDK:
> - `ppe_shikk` $\rightarrow$ `datasets/raw/ppe_shikk/` (DOWNLOADED & VERIFIED)
> - `ppe_safup` $\rightarrow$ `datasets/raw/ppe_safup/` (IN PROGRESS)
> - `safety_ppe_4` $\rightarrow$ `datasets/raw/safety_ppe_4/` (QUEUED)
> - `safety_ppe` $\rightarrow$ `datasets/raw/safety_ppe/` (QUEUED)
> - `bangga_ppe` $\rightarrow$ `datasets/raw/bangga_ppe/` (QUEUED)
>
> If the API key ever expires or quota limits are reached, Sahil can export any of these projects manually as `YOLOv8` zips from Roboflow Universe and place them into the respective directories under `datasets/raw/`.
