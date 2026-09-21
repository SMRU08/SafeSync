# Known Limitations & Operating Boundaries

This document outlines the known physical, computational, and environmental limitations of RAKSHYA VISION.

---

## 1. Computer Vision & Optical Boundaries

### 1.1 Small PPE Item Detection at Distance
- **Observation:** While `person`, `helmet`, and `safety_vest` detections maintain high reliability up to 20 meters from standard 1080p cameras, smaller items (`gloves` and `safety_footwear`) require at least $40 \times 40$ pixels on target.
- **Limitation:** Beyond 15 meters, glove and safety shoe detection confidence degrades significantly. In far-field camera views, the system marks gloves and footwear as `UNKNOWN` rather than generating false alarms.
- **Recommended Practice:** Install dedicated choke-point or turnstile cameras at facility entry gates for detailed glove and footwear compliance checks.

### 1.2 Steep Overhead Camera Angles
- **Observation:** Cameras mounted directly overhead ($> 60^\circ$ pitch angle relative to the floor) compress worker anatomy into a top-down circle.
- **Limitation:** At steep angles, the torso and legs are occluded by the head and shoulders, preventing reliable safety vest and footwear association.
- **Recommended Practice:** Mount cameras at oblique angles between $15^\circ$ and $45^\circ$ elevation.

---

## 2. Environmental & Atmospheric Conditions

### 2.1 Low Illuminance & Night Shifts
- **Observation:** In ambient light conditions below 15 lux, sensor noise increases and color fidelity drops, impairing high-visibility vest detection.
- **Recommended Practice:** Maintain adequate facility lighting or deploy commercial CCTV cameras equipped with active infrared (IR) night illuminators.

### 2.2 Industrial Steam & Condensation
- **Observation:** High-volume boiler blowdown steam or heavy industrial mist exhibits fluid dynamics similar to white smoke plumes.
- **Mitigation:** Operators must define polygon exclusion masks (`roi_polygons` in `configs/cameras.yaml`) around stationary steam vents to avoid false hazard confirmations.

---

## 3. Hardware & Concurrency Boundaries

### 3.1 Multi-Stream CPU Concurrency
- **Observation:** On standard 8-core CPU hardware, running YOLOv8n inference on more than 3 simultaneous 30 FPS streams causes frame queue build-up if every frame is analyzed.
- **Mitigation:** The system employs frame scheduling (`infer_interval_frames = 2` or `3`) to sustain 10–15 FPS analytics across multiple cameras while maintaining 100% video display smoothness.
- **Scale-Up:** For installations exceeding 4 concurrent high-resolution streams, adding an edge GPU (e.g. NVIDIA RTX 3060 / T4) is strongly recommended.
