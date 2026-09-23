# Operational Review Dashboard

Generated from the fictional sample dataset in `data/validated/sample_operational_items.csv` using the existing scoring and threshold sensitivity workflows.

## Current Portfolio Snapshot

| Metric | Count | Share |
| --- | ---: | ---: |
| Total Items | 8 | 100.0% |
| Stable | 4 | 50.0% |
| Watch | 3 | 37.5% |
| At Risk | 1 | 12.5% |
| Review Queue | 4 | 50.0% |

## Priority Review Queue

| Rank | Item ID | Status | Review Score | Exact Score | Classification | Overdue Days | Handoffs | Rework | Suggested Review |
| ---: | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 1 | OPS-1042 | In Review | 61 | 61.0 | At Risk | 120 | 8 | 6 | Confirm ownership, identify blockers, and determine whether escalation is needed |
| 2 | OPS-1194 | Blocked | 50 | 50.3 | Watch | 85 | 6 | 5 | Confirm ownership and monitor during the next review |
| 3 | OPS-1288 | In Review | 40 | 40.4 | Watch | 75 | 7 | 3 | Confirm ownership and monitor during the next review |
| 4 | OPS-1087 | Open | 37 | 37.2 | Watch | 60 | 8 | 8 | Confirm ownership and monitor during the next review |

## Signal Snapshot

The current review queue includes only items classified as Watch or At Risk.

| Signal | Value |
| --- | ---: |
| Review queue items with overdue days | 4 |
| Total overdue days across review queue | 340 |
| Total handoffs across review queue | 29 |
| Total rework across review queue | 22 |
| Highest overdue-days value | 120 |
| Highest handoff count | 8 |
| Highest rework count | 8 |

| Item ID | Overdue Days | Handoffs | Rework | Primary Reason |
| --- | ---: | ---: | ---: | --- |
| OPS-1042 | 120 | 8 | 6 | Significantly overdue at 120 days |
| OPS-1194 | 85 | 6 | 5 | Overdue by 85 days |
| OPS-1288 | 75 | 7 | 3 | Overdue by 75 days |
| OPS-1087 | 60 | 8 | 8 | Overdue by 60 days |

## Threshold Sensitivity Snapshot

| Scenario | Stable | Watch | At Risk | Review Volume |
| --- | ---: | ---: | ---: | ---: |
| Current | 4 | 3 | 1 | 4 |
| Earlier Review | 3 | 4 | 1 | 5 |
| Later Review | 4 | 4 | 0 | 4 |

## Classification Movement

| Scenario | Item ID | Review Score | Current | Scenario | Change |
| --- | --- | ---: | --- | --- | --- |
| Earlier Review | OPS-1215 | 26 | Stable | Watch | Stable -> Watch |
| Later Review | OPS-1042 | 61 | At Risk | Watch | At Risk -> Watch |

Scenario movement summary:

- Earlier Review: OPS-1215 moves Stable -> Watch.
- Later Review: OPS-1042 moves At Risk -> Watch.

## Review Notes

- Scoring is deterministic and follows the documented weighted rule set.
- Threshold values are illustrative and should not be treated as production calibration.
- Source data is fictional and intended for prototype review.
- The dashboard supports prioritization and discussion; human operational judgment is still required.
- Sensitivity scenarios are not recommendations and do not change the default scoring configuration.
