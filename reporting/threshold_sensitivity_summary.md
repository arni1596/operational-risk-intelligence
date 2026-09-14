# Threshold Sensitivity Analysis

## Purpose

This report tests how illustrative threshold changes affect review classifications for the fictional sample dataset. It does not recommend changing the default thresholds and does not represent production calibration.

## Scenario Definitions

| Scenario | Stable Upper Bound | Watch Upper Bound | Purpose |
| --- | ---: | ---: | --- |
| Current | 30 | 60 | Existing default review thresholds. |
| Earlier Review | 25 | 55 | Illustrative scenario where items enter review classifications earlier. |
| Later Review | 35 | 65 | Illustrative scenario where items enter review classifications later. |

## Classification Distribution

| Scenario | Stable | Watch | At Risk |
| --- | ---: | ---: | ---: |
| Current | 4 | 3 | 1 |
| Earlier Review | 3 | 4 | 1 |
| Later Review | 4 | 4 | 0 |

## Classification Changes

### Earlier Review

| Item ID | Review Score | Current | Scenario | Change |
| --- | ---: | --- | --- | --- |
| OPS-1215 | 26 | Stable | Watch | Stable -> Watch |

### Later Review

| Item ID | Review Score | Current | Scenario | Change |
| --- | ---: | --- | --- | --- |
| OPS-1042 | 61 | At Risk | Watch | At Risk -> Watch |

## Interpretation

- Earlier Review changes 1 record(s) compared with Current and moves review volume from 4 to 5.
- Later Review changes 1 record(s) compared with Current and moves review volume from 4 to 4.
- These scenarios vary classification thresholds only; exact scores and review scores are unchanged for each operational item.
