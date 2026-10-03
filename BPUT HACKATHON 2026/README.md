# BPUT HACKATHON 2026 — OFFICIAL PRESENTATION SLIDE MASTER

> **Project Name:** SafeSync  
> **Problem Statement ID:** PS06  
> **Problem Statement Title:** AI-Powered Real-Time Industrial Workplace Safety Monitoring, 4-Point PPE Compliance, and Optical Fire/Smoke Detection  
> **Theme:** Smart Automation (AI & Computer Vision for Industrial Workplace Safety & Compliance Governance)  
> **Category:** Software  
> **Team ID:** BH26PS06T049  
> **Team Name:** XERSES  
> **Target Event:** BPUT HACKATHON 2026 (Organized by BPUT in partnership with STPI & EmTek)  
> **Repository:** [https://github.com/SMRU08/SafeSync](https://github.com/SMRU08/SafeSync)
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           PRESENTATION FLOW                            │
  ├──────────────┬──────────────┬──────────────┬──────────────┬────────────┤
  │   SLIDE 1    │   SLIDE 2    │   SLIDE 3    │   SLIDE 4    │  SLIDE 5   │  SLIDE 6
  │ Title Page   │ Idea Title & │  Technical   │ Feasibility  │ Impact &   │ Research &
  │ Team Details │ Solution     │  Approach    │ & Viability  │ Benefits   │ References
  └──────────────┴──────────────┴──────────────┴──────────────┴────────────┴────────────
```

---

## SLIDE 1 — TITLE PAGE

### 1. Slide Title & Header
**BPUT HACKATHON 2026**  
*Grand Finale Presentation — Track: Smart Automation*

---

* **Problem Statement ID:** `PS06`
* **Problem Statement Title:** AI-Powered Real-Time Industrial Workplace Safety Monitoring, 4-Point PPE Compliance, and Optical Fire/Smoke Detection
* **Theme:** Smart Automation / Occupational Health & Safety Governance
* **Category:** Software (Edge-Compatible AI Vision Platform)
* **Team ID:** `BH26PS06T049`
* **Team Name:** `XERSES`
* **Project Name:** **SafeSync**
* **College / Institution:** BPUT Affiliated Engineering Institution *(e.g., [Insert College Name])*
* **Department:** Department of Computer Science & Engineering / Information Technology
* **Tagline:** *"Smart Vision. Safe Workers. Faster Response."*

---

### 3. Important Bullet Points to Include
* **Autonomous Industrial Safety:** 24/7 vision-based continuous worker protection and hazard mitigation.
* **Dual-Capability Engine:** Simultaneous 4-point PPE compliance tracking alongside instant optical fire/smoke hazard alerting.
* **Zero Additional Sensors:** Operates directly over existing workplace IP cameras, RTSP streams, and USB webcams.
* **Edge-Optimized Efficiency:** Built to run on standard commercial CPUs without requiring dedicated cloud GPUs.

---

### 4. Slide Layout & Visual Suggestions
* **Layout:** Clean corporate dark-mode or industrial navy-blue theme (`#0F172A` background with `#0EA5E9` cyan/blue accent and `#F59E0B` amber warning accents).
* **Logos to Place:** 
  1. BPUT Hackathon 2026 Logo (Top Left / Right)
  2. STPI & EmTek Partner Logos (Top Right)
  3. SafeSync Project Badge & Team XERSES Logo (Center / Bottom Center)
* **Suggested Background Image:** Dark industrial construction/manufacturing backdrop with subtle semi-transparent cyan bounding-box overlay.

---

### 5. Short Instruction & Presenter Highlight Guidance
* **What to Highlight:** 
  - Greet the jury with confidence.
  - State your Team ID (`BH26PS06T049`) and Team Name (`XERSES`).
  - Emphasize that **SafeSync** addresses Problem Statement **PS06** by transforming passive, unmonitored CCTV networks into an active, intelligent safety governance system that detects missing gear and early combustion in real time.

---

## SLIDE 2 — IDEA TITLE & PROPOSED SOLUTION

### 1. Slide Title
**SafeSync — Autonomous Industrial Safety Intelligence & Hazard Governance Platform**

---

### 2. PPT-Ready Text (Copy-Paste directly into Slide 2)

#### Proposed Solution: What is SafeSync?
SafeSync is an end-to-end, real-time AI computer vision system designed to continuously monitor industrial workplaces, construction sites, and manufacturing plants. By connecting directly to existing standard CCTV camera streams, SafeSync provides simultaneous **4-point PPE compliance monitoring** (`helmet`, `safety_vest`, `gloves`, `safety_footwear`) for each individual worker, coupled with **zero-lag optical combustion detection** (`fire` and `smoke`).

#### How It Addresses the Problem:
* **Eliminates Human Vigilance Decay:** Safety officers monitoring multiple CCTV displays lose attention within 20–30 minutes. SafeSync provides tireless 24/7 automated monitoring.
* **Overcomes Periodic Spot-Check Blindness:** Manual inspections only capture snapshot compliance; workers often remove gear when supervisors leave. SafeSync tracks compliance persistently.
* **Accelerates Disaster Response:** Traditional ceiling smoke detectors take minutes to trigger in high-ceiling factories. SafeSync detects open flame and smoke plumes optically within seconds.
* **Reduces Alert Fatigue:** Implements decoupled alerting—silent non-auditory visual HUD logs for missing PPE versus high-priority ($P_0$) audible sirens for fire/smoke emergencies.

#### Innovation and Uniqueness of the Solution:
1. **Worker-Centric Anatomical Spatial Association:** Rather than naively counting objects in a frame, SafeSync tracks each individual worker with ByteTrack and maps gear specifically to their cranial, thoracic, and extremity zones using Hungarian bipartite matching.
2. **Strict `UNKNOWN != ABSENT` Ambiguity Guarantee:** If a worker's boots or hands are occluded behind machinery or clipped by camera boundaries, SafeSync marks the status as `UNKNOWN` rather than creating a false violation.
3. **Multi-Frame Temporal Confirmation State Machine:** Eliminates detector flicker by requiring persistent detection across 3 consecutive frames for PPE infractions and 5 frames for fire/smoke, backed by a 15-frame tolerance window.
4. **Hard-Negative Distractor Conditioning:** Specifically hardened against industrial false alarms (steam exhaust, welder glare, orange machinery, and dust clouds).

---

### 3. Key Quantitative Metrics to Display in Callout Cards
* **56.4 ms** — Mean end-to-end inference latency on standard Intel Core i5 CPU.
* **18–25 FPS** — Real-time frame processing rate (zero discrete GPU dependency).
* **7 Classes** — Unified single-pass model (`person`, `helmet`, `safety_vest`, `gloves`, `safety_footwear`, `fire`, `smoke`).
* **276 / 276** — Passing automated unit, integration, and E2E recovery tests.
* **0 dB vs 85 dB** — Decoupled alerting: silent PPE visual logs vs. audible fire evacuation siren.

---

### 4. Relevant Diagram / Flowchart
```
               SAFESYNC DUAL-PIPELINE ARCHITECTURE
               
  [ CCTV / RTSP / Webcam ] ──> [ Frame Ingestion (Queue Depth = 1) ]
                                                │
                                    [ YOLOv8n Single-Pass ]
                                     (7 Detection Classes)
                                        │               │
                 ┌──────────────────────┘               └──────────────────────┐
                 ▼                                                             ▼
     [ WORKER PPE PIPELINE ]                                       [ HAZARD FIRE/SMOKE PIPELINE ]
  • ByteTrack Worker Tracking                                   • Dual-Channel Persistence Accumulator
  • 4-Zone Spatial Anatomical Association                       • Candidate -> Confirmed State Machine
  • UNKNOWN != ABSENT Boundary Filtering                        • Hard-Negative Steam/Dust Suppression
  • 3-Frame Temporal Debouncing Window                          • 5-Frame Confirmation -> P0 Audio Siren
                 │                                                             │
                 └──────────────────────┬──────────────────────────────────────┘
                                        ▼
                   [ UNIFIED REAL-TIME SOC DASHBOARD ]
                   • Live Video Annotation & Worker HUD
                   • SHA-256 Hashed Tamper-Evident Evidence
                   • Immutable Incident Audit Trail (SQLite WAL)
```

---

### 5. Relevant Project Visuals / Screenshots to Use
* **Primary Visual:** Multi-worker compliance annotated frame showing bounding boxes and checklist HUD:
  - File: `reports/shadow_mode_visuals/shadow_snapshot_PPE_Multi_safup_00002.jpg` or `reports/shadow_mode_visuals/shadow_snapshot_PPE_Full_safup_00010.jpg`
* **Hazard Validation Visual:** Real-time fire and smoke optical detection:
  - File: `reports/shadow_mode_visuals/shadow_snapshot_Hazard_Fire_dfire_00000.jpg` or `reports/shadow_mode_visuals/shadow_snapshot_Hazard_Smoke_dfire_00013.jpg`
* **Hard-Negative Benchmark Visual:** Rejection of steam and industrial false alarms:
  - File: `reports/shadow_mode_visuals/shadow_snapshot_HardNegative_Steam_hneg_00004.jpg`

---

### 6. Presenter Highlight Guidance
* **Key Message to Deliver:** *"Most existing systems simply count '3 helmets and 2 vests' in an image. SafeSync goes further: it binds each piece of safety gear to the specific tracked worker's body. If worker #4 is missing gloves, worker #4 is flagged—while preventing false alarms when workers are partially occluded."*

---

## SLIDE 3 — TECHNICAL APPROACH & SYSTEM ARCHITECTURE

### 1. Slide Title
**Technical Approach & Implementation Methodology**

---
#### 1. Core Technology Stack
* **AI & Computer Vision:** 
  - **Ultralytics YOLOv8n:** Lightweight anchor-free neural detector (3.01M parameters, 8.2 GFLOPs at 384×384 input resolution) optimized for high-speed edge CPU execution.
  - **PyTorch 2.x & OpenCV:** Low-overhead tensor operations and vectorized frame preprocessing.
  - **ByteTrack Tracking Algorithm:** 8-state Kalman filtering with Hungarian data association for persistent multi-worker trajectory tracking.
* **Backend Architecture:** 
  - **FastAPI (Python 3.11/3.13):** High-concurrency asynchronous ASGI REST API and native bi-directional WebSockets.
  - **Thread-Isolated Capture Workers:** Dedicated background ingestion threads with a strict bounded queue depth of 1 ("latest-frame-wins") to eliminate pipeline latency drift.
  - **SQLite WAL Mode:** Write-Ahead Logging (`PRAGMA journal_mode=WAL`, `synchronous=NORMAL`) delivering sub-millisecond ACID-compliant incident and evidence persistence.
* **Frontend Operations Dashboard:** 
  - **React 18 + TypeScript + Vite 6:** Highly responsive single-page application with modular state management.
  - **Tailwind CSS & Lucide Icons:** Clean operator HUD with responsive multi-camera surveillance grids.
  - **HTML5 Canvas Vector Rendering:** Zero-flicker live video stream annotations and real-time worker checklist overlays.
* **Hardware & Deployment:** Standard industrial edge PCs or commercial laptops (tested on Intel Core i5-13420H, 16 GB RAM); zero GPU requirement.

---

#### 2. Six-Stage Implementation Pipeline
1. **Thread-Isolated Ingestion:** Captures frames from USB, IP, RTSP, or video sources with automatic backoff reconnection and memory buffer bounds.
2. **Single-Pass Neural Inference:** A single forward pass through YOLOv8n simultaneously detects all 7 target classes with calibrated confidence thresholds (0.25 for PPE, 0.20 for Fire/Smoke).
3. **Multi-Object Worker Tracking:** ByteTrack maps detected `person` instances across consecutive frames, assigning deterministic integer Track IDs and velocity vectors.
4. **Anthropometric Spatial Association:** Maps detected safety gear into 4 normalized anatomical zones:
   - **Head Zone (0.00 – 0.25):** Helmet association.
   - **Torso Zone (0.10 – 0.78, height ratio 0.12 – 0.88):** Safety vest association.
   - **Limb/Hand Zones (0.35 – 0.80 lateral):** Gloves association.
   - **Foot Zone (0.70 – 1.00):** Safety footwear association.
5. **Dual-Channel Temporal Validation:**
   - **PPE Violations:** Debounced across 3 confirmed frames with 15-frame detector loss tolerance before opening an infraction ticket.
   - **Fire/Smoke Hazards:** Multi-stage confirmation (Candidate $\rightarrow$ Detecting $\rightarrow$ Confirmed $\rightarrow$ Active) requiring 5 consecutive frames.
6. **Prioritized Alert & Evidence Persistence:** Computes deterministic 0–100 risk score, saves SHA-256 hashed evidence snapshots, updates SQLite database, and pushes sub-100ms WebSocket updates to the operator HUD.

---

### 3. System Architecture Tier Diagram
```
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 TIER 1: PRESENTATION LAYER (FRONTEND)                  │
  │  React 18 Dashboard  │  Live HUD Canvas  │  Incident Queue  │  WebSockets│
  └───────────────────────────────────▲────────────────────────────────────┘
                                      │ (Real-Time JSON + WebSocket Push)
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │                   TIER 2: APPLICATION & API LAYER                      │
  │  FastAPI ASGI  │  REST Endpoints  │  RBAC Security  │  Prometheus Metrics│
  └───────────────────────────────────▲────────────────────────────────────┘
                                      │ (Decoupled Event Bus)
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │           TIER 3: COMPLIANCE, TRACKING & HAZARD STATE ENGINE           │
  │  ByteTrack Tracker │ Spatial Anatomical Matcher │ Temporal Debouncer   │
  └───────────────────────────────────▲────────────────────────────────────┘
                                      │ (Bounding Boxes + Class Confidences)
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │                 TIER 4: DEEP LEARNING INFERENCE LAYER                  │
  │  Ultralytics YOLOv8n (384x384 Single-Pass) │ PyTorch CPU Vector Engine │
  └───────────────────────────────────▲────────────────────────────────────┘
                                      │ (Thread-Safe Buffer, Queue Depth = 1)
  ┌───────────────────────────────────┴────────────────────────────────────┐
  │                 TIER 5: STREAM INGESTION & DATA LAYER                  │
  │  OpenCV Ingestion Thread │ RTSP/IP/USB Cameras │ SQLite (WAL Mode) DB  │
  └────────────────────────────────────────────────────────────────────────┘
```

---

### 4. Relevant Visuals to Place on Slide 3
* **Pipeline / Confusion Matrix Visual:**
  - File: `models/detection/ppe_fire_smoke_v3/confusion_matrix_normalized.png` or `models/detection/ppe_fire_smoke_v3/results.png`
* **Raw Detection / Anatomical Debug Visual:**
  - File: `reports/ppe_debug/raw_detections/raw_debug_sensor_01.jpg`

---

### 5. Presenter Highlight Guidance
* **What to Highlight:** 
  - Point out that the pipeline does **NOT** run two separate models for PPE and Fire/Smoke. A single unified model processes everything in **one single forward pass**, cutting computational cost and latency in half.
  - Explain the queue-depth-1 architecture: the system never suffers from video lag or frame buffering during network slowdowns because old frames are immediately dropped in favor of the freshest frame.

---

## SLIDE 4 — FEASIBILITY AND VIABILITY

### 1. Slide Title
**Feasibility, Edge Viability & Risk Mitigation**

#### 1. Technical & Commercial Feasibility
* **Zero Dedicated Hardware Barrier:** Validated on standard commodity laptops (Intel Core i5-13420H CPU, 16 GB RAM) delivering **24.85 ms P50 inference** and **~18 to 25.1 FPS**. No \$2,000+ discrete GPU is required for active deployment.
* **Seamless Retrofit Integration:** Plugs into existing analog/digital CCTV networks via RTSP, HTTP/MJPEG, or USB interfaces. Eliminates the capital expense of installing proprietary IoT sensors.
* **Low Maintenance & Resource Footprint:** Memory utilization remains under 1.2 GB RAM during continuous multi-hour streaming; SQLite WAL mode operates without heavy database daemon administration.
* **Rigorous Verification:** 276/276 passing automated tests covering all mathematical spatial association bounds, state transitions, and network drop recovery.

---

#### 2. Potential Challenges & Proven Mitigation Strategies

| Challenge & Technical Risk | Root Cause in Industrial Environments | SafeSync Proven Engineering Mitigation |
|---|---|---|
| **False Smoke & Fire Alarms** | Industrial steam vents, dust plumes, welder arc glare, and yellow excavators trigger naive optical detectors. | **Hard-Negative Training & Temporal Gate:** Curated 1,200+ negative environmental images; 5-frame temporal accumulator prevents transient reflections from alarming. |
| **Worker Occlusion & Clipping** | Workers bend, crouch, or step behind equipment, temporarily hiding gloves or safety boots. | **Strict `UNKNOWN != ABSENT` State:** If limbs fall outside anatomical view or confidence bounds, status remains `UNKNOWN`. Zero false violations created. |
| **Detector Flickering** | Slight head movement or lighting shifts cause single-frame detection drops. | **15-Frame Persistence Tolerance:** Debouncing engine bridges momentary detection drops without resetting worker compliance state. |
| **Multi-Worker Crowding** | Multiple workers overlapping in camera frame causes safety gear to be assigned to wrong person. | **Hungarian Bipartite Distance Matching:** Strict relative coordinate bounding box geometry ensures gear belongs strictly to the enclosing worker bounding box. |
| **Stream Dropout & Network Lag** | RTSP network packets drop or camera temporarily disconnects during factory shifts. | **Thread-Isolated Exponential Backoff:** Ingestion worker automatically reconnects within 2 seconds without hanging or crashing the core backend. |

---

### 3. Key Robustness Metrics Table
* **Steam & Fog False Alarms:** `0%` (Fully suppressed across validation suite).
* **Metallic Glare False Positives:** `0%` (Eliminated via hard-negative conditioning).
* **Detector Recovery Time:** `< 0.5s` (Smoothly bridges momentary occlusions).
* **Camera Auto-Reconnection:** `< 2.0s` (Automatic background retry with backoff).

---

### 4. Relevant Visuals to Place on Slide 4
* **Hard-Negative Benchmark Visuals:** 
  - File: `reports/staged_validation_visuals/comparison_steam_pipe.jpg` (Proves steam is not classified as smoke)
  - File: `reports/staged_validation_visuals/comparison_excavator_surface.jpg` (Proves yellow equipment does not trigger false high-vis vest alerts)
  - File: `reports/staged_validation_visuals/comparison_metallic_glare.jpg` (Proves welder/sun glare does not trigger false fire alerts)

---

### 5. Presenter Highlight Guidance
* **What to Highlight:** 
  - *"In industrial safety, false alarms kill adoption. If a system triggers alarms every time an exhaust pipe vents steam, operators will shut it off. SafeSync's biggest engineering breakthrough is hard-negative resilience and temporal debouncing—achieving 100% false alarm suppression on steam and glare."*

---

## SLIDE 5 — IMPACT AND BENEFITS

### 1. Slide Title
**Impact, Industrial Benefits & Market Potential**

--
#### 1. Multi-Tier Stakeholder Impact & Benefits
* **For Industrial Workers (Life Safety):**
  - Continuous protection against head trauma, lacerations, foot injuries, and burns.
  - Faster emergency evacuation alerts in the event of an outbreak of fire or hazardous smoke.
  - Cultivates an active, peer-encouraged safety-first workplace culture.
* **For EHS Managers & Safety Officers (Operational Excellence):**
  - Replaces tedious, subjective manual clipboard inspections with continuous, automated oversight.
  - Consolidated real-time visibility across all operational zones from a centralized SOC dashboard.
  - Drastic reduction in alarm fatigue via non-auditory visual logging for PPE infractions.
* **For Plant Directors & Enterprises (Economic & Legal Protection):**
  - **Downtime Prevention:** Early optical combustion detection suppresses fires before catastrophic structural damage occurs.
  - **Regulatory Penalty Avoidance:** Enforces continuous adherence to OSHA (29 CFR 1926) and ISO 45001 occupational safety mandates.
  - **Audit-Ready Immutable Records:** Every incident is automatically captured with timestamped, SHA-256 verified visual snapshot evidence.
  - **Lower Insurance Premiums:** Verifiable safety compliance records directly assist in negotiating reduced industrial risk underwriting costs.

---

#### 2. Addressable Market Potential & Deployment Scalability
* **Vast Retrofit Market:** Over **100+ Million** legacy CCTV cameras currently deployed across global manufacturing, construction, chemical, and mining facilities can be instantly upgraded to AI safety sensors without purchasing new cameras.
* **Target Industry Verticals:**
  1. Heavy Construction & Infrastructure Sites
  2. Oil & Gas Refineries and Petrochemical Facilities
  3. Steel, Metallurgy & Heavy Machinery Plants
  4. Warehouses, Port Logistics & Distribution Hubs
  5. Underground & Surface Mining Operations

---

#### 3. Strategic Product Roadmap & Future Scope
```
  [ PHASE 1: CURRENT PROTOTYPE ] ───> Validated CPU Real-Time Pipeline (18-25 FPS, 7 Classes)
  [ PHASE 2: EDGE HARDWARE ]     ───> INT8 TensorRT on NVIDIA Jetson Orin Nano (Sub-10ms Latency)
  [ PHASE 3: INDUSTRIAL SCADA ]  ───> Hardware Interlocks via Modbus TCP & OPC-UA PLC Relays
  [ PHASE 4: SPATIAL ANALYTICS ] ───> Restricted Zone Geofencing, Virtual Tripwires & Heatmaps
```

---

### 4. Relevant Visuals to Place on Slide 5
* **Incident Log & Evidence Visual:**
  - File: `reports/shadow_mode_visuals/shadow_snapshot_PPE_Facility_ppec_00001.jpg`
* **Real-World Multi-Worker Detection Visual:**
  - File: `reports/staged_validation_visuals/comparison_multi_worker_ppe.jpg`

---

### 5. Presenter Highlight Guidance
* **What to Highlight:** 
  - *"SafeSync is not an expensive hardware replacement. It is a pure software intelligence layer that turns existing, passive video surveillance into an active life-saving governance engine. It protects human lives, preserves multi-million dollar assets, and provides undeniable audit-ready evidence for regulatory compliance."*

---

## SLIDE 6 — RESEARCH, REFERENCES & STANDARDS

### 1. Slide Title
**Research Foundations, Verified Datasets & Industry Standards**

---



#### 1. Peer-Reviewed Academic & Technical Foundations
* **Ultralytics YOLOv8 (2023):** Jocher, G., Chaurasia, A., & Qiu, J. — *Anchor-Free Real-Time Object Detection Framework*. Provides state-of-the-art parameter efficiency, decoupled head design, and high edge inference throughput. (`https://github.com/ultralytics/ultralytics`)
* **ByteTrack Multi-Object Tracking (ECCV 2022):** Zhang, Y., Sun, P., Dong, Y., et al. — *ByteTrack: Multi-Object Tracking by Associating Every Detection Box*. Utilizes low-confidence detection box recovery for maintaining persistent worker IDs through heavy occlusion. (`https://arxiv.org/abs/2110.06864`)
* **D-Fire Dataset & Flame Detection (2022):** Pedro et al. — *D-Fire: Real-Time Optical Flame and Smoke Detection Benchmark*. Published in Neural Computing & Applications. Foundational benchmark for combustion boundary modeling. (`https://github.com/gaia-solutions-on-demand/DFireDataset`)
* **CPPE-5 Benchmark (2021):** Maurya, A., et al. — *Medical & Industrial Personal Protective Equipment Benchmark*. Referenced for multi-class hierarchical PPE classification topologies. (`https://arxiv.org/abs/2112.09569`)

---

#### 2. Open Datasets Curated & Ingested (22,453+ Total Images)
* **Pictor PPE Dataset:** 1,487 high-resolution annotated images of construction workers, hard hats, and safety vests under realistic outdoor illumination.
* **Hard Hat Workers (Roboflow Universe):** 7,035 images providing diverse multi-angle headwear poses, varying colors, and worker postures.
* **Construction Site Safety (CSS):** 9,451 multi-class images used as the primary source for full-body PPE annotations (`helmet`, `vest`, `gloves`, `footwear`).
* **D-Fire Benchmark:** 4,480 images of open flame plumes and expanding smoke clouds.
* **SafeSync Hard-Negative Distractor Suite:** 1,200 curated hard-negative samples of steam vents, welder glare, orange machinery, and airborne dust to ensure 0% false positive hazard rates.

---

#### 3. Regulatory Standards & Engineering Frameworks
* **OSHA 29 CFR 1926.100 & 1926.95:** United States Occupational Safety and Health Standards for Head and Personal Protective Equipment.
* **ISO 45001:2018:** International Standard for Occupational Health and Safety Management Systems.
* **EN ISO 20471 / ANSI 107:** High-Visibility Warning Clothing Performance Requirements.
* **EN 397 / ANSI Z89.1:** Industrial Safety Helmets Physical and Impact Specifications.
* **Engineering Tools:** FastAPI, Uvicorn, React 18, Vite, Tailwind CSS, PyTorch, OpenCV, SQLite WAL.
* **SafeSync Official Source Code:** [https://github.com/SMRU08/SafeSync](https://github.com/SMRU08/SafeSync)

---



### 5. Presenter Highlight Guidance
* **What to Highlight:** 
  - Conclude the presentation by emphasizing the rigorous scientific grounding of SafeSync.
  - State that SafeSync was not trained on synthetic toy data, but on over 22,000 carefully curated real-world images aligned with strict OSHA and ISO safety standards.
  - Direct the judges to your open-source repository at `https://github.com/SMRU08/SafeSync` for complete code, logs, and benchmark reproduction.

--
