# Class Distribution Analysis — SafeSync

**Total Processed Images**: 22453 (Train: 15717, Val: 4490, Test: 2246)
**Total Annotated Bounding Boxes**: 51195

## 1. Instance Distribution by Split

| ID | Class Name | Train Instances | Val Instances | Test Instances | Total Instances | % of Total | Images Containing |
|---|---|---|---|---|---|---|---|
| 0 | `person` | 3884 | 1059 | 602 | 5545 | 10.83% | 3450 |
| 1 | `helmet` | 17041 | 5005 | 2485 | 24531 | 47.92% | 9241 |
| 2 | `safety_vest` | 4505 | 1199 | 568 | 6272 | 12.25% | 3001 |
| 3 | `gloves` | 1886 | 500 | 248 | 2634 | 5.15% | 1394 |
| 4 | `safety_footwear` | 1010 | 257 | 240 | 1507 | 2.94% | 445 |
| 5 | `fire` | 3637 | 1131 | 565 | 5333 | 10.42% | 2063 |
| 6 | `smoke` | 3765 | 1106 | 502 | 5373 | 10.5% | 3515 |

## 2. Severe Class Imbalance Assessment

- **Dominant Class**: `helmet` represents ~47.9% of all annotations.
- **Minority Classes**: `safety_footwear` represents ~2.9% and `gloves` represents ~5.1%.
- **Person Class**: Represents ~10.8% of annotations.
- **Fire & Smoke**: Each represents ~10.5% of annotations, well distributed.

## 3. Train/Val/Test Split Proportions

Evaluation of class representation consistency across splits:

- `person`: Train 70.0% | Val 19.1% | Test 10.9%
- `helmet`: Train 69.5% | Val 20.4% | Test 10.1%
- `safety_vest`: Train 71.8% | Val 19.1% | Test 9.1%
- `gloves`: Train 71.6% | Val 19.0% | Test 9.4%
- `safety_footwear`: Train 67.0% | Val 17.1% | Test 15.9%
- `fire`: Train 68.2% | Val 21.2% | Test 10.6%
- `smoke`: Train 70.1% | Val 20.6% | Test 9.3%
