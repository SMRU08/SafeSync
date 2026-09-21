# Phase 6 — False-Positive & Environmental Interference Analysis

**Project:** RAKSHYA VISION — AI Vision-Based Safety Monitoring  
**Phase:** 6 (Fire & Smoke Hazard Analysis)  
**Date:** September 2026  

---

## 1. Scope & Objective

Computer vision models for fire and smoke detection are notoriously vulnerable to false alarms in industrial, construction, and outdoor manufacturing environments. This document provides an honest, empirical analysis of optical challenges and false-positive triggers observed during Phase 3/3.1 model validation and Phase 6 temporal pipeline testing.

> [!WARNING]
> The RAKSHYA VISION fire and smoke detection system is an assistive safety monitoring tool. It **does NOT replace** certified flame detectors, ionization/optical smoke alarms, sprinkler release sensors, or fire-safety regulatory compliance equipment.

---

## 2. Tested & Observed Environmental Interference Scenarios

### 2.1 Orange & Red Industrial Objects (Color Mimicry)
* **Description:** High-visibility safety vests, red traffic cones, orange hard hats, and crimson toolboxes exhibit color distributions ($R > 200, G < 100, B < 50$) that overlap with active hydrocarbon flame spectra.
* **Observed Impact:** In Phase 3.1 evaluation, solitary red or neon-orange objects occasionally yielded low-confidence fire detections ($0.20 \le \text{conf} < 0.28$) under direct sunlight.
* **Mitigation Implemented:**
  1. *Confidence thresholding:* Set `fire_confidence: 0.25` in `configs/hazard.yaml`.
  2. *Spatial tracking & aspect ratio stability:* Real flames exhibit dynamic flicker and shape expansion, whereas static objects retain constant centroid coordinates and area.
  3. *Temporal confirmation:* Single-frame glints produce `SUSPECTED` states that decay within `max_gap_frames = 5` rather than transitioning to `CONFIRMED`.
* **Remaining Limitation:** Prolonged specular reflections or vibrating red tarpaulins can maintain intermittent detections that require temporal verification.

### 2.2 Steam, Exhaust & Particulate Clouds (Texture Mimicry)
* **Description:** Industrial boiler steam, hot vapor discharge, heavy diesel vehicle exhaust, and concrete cutting dust plumes resemble white/gray smoke plumes in grayscale intensity and diffuse boundary characteristics.
* **Observed Impact:** The baseline model produces moderate false-positive detections on dense steam exhaust when back-lit by bright morning sun.
* **Mitigation Implemented:**
  1. *Temporal evidence accumulation:* Sudden steam puffs that dissipate within 1–3 seconds fail the `confirmation_frames = 5` and `minimum_observation_ratio = 0.60` thresholds.
  2. *Clearing state transition:* As steam rapidly diffuses and cools, missed frame streaks rapidly trigger `clear_frames = 10`, reverting the track to `CLEARED` and `NO_HAZARD`.
* **Remaining Limitation:** Continuous, high-volume boiler exhaust escaping through an unmonitored vent will produce a persistent smoke event unless an exclusion ROI is drawn around the vent.

### 2.3 Bright Glare, Floodlights & Welding Arcs (Luminance Glare)
* **Description:** Direct sunlight in CCTV lenses, nighttime stadium floodlights, and structural arc welding emit intense localized luminance exceeding 250 in 8-bit channels.
* **Observed Impact:** Welding arcs produce high-intensity flicker with localized smoke plumes, which the model detects as both fire and smoke.
* **Mitigation Implemented:**
  1. Multi-modal relationship logging: Categorized as `FIRE_AND_SMOKE` rather than ambiguous single classes.
  2. Zone assignment: If camera is mapped to `production_floor` or `loading_dock`, event is contextualized.
* **Remaining Limitation:** Arc welding will trigger fire/smoke events in standard fabrication zones unless specifically excluded via hot-work permits or localized ROI masks.

### 2.4 Dust Clouds & Fog (Atmospheric Scatter)
* **Description:** High-particulate construction dust (earthmoving operations) or dense morning maritime fog reduces overall scene contrast and creates diffuse gray gradients.
* **Observed Impact:** Fog reduces detection confidence across all classes, resulting in higher false-negative rates for distant smoke plumes.
* **Mitigation Implemented:**
  - Independent confidence thresholds: `smoke_confidence` is kept configurable and decoupled from fire.
* **Remaining Limitation:** Extremely thick dust or fog cannot be penetrated by standard visible-spectrum RGB CCTV cameras without thermal/LWIR imagery.

---

## 3. Summary of Temporal Filter Effectiveness

| Interference Source | Single-Frame Impact | Filter Stage Applied | Final State Achieved | False Positive Prevented? |
| :--- | :--- | :--- | :--- | :--- |
| **High-vis vest glare** | Conf ~0.22 | Confidence threshold (0.25) | Discarded at detection | **YES** |
| **Brief orange reflection** | Conf ~0.27 (1 frame) | Temporal state machine | `SUSPECTED` $\rightarrow$ `CLEARED` | **YES** |
| **Puff of truck exhaust** | Conf ~0.35 (2 frames) | Confirmation frames ($N=5$) | `SUSPECTED` $\rightarrow$ `CLEARED` | **YES** |
| **Boiler vent steam** | Conf ~0.45 (sustained) | Requires polygon ROI exclusion | `CONFIRMED` | **NO (Requires Zone ROI)** |
| **Welding arc operation** | Conf ~0.75 (sustained) | Multi-modal tracking | `CONFIRMED` | **NO (True Flame Detection)** |

---

## 4. Engineering Recommendations for Phase 7

1. **Polygon Exclusion Zones:** For fixed cameras pointing near known heat sources (furnaces, exhausts, welding bays), configure polygon ROIs in `configs/cameras.yaml` to exclude known hot zones.
2. **Thermal / Multi-Spectral Input:** When high-reliability fire suppression triggering is required, visible RGB cameras should be paired with thermal radiometric or flame-flicker sensors.
3. **Phase 7 Alert Policies:** Alert dispatchers must use persistence duration and confirmation state before notifying human emergency dispatchers.
