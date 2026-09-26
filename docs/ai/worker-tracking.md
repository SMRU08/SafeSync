# Worker Tracking & Trajectory Estimation

SafeSync tracks individual workers across video frames using a customized implementation of the **ByteTrack** algorithm. This enables continuous, anonymous trajectory estimation and prevents identity switches without requiring facial recognition or personal biometric data.

---

## 1. Tracking Engine Overview

Tracking is decoupled from neural detection. The detector outputs raw `person` bounding boxes with confidence scores, and `ByteTrack` (`app/ai/compliance/tracker.py`) associates these detections across successive frames.

```
Detection Stream (Person Bounding Boxes)
                │
                ▼
      ┌───────────────────┐
      │ Score Partitioning│
      └─────────┬─────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
High-Score (>= 0.5)   Low-Score (0.1 .. 0.5)
        │               │
        ▼               │
Stage 1: Hungarian      │
Matching with Kalman    │
Predicted Tracks        │
        │               │
        ▼               ▼
Unmatched Tracks ──► Stage 2: Hungarian Matching
                     with Low-Score Detections
                        │
                        ▼
      ┌───────────────────────────────────┐
      │ Updated Tracks & Stable Track IDs │
      └───────────────────────────────────┘
```

---

## 2. Kalman Filter Motion Model

Each active track is modeled by an 8-state Kalman Filter (`KalmanBoxTracker`):

$$\mathbf{x} = \begin{bmatrix} x & y & a & h & \dot{x} & \dot{y} & \dot{a} & \dot{h} \end{bmatrix}^T$$

- $x, y$: Centroid coordinates of the worker's bounding box.
- $a$: Aspect ratio of the bounding box ($w / h$).
- $h$: Height of the bounding box.
- $\dot{x}, \dot{y}, \dot{a}, \dot{h}$: Corresponding velocities (first derivatives over time).

The filter predicts worker position in frame $t$ prior to association, allowing the tracker to bridge temporary occlusions when a worker walks behind equipment or columns.

---

## 3. Two-Stage Hungarian Association

Standard tracking algorithms discard low-confidence detections below the detector threshold (e.g. 0.4), causing tracks to fragment when workers are partially occluded. ByteTrack solves this through two-stage association:

1. **Stage 1 (Primary Association):**
   High-confidence detections ($\text{conf} \ge 0.5$) are matched against predicted Kalman tracks using Intersection-over-Union (IoU) distance and the Hungarian assignment algorithm.
2. **Stage 2 (Recovery Association):**
   Remaining unmatched tracks are compared against low-confidence detections ($0.1 \le \text{conf} < 0.5$). This recovers workers whose visibility temporarily drops due to motion blur, lighting changes, or partial obstruction.
3. **Track Initialization & Termination:**
   - A new track is created only if a high-confidence detection cannot be associated with any existing track.
   - A track is maintained in a "lost" state for up to `max_lost = 30` consecutive frames (~1.0–1.5 seconds) before being retired.

---

## 4. Privacy & Anonymity Guarantees

- **Zero Biometrics:** The system does not extract facial embeddings, gait signatures, or identifying personal markers.
- **Anonymous Session IDs:** Workers are assigned transient integer IDs (`track_id: 1, 2, 3...`) valid only within the camera view session.
- **Automatic Expiration:** Once a worker exits the camera field of view, the track ID is purged from active memory after the 30-frame buffer expires.
