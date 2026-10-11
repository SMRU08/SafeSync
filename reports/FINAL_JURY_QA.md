# SafeSync Final Prototype — Phase D: Jury Q&A Technical Defense Guide

**Document:** `reports/FINAL_JURY_QA.md`  
**Date:** 2026-10-11  
**Project:** SafeSync Industrial Safety Operations Center  
**Target:** Hackathon Evaluation Jury, Technical Evaluators, Industry Experts  

---

## 1. Computer Vision & Model Architecture

### Q1: Why did you select YOLOv8 over faster models (e.g. SSD, MobileNet) or heavier models (e.g. Faster R-CNN, Mask R-CNN)?
**Answer:**  
Industrial safety monitoring requires **real-time single-pass multi-class inference** at edge frame rates (15–30 FPS).
- Two-stage detectors (like Faster R-CNN) yield higher per-pixel precision but introduce latencies $> 300\text{ ms}$ on edge hardware, causing severe video buffering lag.
- Legacy one-stage detectors (SSD, MobileNet-SSD) suffer from poor localization on small objects (like safety glasses, gloves, and small fire seeds).
- **YOLOv8n** utilizes an anchor-free decoupled head with C2f feature aggregation, providing an optimal Pareto frontier: 3.2M parameters, fast CPU inference (~100ms on standard Intel CPU, <15ms on GPU), and high sensitivity for compact safety objects.

### Q2: How was the model trained, and what datasets were used?
**Answer:**  
The active production model is `ppe_fire_smoke_v3` (`best.pt`, SHA-256: `9b414f3018d54ae5...`).
- It was trained on the curated `processed_v3` dataset (4,100 leakage-free industrial images) combining:
  1. `ppe_safup`: Richly annotated multi-worker imagery with co-occurring `person`, `helmet`, and `safety_vest` annotations.
  2. `ppec`: Industrial construction floor scenarios.
  3. `d_fire` / industrial hazard data: Authenticated flame and smoke plume samples.
- **Forensic Dataset Fix:** In earlier versions (`ppe_fire_smoke_v2`), datasets like `construction_ppe` had zero `person` annotations, which caused the neural network to suppress person detections when high-vis vests were present. We purged poisoned annotations and balanced full-body person envelopes, eliminating the "invisible worker" bug.

### Q3: What are the canonical classes and confidence thresholds?
**Answer:**  
SafeSync standardizes on 7 canonical classes:
- `0: person` (conf threshold: 0.25)
- `1: helmet` (conf threshold: 0.20)
- `2: safety_vest` (conf threshold: 0.20)
- `3: gloves` (conf threshold: 0.20)
- `4: safety_footwear` (conf threshold: 0.20)
- `5: fire` (conf threshold: 0.25)
- `6: smoke` (conf threshold: 0.25)

---

## 2. Safety Logic & Compliance Engineering

### Q4: What is the "UNKNOWN" state and why is it critical in industrial safety?
**Answer:**  
Most naive computer vision systems employ binary logic (`COMPLIANT` vs `VIOLATION`). If a worker is seated at a desk or behind equipment where their feet cannot be seen, a binary system marks `FOOTWEAR: ABSENT` and levies a false violation fine.
SafeSync enforces **Tri-State Compliance Logic**:
- **PRESENT:** Positively detected and anatomically associated.
- **ABSENT:** Confirmed absent only when the body region is clearly visible, unoccluded, and missed across $\ge 15$ consecutive frames.
- **UNKNOWN:** Assigned whenever an anatomical zone is occluded by foreground obstacles, clipped by frame borders, or too small to evaluate.
**Safety Rule:** *UNKNOWN is strictly non-violating, but never declared SAFE.*

### Q5: How do you prevent civilian yellow/orange clothing from triggering fire alerts?
**Answer:**  
SafeSync employs **Torso Exclusion Masking** and **Independent Optical Passes**:
1. Fire and smoke detections are processed independently of worker PPE.
2. If a candidate fire bounding box has $> 60\%$ spatial intersection with a detected worker's torso region, it is evaluated through chromatic flicker and spatial bounding analysis. Steady, static orange reflective strips on clothing are rejected as clothing artifacts, preventing false plant evacuation alarms.

### Q6: How does SafeSync handle multi-worker contention when workers stand close together?
**Answer:**  
SafeSync uses **Optimal Bipartite Matching** (`scipy.optimize.linear_sum_assignment` / Hungarian Algorithm).
- Rather than assigning a detected helmet to the nearest bounding box centroid, SafeSync computes an affinity cost matrix based on:
  1. Relative vertical band: Cranium region ($Y_c \in [-0.15, 0.32]$).
  2. Horizontal center alignment: Helmet center within worker lateral bounds $\pm 20\%$.
  3. Containment ratio.
- Bipartite matching mathematically guarantees that one helmet cannot be claimed by two workers, preventing cross-worker attribution bleed.

---

## 3. Performance & Real-World Feasibility

### Q7: Why does the live video stream not freeze if AI inference takes ~100ms?
**Answer:**  
SafeSync decouples video capture from AI inference using a **multi-threaded architecture**:
- **Capture Thread (Thread 1):** Dedicated hardware loop running at 15–30 FPS, reading DirectShow frames without delay.
- **AI Thread (Thread 2):** Runs asynchronously with a **1-slot bounded latest-frame-wins buffer**.
- When inference finishes on frame $N$, it immediately grabs the newest frame from the camera buffer, dropping any intermediate frames from the inference queue. This ensures zero memory bloat and sub-50ms display latency.

### Q8: What are the current limitations of this prototype?
**Answer:**  
1. **CPU vs GPU:** On standard CPU, inference runs at ~100ms (~10 FPS). On systems with an NVIDIA GPU, CUDA engages automatically to reduce latency to <15ms.
2. **Desk Webcam Framing:** A close-up desktop webcam naturally crops lower extremities, correctly showing `UNKNOWN (occluded)`. In production industrial deployment, wide-angle ceiling-mounted cameras capture full-body envelopes.
3. **Small-Flame Distance:** Tiny flame seeds (< 15 pixels in size) require high optical resolution (1080p/4K) for positive identification.
