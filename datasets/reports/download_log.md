# RAKSHYA VISION — Dataset Download Audit Log

Tracks access verification, attempts, authentication requirements, and statuses for each target dataset.

## Status Dictionary
- `PENDING`
- `DOWNLOADING`
- `DOWNLOADED`
- `EXTRACTED`
- `VALIDATING`
- `VERIFIED`
- `FAILED`
- `SKIPPED`

---

## Download Records

### Record 1: Hard Hat Workers
- **Dataset:** Hard Hat Workers
- **URL:** https://public.roboflow.com/object-detection/hard-hat-workers
- **Start Time:** 2026-09-20T13:31:00Z
- **End Time:** 2026-09-20T13:32:00Z
- **Status:** PENDING
- **Attempts:** 1
- **Error:** Roboflow download requires API key authentication or user export session.
- **Recovery Attempted:** Inspected public metadata; configured Roboflow adapter and API key parameter.
- **Final Result:** Adapter ready for user API key injection.
- **Files Downloaded:** 0
- **Verification Result:** Not verified until downloaded.

### Record 2: PPE Detection & Compliance
- **Dataset:** PPE Detection & Compliance
- **URL:** https://universe.roboflow.com/izanagi/ppe-detection-and-compliance
- **Start Time:** 2026-09-20T13:31:30Z
- **End Time:** 2026-09-20T13:32:15Z
- **Status:** PENDING
- **Attempts:** 1
- **Error:** Roboflow Universe endpoints require authenticated API key.
- **Recovery Attempted:** Integrated Roboflow SDK adapter.
- **Final Result:** Adapter ready.
- **Files Downloaded:** 0
- **Verification Result:** Not verified until downloaded.

### Record 3: Construction PPE
- **Dataset:** Construction PPE
- **URL:** https://universe.roboflow.com/skcet-g4h72/construction-ppe-rdhzo
- **Start Time:** 2026-09-20T13:32:00Z
- **End Time:** 2026-09-20T13:32:30Z
- **Status:** PENDING
- **Attempts:** 1
- **Error:** Roboflow Universe endpoints require authenticated API key.
- **Recovery Attempted:** Integrated Roboflow SDK adapter.
- **Final Result:** Adapter ready.
- **Files Downloaded:** 0
- **Verification Result:** Not verified until downloaded.

### Record 4: D-Fire
- **Dataset:** D-Fire
- **URL:** https://github.com/gaia-solutions-on-demand/DFireDataset
- **Start Time:** 2026-09-20T13:30:00Z
- **End Time:** 2026-09-20T13:33:30Z
- **Status:** PENDING
- **Attempts:** 2
- **Error:** Upstream OneDrive direct download link returned 404/requires browser session.
- **Recovery Attempted:** Inspected official Kaggle alternative source listed in README (`sayedgamal99/smoke-fire-detection-yolo`).
- **Final Result:** Documented official mirror options in SOURCES.md; adapter ready.
- **Files Downloaded:** 0
- **Verification Result:** Not verified until downloaded.