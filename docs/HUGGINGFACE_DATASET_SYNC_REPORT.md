# SafeSync — Hugging Face Dataset Sync Report
## New Source Audit & Ingestion: `smrutiranjannayakcs/PPE_Detection-bucket`
**Document Version:** 1.0.0  
**Date of Ingestion:** September 29, 2026  
**Ingestion Status:** SUCCESS (Verified & Synchronized)  

---

## 1. Resource Forensic Audit & Identification

Prior to downloading, the Hugging Face resource was programmatically probed across all Hub resource types (Model Repository, Dataset Repository, Space, and Storage Bucket):

| Resource Type Probed | API Endpoint | Response Status | Determination |
| :--- | :--- | :---: | :--- |
| **Hugging Face Model** | `https://huggingface.co/api/models/smrutiranjannayakcs/PPE_Detection-bucket` | 404 Not Found | Not a Model |
| **Hugging Face Dataset** | `https://huggingface.co/api/datasets/smrutiranjannayakcs/PPE_Detection-bucket` | 404 Not Found | Not a Git Dataset |
| **Hugging Face Space** | `https://huggingface.co/api/spaces/smrutiranjannayakcs/PPE_Detection-bucket` | 404 Not Found | Not a Space |
| **Hugging Face Storage Bucket** | `https://huggingface.co/api/buckets/smrutiranjannayakcs/PPE_Detection-bucket` | **200 OK** | **AUTHENTICATED STORAGE BUCKET** |

### Resource Metadata:
- **Bucket ID:** `smrutiranjannayakcs/PPE_Detection-bucket`
- **Owner / Author:** `smrutiranjannayakcs` (Full Name: Smruti Ranjan Nayak)
- **Bucket Technology:** Hugging Face Xet-powered Object Storage (S3-compatible mutable bucket)
- **Access Status:** Public (`"private": false`)
- **Total Files:** 3
- **Total Payload Size:** 667,695,086 bytes (~667.7 MB)
- **Created Timestamp:** `2026-09-29T06:59:31.000Z`
- **Updated Timestamp:** `2026-09-29T07:00:22.139Z`

---

## 2. Bucket File Inventory & Discovered Entities

Listing obtained via `HfFileSystem` (`hf://buckets/smrutiranjannayakcs/PPE_Detection-bucket/`):

| File Path in Bucket | File Size (Bytes) | Xet Content Hash (SHA-256) | Ingestion Action |
| :--- | :---: | :--- | :--- |
| `.gitattributes` | 2,461 B | `19463de8293cfbe466dc4583dc14df84f96f263bdf21cd76abda5e283c6fb4b5` | Downloaded |
| `README.md` | 1,957 B | `f448e9dbe1cb2fa178f82208e1b9b0d64fdf708875417ac7332879a3535b6b57` | Downloaded & Audited |
| `PPE.zip` | 667,690,668 B (~636.8 MB) | `ddd4dbfbebde2b4ef2a1fd3a5c86226be2e21148be08f48b86e52c3f7cbebc0c` | Downloaded with Range Resume & Extracted |

---

## 3. Network Resilience & Synchronization Mechanism

- **Client Implementation:** [`scripts/dataset/sync_hf_bucket.py`](file:///D:/Additional/PROJECT/RAKSHYA-VISION/scripts/dataset/sync_hf_bucket.py)
- **Protocol:** HTTP 206 Partial Content Range Requests (`bytes={downloaded_bytes}-`)
- **Error Recovery:** A transient SSL handshake timeout occurred during the initial connection; the resumable stream automatically reconnected with exponential backoff and resumed from byte offset 243,269,632 without restarting from zero.
- **Local Target Directory:** `data/raw/huggingface/PPE_Detection-bucket/`
- **Extracted Contents:** `data/raw/huggingface/PPE_Detection-bucket/extracted/`

---

## 4. Dataset Content, Classes & Annotation Statistics

The dataset archive `PPE.zip` contains a complete YOLOv8 object detection structure with images and labels partitioned into `train`, `valid`, and `test` splits.

### Original Dataset Class Taxonomy:
```yaml
names:
  - Vest
  - Safety Shoe
  - Mask
  - Helmet
  - Goggles
  - Gloves
```

### Raw Annotated Object Breakdown:
| Class Name | Total Annotated Objects | Semantic Alignment to SafeSync PS06 | SafeSync Canonical Class |
| :--- | :---: | :--- | :--- |
| **Vest** | 4,418 | Direct Match | `safety_vest` (Class 2) |
| **Helmet** | 2,703 | Direct Match | `helmet` (Class 1) |
| **Gloves** | 2,693 | Direct Match | `gloves` (Class 3) |
| **Safety Shoe** | 2,006 | Direct Match | `safety_footwear` (Class 4) |
| **Mask** | 2,763 | Non-Canonical (Sanitary PPE) | Filtered / Ignored |
| **Goggles** | 1,431 | Non-Canonical (Eye Protection) | Filtered / Ignored |
| **Total Objects** | **16,014** | **11,820 Usable Canonical Instances** | **73.8% Direct Utilization** |

---

## 5. Security & Credential Compliance

- **Authentication Method:** Public access verified; token bypass supported.
- **Zero Credential Exposure:** No tokens, API keys, or private secrets were hard-coded, printed, or committed to configuration files or git logs.
