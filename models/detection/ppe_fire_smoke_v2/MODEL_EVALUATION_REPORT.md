# Model Evaluation Report — ppe_fire_smoke_v2

**Date:** 2026-09-20T17:15:42.428420 UTC

## Per-Class Metrics

| Split | Class | Precision | Recall | mAP50 | mAP50-95 |
|-------|-------|-----------|--------|-------|----------|
| val | person | 0.2777 | 0.5071 | 0.2038 | 0.1147 |
| val | helmet | 0.6049 | 0.8186 | 0.7257 | 0.3846 |
| val | safety_vest | 0.3286 | 0.5196 | 0.2926 | 0.1179 |
| val | gloves | 0.3974 | 0.1820 | 0.0866 | 0.0341 |
| val | safety_footwear | 0.0957 | 0.0778 | 0.0478 | 0.0191 |
| val | fire | 0.4502 | 0.2679 | 0.1796 | 0.0716 |
| val | smoke | 0.5262 | 0.2902 | 0.2227 | 0.0892 |
| val | ALL | 0.3830 | 0.3805 | 0.2512 | 0.1187 |
| test | person | 0.3028 | 0.5000 | 0.2264 | 0.1300 |
| test | helmet | 0.6075 | 0.8109 | 0.7284 | 0.3808 |
| test | safety_vest | 0.3145 | 0.5088 | 0.2889 | 0.1158 |
| test | gloves | 0.3478 | 0.1613 | 0.0915 | 0.0383 |
| test | safety_footwear | 0.0619 | 0.0292 | 0.0034 | 0.0017 |
| test | fire | 0.4199 | 0.3062 | 0.2015 | 0.0902 |
| test | smoke | 0.5774 | 0.3048 | 0.2262 | 0.0856 |
| test | ALL | 0.3760 | 0.3744 | 0.2523 | 0.1203 |

## Confidence Threshold Analysis

| Threshold | Precision | Recall | mAP50 | mAP50-95 |
|-----------|-----------|--------|-------|----------|
| 0.25 | 0.3830 | 0.3805 | 0.2512 | 0.1187 |
| 0.35 | 0.4603 | 0.3214 | 0.2262 | 0.1091 |
| 0.5 | 0.5400 | 0.2295 | 0.1768 | 0.0887 |
| 0.6 | 0.6023 | 0.1751 | 0.1428 | 0.0734 |
| 0.7 | 0.6502 | 0.1227 | 0.1064 | 0.0561 |

## Notes

- Metrics are on the held-out validation and test sets only.
- Test set was NOT used for hyperparameter tuning.
- See `error_analysis.md` for class imbalance analysis.
- See `confidence_analysis.csv` for full threshold data.
