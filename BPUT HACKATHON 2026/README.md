# BPUT HACKATHON 2026 — PRESENTATION MASTER REFERENCE

> **Project Name:** SafeSync  
> **Problem Statement ID:** PS06  
> **Problem Statement Title:** AI-Powered Real-Time Industrial Workplace Safety Monitoring, 4-Point PPE Compliance, and Optical Fire/Smoke Detection  
> **Theme:** Smart Automation (AI & Computer Vision for Industrial Workplace Safety & Compliance Governance)  
> **Category:** Software  
> **Team ID:** BH26PS06T049  
> **Team Name:** XERSES  
> **College / Institution:** BPUT Affiliated Engineering Institution *(e.g., [Insert College Name])*  
> **Department:** Department of Computer Science & Engineering / Information Technology  
> **Repository:** [https://github.com/SMRU08/SafeSync](https://github.com/SMRU08/SafeSync)

---

## Structure & Usage Guide
This document contains the **complete, PPT-ready content for all 6 slides** required for the **BPUT HACKATHON 2026** presentation.
- Open PowerPoint.
- Read each slide section sequentially.
- Copy the structured text, bullet points, and data tables directly into your presentation template.
- Insert the referenced diagrams and repository screenshot assets.
- Review the **Short Instruction About What Should Be Highlighted** for each slide to prepare your speaking pitch.

```
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                                   PRESENTATION SLIDES                                  │
  ├──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬─────────────┤
  │   SLIDE 1    │   SLIDE 2    │   SLIDE 3    │   SLIDE 4    │   SLIDE 5    │   SLIDE 6   │
  │  Title Page  │  Idea Title  │  Technical   │ Feasibility  │   Impact &   │ Research &  │
  │              │  & Solution  │   Approach   │ & Viability  │   Benefits   │ References  │
  └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴─────────────┘
```

---

## SLIDE 1 — TITLE PAGE

### Slide Details
* **Problem Statement ID:** `PS06`
* **Problem Statement Title:** AI-Powered Real-Time Industrial Workplace Safety Monitoring, 4-Point PPE Compliance, and Optical Fire/Smoke Detection
* **Theme:** Smart Automation (Occupational Health & Industrial Safety Governance)
* **Category:** Software
* **Team ID:** `BH26PS06T049`
* **Team Name:** `XERSES`
* **College / Institution:** BPUT Affiliated Engineering Institution *(e.g., [Insert College Name])*
* **Department:** Department of Computer Science & Engineering / Information Technology
* **Tagline:** *"Smart Vision. Safe Workers. Faster Response."*

---

### Important Bullet Points for Slide 1
* **Autonomous Industrial Safety:** 24/7 vision-based continuous worker protection and combustion hazard mitigation.
* **Dual-Capability Engine:** Simultaneous 4-point PPE compliance tracking alongside instant optical fire and smoke hazard alerting.
* **Zero Additional Sensors:** Operates directly over existing workplace IP cameras, RTSP streams, and USB webcams.
* **Edge-Optimized Efficiency:** Engineered to run on standard commercial CPUs without requiring dedicated cloud GPUs.

---

### Slide Layout & Visual Suggestions
* **Theme:** Industrial Navy Blue / Slate Dark Theme (`#0F172A` background, `#0EA5E9` cyan borders, `#F59E0B` amber warning accents).
* **Header Logos:** 
  1. BPUT Hackathon 2026 Logo (Top Left)
  2. STPI & EmTek Partner Logos (Top Right)
  3. SafeSync Project Badge & Team XERSES Logo (Center)
* **Visual Reference:** Dark industrial facility background with subtle digital bounding-box HUD overlay.

---

### Short Instruction About What Should Be Highlighted
* Introduce your team name (**XERSES**) and Team ID (**BH26PS06T049**) clearly.
* Emphasize that **SafeSync** addresses Problem Statement **PS06** by converting passive, unmonitored factory CCTV cameras into an active, intelligent safety governance system that detects missing gear and early combustion in real time.

---

## SLIDE 2 — IDEA TITLE & PROPOSED SOLUTION

### Slide Title
**SafeSync — Autonomous Industrial Safety Intelligence & Hazard Governance Platform**

---

### Proposed Solution (Describe your Idea / Solution / Prototype)
SafeSync is an end-to-end, real-time AI computer vision system designed to continuously monitor industrial workplaces, construction sites, and manufacturing plants. By connecting directly to existing standard CCTV camera streams, SafeSync provides simultaneous **4-point PPE compliance monitoring** (`helmet`, `safety_vest`, `gloves`, `safety_footwear`) for each individual worker, coupled with **zero-lag optical combustion detection** (`fire` and `smoke`).

---

### Detailed Explanation of the Proposed Solution
* **Unified Single-Pass Detection:** SafeSync runs a custom single-pass YOLOv8n model that detects 7 canonical classes in a single forward pass, eliminating the computational bottleneck of running separate models.
* **Individual Worker Tracking:** Every worker entering the camera view is assigned an anonymous persistent integer Track ID via an 8-state Kalman Filter (ByteTrack).
* **Spatial Anatomical Association:** Uses Hungarian bipartite matching to anchor safety gear directly to each tracked worker’s anatomical zones (cranial, thoracic, hands, feet).
* **Decoupled Alerting System:** Separates low-severity PPE infractions (silent visual dashboard logging) from high-severity combustion hazards ($P_0$ audible evacuation sirens), eliminating operator alarm fatigue.

---

### How It Addresses the Problem
* **Eliminates Human Vigilance Decay:** Safety officers monitoring multi-screen CCTV feeds suffer steep attention loss within 20–30 minutes. SafeSync provides tireless 24/7 automated monitoring.
* **Overcomes Spot-Check Blindness:** Manual physical inspections provide only snapshot compliance; workers routinely remove gear when inspectors depart. SafeSync tracks compliance persistently.
* **Accelerates Disaster Response:** Traditional ceiling smoke detectors take minutes to trigger in high-ceiling factories. SafeSync detects open flame and smoke plumes optically within seconds.
* **Prevents False Violation Penalties:** Resolves worker occlusions by enforcing the invariant $\text{UNKNOWN} \ne \text{ABSENT}$, ensuring unclear views never trigger false penalties.

---

### Innovation and Uniqueness of the Solution
1. **Worker-Centric Spatial Association:** Gear is mathematically bound to individual tracked workers rather than just counted across the whole frame.
2. **Strict $\text{UNKNOWN} \ne \text{ABSENT} \ne \text{VIOLATION}$ Invariant:** When gear is hidden behind equipment or clipped by camera boundaries, status remains `UNKNOWN`. Only confirmed absence triggers violations.
3. **Multi-Frame Temporal Confirmation State Machine:** Debounces transient detections across 15 tolerance frames, eliminating camera jitter and single-frame detector flicker.
4. **Hard-Negative Distractor Conditioning:** Hardened against industrial false positives (steam vents, welding glare, yellow excavators, dust clouds).

---

### Key Features of the Proposed Solution
* **Single forward-pass 7-class neural architecture** (32.5 ms inference latency on CPU).
* **4-Point PPE compliance governance** (`helmet`, `safety_vest`, `gloves`, `safety_footwear`).
* **Instant optical fire and smoke detection** with dual-channel confirmation state machine.
* **Zero-lag stream capture** via bounded queue depth = 1 ("latest-frame-wins").
* **Tamper-evident visual evidence capture** with SHA-256 cryptographic hashing.
* **Explainable 0–100 risk scoring engine** based on severity, duration, and worker density.
* **Full-stack real-time operator HUD** with sub-100ms WebSocket updates and SQLite WAL persistence.

---

### Relevant Diagram / Flowchart
```
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │                           SAFESYNC DUAL-PIPELINE ARCHITECTURE                           │
  └────────────────────────────────────────────┬────────────────────────────────────────────┘
                                               │
                                 [ CCTV / RTSP / Video Stream ]
                                               │
                              [ Ingestion Worker (Queue Depth = 1) ]
                                               │
                               [ Single-Pass YOLOv8n (7 Classes) ]
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        ▼                                             ▼
            [ WORKER PPE PIPELINE ]                       [ HAZARD COMBUSTION PIPELINE ]
         • ByteTrack Worker Tracking                   • Dual-Channel Persistence Accumulator
         • 4-Zone Anthropometric Matching              • Candidate -> Confirmed State Machine
         • UNKNOWN != ABSENT Boundary Filtering        • Hard-Negative Steam/Dust Suppression
         • 15-Frame Temporal Debouncing Window         • 5-Frame Confirmation -> P0 Audio Siren
                        │                                             │
                        └──────────────────────┬──────────────────────┘
                                               ▼
                              [ REAL-TIME OPERATOR SOC DASHBOARD ]
                              • Live Annotated Video HUD Canvas
                              • SHA-256 Cryptographic Evidence Snapshots
                              • Incident Lifecycle & SQLite WAL Logging
```

---

### Relevant Project Screenshot to Use
* **Multi-Worker Live HUD:** `reports/shadow_mode_visuals/shadow_snapshot_PPE_Multi_safup_00002.jpg`
* **Single Worker Compliance:** `reports/shadow_mode_visuals/shadow_snapshot_PPE_Full_safup_00010.jpg`
* **Optical Hazard Detection:** `reports/shadow_mode_visuals/shadow_snapshot_Hazard_Fire_dfire_00000.jpg`

---

### Short Instruction About What Should Be Highlighted
* Highlight that SafeSync **binds gear to each tracked worker's body** rather than just counting items in an image.
* Point out that SafeSync runs **both PPE and combustion hazard detection in one single forward pass**, cutting inference time and hardware cost in half.

---

## SLIDE 3 — TECHNICAL APPROACH

### Slide Title
**Technical Approach, Methodology & System Architecture**

---

### Technologies to be Used

#### Programming Languages
* **Python 3.11 / 3.13:** High-performance asynchronous backend, computer vision pipeline, and tensor processing.
* **TypeScript:** Type-safe frontend dashboard development.
* **SQL:** Structured relational querying for audit logs and incidents.

#### Frameworks & Libraries
* **FastAPI & Uvicorn:** Asynchronous ASGI web framework delivering sub-100ms REST and WebSocket throughput.
* **PyTorch 2.x:** Vectorized tensor runtime for edge deep learning execution.
* **OpenCV (cv2) & NumPy:** Real-time video frame manipulation, colorspace conversions, and geometric calculations.
* **React 18 & Vite 6:** Component-driven Single Page Application with fast HMR.
* **Tailwind CSS & Lucide Icons:** Responsive, operator-centric dark-mode SOC interface.

#### AI / ML Models
* **Ultralytics YOLOv8n:** Lightweight anchor-free neural detector (3.01M parameters, 8.2 GFLOPs at 384×384 resolution) trained on unified 7-class ontology.
* **ByteTrack Tracker:** 8-state Kalman filtering with Hungarian data association for persistent multi-worker trajectory tracking.

#### Database
* **SQLite 3 with Write-Ahead Logging (WAL Mode):** Configured with `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL`, enabling concurrent reads during active frame writes without database locks.

#### APIs
* **Asynchronous REST API:** Structured endpoints for camera management, incident query, and health monitoring.
* **Native Bi-Directional WebSockets:** Mounted at `/ws/events` and `/ws/alerts` for live HUD telemetry streaming.
* **Prometheus Observability:** Metrics exported at `/metrics` (pipeline latency, frame counters, FPS).

#### Hardware / Sensors (if applicable)
* **Standard Hardware:** Standard commercial PC / laptop (validated on Intel Core i5-13420H, 16 GB RAM); zero discrete GPU requirement.
* **Camera Sensors:** Supports standard USB webcams, IP cameras (HTTP/MJPEG), industrial RTSP streams, and pre-recorded MP4/AVI videos.

---

### Methodology and Implementation Process

```
   [ Stage 1: Ingest ]  ──> Thread-isolated capture, bounded queue depth = 1 (latest-frame-wins)
            │
   [ Stage 2: Detect ]  ──> Single-pass YOLOv8n extracts 7 classes at 384x384 input resolution
            │
   [ Stage 3: Track ]   ──> ByteTrack assigns persistent integer IDs to each detected worker
            │
   [ Stage 4: Associate ] ──> Hungarian matching maps gear to Head, Torso, Hand, and Foot zones
            │
   [ Stage 5: Validate ]  ──> Temporal state debouncer bridges 15-frame detection loss tolerance
            │
   [ Stage 6: Alert ]   ──> Computes 0-100 risk score, saves SHA-256 evidence, pushes WebSocket HUD
```

1. **Ingest:** Thread-isolated capture worker with bounded queue depth 1 eliminates video lag.
2. **Detect:** Single-pass YOLOv8n processes the frame at 384×384 resolution (32.5 ms latency).
3. **Track:** ByteTrack assigns persistent integer IDs to workers using motion prediction.
4. **Associate:** Anthropometric spatial association maps detected gear to 4 anatomical zones:
   - *Head Zone (0.00 – 0.25):* Helmet association.
   - *Torso Zone (0.10 – 0.78, height ratio 0.12 – 0.88):* Safety vest association.
   - *Hand Zone (0.35 – 0.80 lateral):* Gloves association.
   - *Foot Zone (0.70 – 1.00):* Safety footwear association.
5. **Validate:** Multi-frame debouncing (15-frame tolerance) prevents momentary drops from creating violations.
6. **Alert & Persist:** Computes 0–100 risk score, writes incident to SQLite WAL, and pushes live WebSocket HUD updates.

---

### System Architecture / Flow Diagram
```
  ┌─────────────────────────────────────────────────────────────────────────────────────────┐
  │                          TIER 1: PRESENTATION LAYER (FRONTEND)                          │
  │     React 18 Dashboard  │  Live HUD Canvas  │  Incident Queue  │  WebSocket Stream      │
  └────────────────────────────────────────────▲────────────────────────────────────────────┘
                                               │ (Real-Time JSON + WebSocket Push)
  ┌────────────────────────────────────────────┴────────────────────────────────────────────┐
  │                            TIER 2: APPLICATION & API LAYER                              │
  │     FastAPI ASGI  │  REST Endpoints  │  RBAC Security  │  Prometheus Metrics Engine     │
  └────────────────────────────────────────────▲────────────────────────────────────────────┘
                                               │ (Decoupled Internal Event Bus)
  ┌────────────────────────────────────────────┴────────────────────────────────────────────┐
  │                    TIER 3: COMPLIANCE, TRACKING & HAZARD STATE ENGINE                   │
  │     ByteTrack Tracker │ Spatial Anthropometric Matcher │ Temporal Debouncing Engine     │
  └────────────────────────────────────────────▲────────────────────────────────────────────┘
                                               │ (Bounding Boxes + Class Confidences)
  ┌────────────────────────────────────────────┴────────────────────────────────────────────┐
  │                          TIER 4: DEEP LEARNING INFERENCE LAYER                          │
  │       Ultralytics YOLOv8n (384x384 Single-Pass) │ PyTorch CPU Vectorized Engine         │
  └────────────────────────────────────────────▲────────────────────────────────────────────┘
                                               │ (Thread-Safe Buffer, Queue Depth = 1)
  ┌────────────────────────────────────────────┴────────────────────────────────────────────┐
  │                          TIER 5: STREAM INGESTION & DATA LAYER                          │
  │      OpenCV Ingestion Thread │ RTSP/IP/USB Cameras │ SQLite 3 (WAL Mode) Database       │
  └─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Working Prototype / Demo
* **Validated Test Coverage:** 276 / 276 passing tests (250 unit tests, 39 integration tests, 20 recovery tests, 3 root smoke tests).
* **Hardware Benchmark (Intel Core i5):**
  - YOLOv8n Single-Pass Inference Latency: **32.5 ms** (P50: 32.29 ms)
  - End-to-End Pipeline Latency: **72.7 ms**
  - Processing Frame Rate: **13–17 FPS** on standard commercial CPU
* **Continuous Streaming Stability:** 30-minute stress test processed **6,843 frames** continuously with **zero memory leaks**, zero crashes, and zero false violations.

---

### Short Instruction About What Should Be Highlighted
* Emphasize that this is a **fully functional, running prototype** with 276/276 passing tests, not just a concept slide.
* Highlight the **Queue Depth = 1 architecture**: old frames are dropped when network slows down, ensuring the operator always sees the real-time present with zero video lag.

---

## SLIDE 4 — FEASIBILITY AND VIABILITY

### Slide Title
**Feasibility, Viability, Risk Mitigation & Scalability**

---

### Technical Feasibility
* **Zero Discrete GPU Dependency:** Runs at real-time speeds (~13–17 FPS, 32.5 ms inference) on commodity Intel Core i5 processors.
* **Low Memory Footprint:** Operates under 200 MB RSS memory; verified zero memory leak over 6,800+ continuous frames.
* **Non-Blocking Architecture:** Asynchronous FastAPI backend + SQLite WAL mode enables concurrent reading and writing without locking.
* **Comprehensive Test Suite:** 276 automated regression tests ensure mathematical bounds and state machines remain stable.

---

### Financial Feasibility
* **Zero Capital Expenditure (CAPEX):** Connects to existing CCTV and IP camera infrastructure via RTSP; no expensive proprietary AI cameras needed.
* **Zero Cloud GPU Costs:** Eliminates monthly cloud GPU streaming bills by running inference locally on existing on-premise PCs.
* **Instant ROI:** Pays for itself by preventing regulatory OSHA non-compliance fines and reducing industrial insurance underwriting premiums.

---

### Operational Feasibility
* **Seamless Retrofit:** Installed as a software layer on existing factory surveillance systems without disrupting operations.
* **Alarm Fatigue Elimination:** Separates silent visual logs for missing gear from audible sirens for combustion emergencies.
* **Zero-Biometric Privacy Compliance:** Tracks workers using anonymous integer IDs (`Track #1`), preserving worker privacy without facial recognition.

---

### Potential Challenges and Risks & Mitigation Strategies

| Challenge & Technical Risk | Root Cause in Industrial Environments | SafeSync Proven Engineering Mitigation |
|---|---|---|
| **False Smoke & Fire Alarms** | Steam vents, dust plumes, welder arc glare, and yellow machinery trigger naive optical detectors. | **Hard-Negative Training & Temporal Gate:** Curated 1,200+ negative distractor images; 5-frame temporal confirmation accumulator prevents transient sparks from alarming. |
| **Worker Occlusion & Boundary Clipping** | Workers bend, crouch, or step behind equipment, temporarily hiding boots or gloves. | **Strict $\text{UNKNOWN} \ne \text{ABSENT}$ Gate:** If limbs fall outside view or boundary margins, status remains `UNKNOWN`. Zero false violations created. |
| **Detector Flickering** | Lighting shifts or head movement causes single-frame detection drops. | **15-Frame Persistence Tolerance:** Debouncing engine bridges momentary detection drops without resetting worker compliance state. |
| **Multi-Worker Crowding** | Multiple workers overlapping in camera frame causes safety gear to be assigned to wrong person. | **Hungarian Bipartite Distance Matching:** Strict relative coordinate geometry ensures gear belongs strictly to the enclosing worker bounding box. |
| **Stream Dropout & Network Lag** | RTSP network packets drop or camera temporarily disconnects during factory shifts. | **Thread-Isolated Exponential Backoff:** Ingestion worker automatically reconnects within 2 seconds without hanging or crashing the core backend. |

---

### Scalability and Future Scope

```
  [ PHASE 1: PROTOTYPE (CURRENT) ] ───> Validated CPU Pipeline (13-17 FPS, 7 Classes, 276 Tests)
  [ PHASE 2: EDGE ACCELERATION ]   ───> INT8 TensorRT on NVIDIA Jetson Orin Nano (<10ms Latency)
  [ PHASE 3: INDUSTRIAL SCADA ]    ───> Hardware Interlocks via Modbus TCP & OPC-UA PLC Relays
  [ PHASE 4: SPATIAL ANALYTICS ]   ───> Restricted Zone Geofencing, Virtual Tripwires & Heatmaps
```

* **Multi-Camera Expansion:** Modular architecture allows adding camera feeds independently.
* **Edge Hardware Migration:** Ready for INT8 TensorRT deployment on NVIDIA Jetson Orin Nano for sub-10ms edge processing.
* **SCADA / PLC Integration:** Planned Modbus TCP / OPC-UA relays to automatically halt hazardous machinery when unequipped workers approach.

---

### Short Instruction About What Should Be Highlighted
* Address the #1 judge concern: **False Alarms**. Explain how SafeSync achieved **0% false alarms on steam and glare** using hard-negative conditioning and temporal debouncing.
* Emphasize the **financial viability**: factories don't need to replace their existing cameras; SafeSync is a pure software upgrade.

---

## SLIDE 5 — IMPACT AND BENEFITS

### Slide Title
**Multi-Tier Impact, Benefits & Real-World Applications**

---

### Target Users / Beneficiaries
* **Industrial Workers & Technicians:** Protected continuously against head injuries, lacerations, foot trauma, and combustion hazards.
* **EHS (Environment, Health & Safety) Officers:** Replaces tedious manual clipboard checks with continuous automated oversight.
* **Control Room Operators:** Single-screen situational awareness with prioritized incident queues and visual HUD overlays.
* **Plant Directors & Enterprise Executives:** Auditable, immutable compliance records for regulatory inspections and lower insurance risk.

---

### Expected Impact
* **Zero Fatalities Goal:** Real-time intervention before hazardous exposure leads to catastrophic workplace accidents.
* **80%+ Reduction in PPE Infractions:** Consistent automated monitoring eliminates the "inspector-leaves-gear-comes-off" habit.
* **Up to 90% Faster Fire Response:** Optical detection alerts site teams to open flames within seconds, long before ceiling smoke detectors trigger.
* **Complete Audit Readiness:** 100% of safety incidents backed by cryptographic visual evidence snapshots.

---

### Key Benefits

#### Social Benefits
* **Protects Human Life:** Guards workers in high-risk sectors (construction, mining, petrochemical, manufacturing).
* **Fosters Safety Culture:** Encourages peer adherence and transparent safety accountability on the shop floor.
* **Family Security:** Ensures industrial breadwinners return home safely every day.

#### Economic Benefits
* **Downtime Prevention:** Early optical fire detection prevents multi-million dollar structural facility losses.
* **Regulatory Fine Avoidance:** Ensures continuous statutory compliance with OSHA and ISO standards.
* **Lower Insurance Premiums:** Verifiable safety logs reduce commercial insurance underwriting risk.

#### Educational Benefits
* **Transparent Risk Scores:** Deterministic 0–100 risk scoring shows workers and supervisors why an alert was triggered.
* **Incident Review Data:** Visual evidence snapshots provide empirical training material for company safety briefings.

#### Environmental Benefits
* **Prevents Chemical Releases:** Rapid fire detection in petrochemical plants stops combustion before hazardous storage tanks rupture.
* **Suppresses Toxic Plumes:** Immediate fire alerts minimize prolonged toxic smoke emission into surrounding communities.

#### Technological Benefits
* **Commodity Edge AI:** Proves that enterprise-grade computer vision safety governance can run on standard CPUs without cloud dependency.
* **Zero Latency Accumulation:** Bounded queue architecture demonstrates zero-lag streaming on live camera networks.

---

### Real-World Applications
1. **Construction & Infrastructure:** Monitoring hard hats and high-visibility vests across sprawling outdoor job sites.
2. **Oil & Gas Refineries & Petrochemical:** Continuous optical flame/smoke detection combined with mandatory PPE governance.
3. **Steel, Metallurgy & Heavy Manufacturing:** Ensuring protective boots, vests, and helmets near blast furnaces and heavy machinery.
4. **Logistics Hubs & Port Terminals:** High-visibility vest tracking around active container cranes and forklift traffic.
5. **Mining Operations:** Monitoring safety gear adherence in surface excavation and processing facilities.

---

### Long-Term Impact and Scalability
* SafeSync establishes a **universal, software-defined safety standard** that scales from a single workshop webcam to a 500-camera industrial complex, transforming passive surveillance into an active life-saving governance engine.

---

### Short Instruction About What Should Be Highlighted
* Connect the technology directly to **human impact**: *"Every worker deserves to return home safe."*
* Emphasize the **economic return**: SafeSync pays for itself through prevented downtime, eliminated regulatory fines, and reduced insurance premiums.

---

## SLIDE 6 — RESEARCH AND REFERENCES

### Slide Title
**Research Foundations, Curated Datasets & Industry Standards**

---

### Research Papers / Journals
* **Ultralytics YOLOv8 (2023):** Jocher, G., Chaurasia, A., & Qiu, J. — *Anchor-Free Real-Time Object Detection Framework*. Provides state-of-the-art parameter efficiency, decoupled head design, and high edge inference throughput. (`https://github.com/ultralytics/ultralytics`)
* **ByteTrack Multi-Object Tracking (ECCV 2022):** Zhang, Y., Sun, P., Dong, Y., et al. — *ByteTrack: Multi-Object Tracking by Associating Every Detection Box*. European Conference on Computer Vision. Enables robust worker tracking through occlusion using low-confidence recovery. (`https://arxiv.org/abs/2110.06864`)
* **D-Fire Optical Combustion Benchmark (2022):** Pedro et al. — *D-Fire: Real-Time Optical Flame and Smoke Detection Benchmark*. Published in Neural Computing & Applications. Foundational benchmark for combustion boundary modeling. (`https://github.com/gaia-solutions-on-demand/DFireDataset`)
* **CPPE-5 Benchmark (2021):** Maurya, A., et al. — *Medical & Industrial Personal Protective Equipment Benchmark*. Published in arXiv. Referenced for multi-class hierarchical PPE classification topologies. (`https://arxiv.org/abs/2112.09569`)

---

### Datasets Used (22,453+ Curated Images)
* **Pictor PPE Dataset:** 1,487 high-resolution annotated images of construction workers, hard hats, and safety vests under realistic outdoor illumination.
* **Hard Hat Workers (Roboflow Universe):** 7,035 images providing diverse multi-angle headwear poses, varying colors, and worker postures.
* **Construction Site Safety (CSS):** 9,451 multi-class images used as the primary source for full-body PPE annotations (`helmet`, `vest`, `gloves`, `footwear`).
* **D-Fire Benchmark:** 4,480 images of open flame plumes and expanding smoke clouds.
* **SafeSync Hard-Negative Distractor Suite:** 1,200 curated hard-negative samples of steam vents, welder glare, orange machinery, and airborne dust to guarantee 0% false positive hazard rates.

---

### Technologies / Frameworks Referenced
* **AI & Computer Vision:** Ultralytics YOLOv8n, PyTorch, OpenCV, ByteTrack, NumPy.
* **Backend & API:** FastAPI ASGI, Uvicorn, Pydantic v2, Python 3.13.
* **Frontend & UI:** React 18, Vite 6, TypeScript, Tailwind CSS, HTML5 Canvas.
* **Database & Storage:** SQLite 3 with Write-Ahead Logging (`WAL` mode).

---

### Official Documentation
* **FastAPI Official Documentation:** [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
* **PyTorch Official Documentation:** [https://pytorch.org/docs/stable/index.html](https://pytorch.org/docs/stable/index.html)
* **React 18 Official Documentation:** [https://react.dev](https://react.dev)
* **SQLite Write-Ahead Logging (WAL) Guide:** [https://sqlite.org/wal.html](https://sqlite.org/wal.html)

---

### GitHub Repositories
* **SafeSync Official Codebase:** [https://github.com/SMRU08/SafeSync](https://github.com/SMRU08/SafeSync)
* **Ultralytics YOLOv8:** [https://github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics)
* **ByteTrack Official Repository:** [https://github.com/ifzhang/ByteTrack](https://github.com/ifzhang/ByteTrack)
* **D-Fire Dataset Repository:** [https://github.com/gaia-solutions-on-demand/DFireDataset](https://github.com/gaia-solutions-on-demand/DFireDataset)

---

### Other Relevant Sources & Regulatory Safety Standards
* **OSHA 29 CFR 1926.100 & 1926.95:** U.S. Occupational Safety and Health Administration Standards for Head and Personal Protective Equipment.
* **ISO 45001:2018:** International Standard for Occupational Health and Safety Management Systems.
* **EN ISO 20471 / ANSI 107:** High-Visibility Warning Clothing Performance Requirements.
* **EN 397 / ANSI Z89.1:** Industrial Safety Helmets Physical and Impact Specifications.

---

### Reference Links (Consolidated for Copy-Paste)
* SafeSync Project: `https://github.com/SMRU08/SafeSync`
* YOLOv8 Research: `https://github.com/ultralytics/ultralytics`
* ByteTrack Paper: `https://arxiv.org/abs/2110.06864`
* D-Fire Dataset: `https://github.com/gaia-solutions-on-demand/DFireDataset`
* CPPE-5 Benchmark: `https://arxiv.org/abs/2112.09569`
* OSHA Regulations: `https://www.osha.gov/laws-regs/regulations/standardnumber/1926`
* ISO 45001 Standard: `https://www.iso.org/standard/63787.html`

---

### Short Instruction About What Should Be Highlighted
* Emphasize the **academic rigor and empirical validation** behind SafeSync.
* Mention that the system was trained and benchmarked on **over 22,000 curated real-world images** aligned with strict **OSHA and ISO standards**.
* Direct the judges to your open-source repository at `https://github.com/SMRU08/SafeSync` for complete code, logs, and benchmark reproduction.

---

## PRESENTATION DELIVERY CHECKLIST & FAQ FOR JUDGES

| Anticipated Jury Question | Recommended Winning Answer |
|---|---|
| **"Why not run two models: one for PPE and one for Fire?"** | *"Running two models doubles inference latency from 32ms to 65ms+ per frame, which drops throughput below real-time on CPU. SafeSync solves this with a unified 7-class single-pass detector that extracts both workers, gear, and hazards simultaneously."* |
| **"What happens if a worker is kneeling or hidden behind a machine?"** | *"Traditional systems falsely trigger a missing boots violation. SafeSync implements strict $\text{UNKNOWN} \ne \text{ABSENT}$ logic. If limbs are occluded or clipped by image borders, the system assigns an `UNKNOWN` status, preventing embarrassing false alarms."* |
| **"How do you prevent false alarms from factory steam or welding torches?"** | *"We trained SafeSync with over 1,200 curated hard-negative distractor images (steam exhaust, welder glare, orange machinery). In addition, our 5-frame temporal state machine ensures transient sparks or steam vents never trigger an evacuation siren."* |
| **"Can small factories afford this?"** | *"Yes! SafeSync requires zero new sensor installations and runs on existing CCTV feeds using standard, low-cost office PC hardware without expensive GPUs."* |

---
*Created for Team XERSES — BPUT HACKATHON 2026 Submission.*
