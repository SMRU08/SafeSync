# Error Analysis — ppe_fire_smoke_v2

**Generated:** 2026-09-20T17:15:42.425936 UTC

## Known Dataset Biases

| Class | Boxes | % of Total | Risk |
|-------|-------|------------|------|
| helmet | 24,531 | 47.92% | Overrepresented — model may be biased |
| safety_vest | 6,272 | 12.25% | Moderate |
| person | 5,545 | 10.83% | Moderate |
| smoke | 5,373 | 10.50% | Moderate |
| fire | 5,333 | 10.42% | Moderate |
| gloves | 2,634 | 5.15% | Underrepresented — may underperform |
| safety_footwear | 1,507 | 2.94% | Most underrepresented — highest recall risk |

## Validation Metrics

See `MODEL_EVALUATION_REPORT.md` for full per-class results.
