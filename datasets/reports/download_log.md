# RAKSHYA VISION — Dataset Download Audit Log

## Download Records

### Record 1: Construction PPE
- **Dataset:** Construction PPE
- **URL:** https://universe.roboflow.com/skcet-g4h72/construction-ppe-rdhzo
- **Start Time:** 2026-09-20T14:01:30Z
- **End Time:** 2026-09-20T14:01:45Z
- **Status:** VERIFIED
- **Attempts:** 1
- **Error:** None
- **Recovery Attempted:** N/A
- **Final Result:** Downloaded and extracted into `datasets/raw/construction_ppe/`
- **Files Downloaded:** 1,124 images + labels
- **Verification Result:** Passed all checks (0 corrupted).

### Record 2: Hard Hat Workers
- **Dataset:** Hard Hat Workers
- **URL:** https://public.roboflow.com/object-detection/hard-hat-workers
- **Start Time:** 2026-09-20T14:09:30Z
- **End Time:** 2026-09-20T17:07:15Z
- **Status:** VERIFIED
- **Attempts:** 2
- **Error:** Initial large download aborted due to connection timeout.
- **Recovery Attempted:** Downloaded directly via verified Roboflow streaming zip endpoint with chunking and SHA-256 validation.
- **Final Result:** Downloaded and extracted into `datasets/raw/hard_hat_workers/`
- **Files Downloaded:** 7,035 images + labels
- **Verification Result:** Passed all checks (0 corrupted).

### Record 3: PPE Detection & Compliance
- **Dataset:** PPE Detection & Compliance
- **URL:** https://universe.roboflow.com/izanagi/ppe-detection-and-compliance
- **Start Time:** 2026-09-20T17:10:00Z
- **End Time:** 2026-09-20T17:17:45Z
- **Status:** VERIFIED
- **Attempts:** 2
- **Error:** Transient DNS name resolution error on initial stream attempt.
- **Recovery Attempted:** Automatic retry with backoff.
- **Final Result:** Downloaded and extracted into `datasets/raw/ppe_detection_compliance/`
- **Files Downloaded:** 9,663 images + labels
- **Verification Result:** Passed all checks (0 corrupted).

### Record 4: D-Fire / Fire & Smoke
- **Dataset:** D-Fire (Fire & Smoke)
- **URL:** https://github.com/gaia-solutions-on-demand/DFireDataset
- **Start Time:** 2026-09-20T13:48:00Z
- **End Time:** 2026-09-20T17:27:45Z
- **Status:** VERIFIED
- **Attempts:** 1
- **Error:** None
- **Recovery Attempted:** Cloned official GitHub repository; downloaded Roboflow Fire-Smoke export.
- **Final Result:** Extracted into `datasets/raw/d_fire/`
- **Files Downloaded:** 4,631 images + labels
- **Verification Result:** Passed all checks (0 corrupted).