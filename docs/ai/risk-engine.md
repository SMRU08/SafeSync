# Explainable Risk Engine

SafeSync uses a transparent, deterministic mathematical risk engine (`RiskEngine`) to quantify safety risk. Rather than relying on opaque deep-learning score predictions, risk is calculated using inspectable rules and policy weights defined in `configs/risk_policy.yaml`.

---

## 1. Risk Scoring Formula

The risk score is computed on a scale from $0$ to $100$:

$$\text{Score} = \text{clamp}\left( \Big(\text{BaseSeverity} + \text{PersistenceFactor} + \text{WorkerDensityFactor} + \text{RecurrenceFactor}\Big) \times \text{ZoneMultiplier},\; 0,\; 100 \right)$$

```
Normalized Safety Event
          │
          ▼
┌────────────────────────────────────────────────────────┐
│               Risk Factor Evaluation                   │
│                                                        │
│  1. Base Severity (Missing Helmet: +30, Fire: +90)     │
│  2. Persistence Weight (Duration in Seconds * 0.5)     │
│  3. Worker Density ((Affected Workers - 1) * 5)        │
│  4. Recurrence Penalty (Repeated Violations in 1 Hour) │
│  5. Zone Risk Multiplier (Hazardous Zone: 1.2x - 1.8x) │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            Clamping to [0, 100] & Tier Mapping         │
│  - LOW (0 - 29)          - HIGH (60 - 84)              │
│  - MEDIUM (30 - 59)      - CRITICAL (85 - 100)         │
└────────────────────────────────────────────────────────┘
```

---

## 2. Factor Breakdown

### 2.1 Base Severity Weights
The baseline severity reflects the immediate intrinsic danger of the safety violation or hazard:

| Event Type | Base Severity | Standard Operational Classification |
|---|---|---|
| `MISSING_HELMET` | 30 | Medium |
| `MISSING_SAFETY_VEST` | 25 | Medium |
| `MISSING_GLOVES` | 10 | Low |
| `MISSING_SAFETY_FOOTWEAR` | 15 | Low |
| `SMOKE_DETECTED` | 70 | High |
| `FIRE_DETECTED` | 90 | Critical |

### 2.2 Persistence Factor
Prolonged violations pose escalating danger. The system adds $+0.5$ points per second of sustained violation, capped at $+20$ points:

$$\text{PersistenceFactor} = \min(20,\; \text{duration\_seconds} \times 0.5)$$

### 2.3 Worker Density Multiplier
In high-occupancy zones or near heavy equipment, hazards threaten multiple individuals simultaneously:

$$\text{WorkerDensityFactor} = \max(0,\; (\text{affected\_workers} - 1) \times 5)$$

### 2.4 Zone Risk Multipliers
Different physical areas exhibit varying baseline hazards, configured in `configs/cameras.yaml`:

- **Low Hazard Zone (e.g. Office / Break Area):** `1.0×`
- **Standard Floor (e.g. Main Assembly Line):** `1.1×`
- **High Risk Zone (e.g. Crane Corridor / Heavy Machinery):** `1.4×`
- **Extreme Hazard Zone (e.g. High-Voltage Electrical Room):** `1.8×`

---

## 3. Operational Severity Tiers

| Score Range | Severity Level | System Response | Operator SLA |
|---|---|---|---|
| **0 – 29** | **LOW** | Recorded to database; advisory badge on dashboard. | End of shift review |
| **30 – 59** | **MEDIUM** | Dashboard alert card; sound notification. | Within 15 minutes |
| **60 – 84** | **HIGH** | Priority alert banner; webhook/email dispatch. | Within 3 minutes |
| **85 – 100** | **CRITICAL** | Full-screen visual alarm; emergency broadcast; sirens/SMS. | Immediate (< 30 seconds) |

---

## 4. Transparent Auditability

Every calculated score returns a full `RiskScoreBreakdown` schema, guaranteeing complete mathematical transparency for safety incident investigations:

```json
{
  "score": 72,
  "level": "HIGH",
  "factors": {
    "base_severity": 30.0,
    "persistence_factor": 12.0,
    "worker_density_factor": 5.0,
    "recurrence_factor": 0.0,
    "zone_multiplier": 1.5,
    "raw_score": 70.5
  },
  "explanation": "Worker #102 missing required helmet in High-Risk Turbine Zone (1.5x multiplier) sustained for 24 seconds with 2 workers in close proximity."
}
```
