# Operational Review Dashboard

Generated from the fictional sample dataset in `data/validated/sample_operational_items.csv` using the existing scoring and threshold sensitivity workflows.

## Current Risk Snapshot

| Classification | Count |
| --- | ---: |
| At Risk | 1 |
| Watch | 3 |
| Stable | 4 |

Current review volume: 4 item(s) classified as Watch or At Risk.

## Priority Review Queue

| Item ID | Status | Review Score | Exact Score | Flag | Primary Reason | Suggested Review |
| --- | --- | ---: | ---: | --- | --- | --- |
| OPS-1042 | In Review | 61 | 61.0 | At Risk | Significantly overdue at 120 days | Confirm ownership, identify blockers, and determine whether escalation is needed |
| OPS-1194 | Blocked | 50 | 50.3 | Watch | Overdue by 85 days | Confirm ownership and monitor during the next review |
| OPS-1288 | In Review | 40 | 40.4 | Watch | Overdue by 75 days | Confirm ownership and monitor during the next review |
| OPS-1087 | Open | 37 | 37.2 | Watch | Overdue by 60 days | Confirm ownership and monitor during the next review |

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

## Review Focus

- 1 item(s) currently meet the At Risk threshold.
- The Earlier Review scenario moves review volume from 4 to 5 item(s).
- The Later Review scenario keeps review volume at 4 item(s), but changes the classification for OPS-1042.
- Scenario results are for threshold sensitivity review only; they do not change the default scoring configuration.
