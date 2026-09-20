# Model Evaluation Report — ppe_fire_smoke_v1

**Date:** 2026-09-20T15:29:22.848349 UTC

## Per-Class Metrics

| Split | Class | Precision | Recall | mAP50 | mAP50-95 |
|-------|-------|-----------|--------|-------|----------|
| val | person | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| val | helmet | 0.5076 | 0.3475 | 0.2210 | 0.0585 |
| val | safety_vest | 0.1855 | 0.0492 | 0.0161 | 0.0048 |
| val | gloves | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| val | safety_footwear | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| val | fire | 0.4708 | 0.1353 | 0.0848 | 0.0320 |
| val | smoke | 0.4750 | 0.2577 | 0.1787 | 0.0568 |
| val | ALL | 0.2341 | 0.1128 | 0.0715 | 0.0217 |
| test | person | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| test | helmet | 0.4977 | 0.3461 | 0.2224 | 0.0550 |
| test | safety_vest | 0.1747 | 0.0511 | 0.0174 | 0.0057 |
| test | gloves | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| test | safety_footwear | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| test | fire | 0.4808 | 0.1770 | 0.1106 | 0.0406 |
| test | smoke | 0.4343 | 0.2371 | 0.1383 | 0.0427 |
| test | ALL | 0.2268 | 0.1159 | 0.0698 | 0.0206 |

## Confidence Threshold Analysis

| Threshold | Precision | Recall | mAP50 | mAP50-95 |
|-----------|-----------|--------|-------|----------|
| 0.25 | 0.2341 | 0.1128 | 0.0715 | 0.0217 |
| 0.35 | 0.2829 | 0.0812 | 0.0563 | 0.0172 |
| 0.5 | 0.3232 | 0.0474 | 0.0357 | 0.0111 |
| 0.6 | 0.3614 | 0.0305 | 0.0247 | 0.0077 |
| 0.7 | 0.4044 | 0.0166 | 0.0128 | 0.0044 |

## Notes

- Metrics are on the held-out validation and test sets only.
- Test set was NOT used for hyperparameter tuning.
- See `error_analysis.md` for class imbalance analysis.
- See `confidence_analysis.csv` for full threshold data.
