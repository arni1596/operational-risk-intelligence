# Operational Risk Review Summary

Generated from the fictional sample dataset in `data/validated/sample_operational_items.csv` using the documented risk-scoring model.

## Classification Distribution

| Classification | Count |
| --- | ---: |
| At Risk | 1 |
| Watch | 3 |
| Stable | 4 |

## Top Review Candidates

| Item ID | Review Score | Exact Score | Flag | Primary Reason | Suggested Review |
| --- | ---: | ---: | --- | --- | --- |
| OPS-1042 | 61 | 61.0 | At Risk | Significantly overdue at 120 days | Confirm ownership, identify blockers, and determine whether escalation is needed |
| OPS-1194 | 50 | 50.3 | Watch | Overdue by 85 days | Confirm ownership and monitor during the next review |
| OPS-1288 | 40 | 40.4 | Watch | Overdue by 75 days | Confirm ownership and monitor during the next review |
| OPS-1087 | 37 | 37.2 | Watch | Overdue by 60 days | Confirm ownership and monitor during the next review |

## Flag Explanations

### OPS-1042: At Risk

- Exact score: 61.0
- Review score: 61
- Classification rule: `review_score >= 61`
- Status: In Review
- Signals: overdue_days=120, handoff_count=8, priority_weight=50, rework_count=6
- Reasons: Significantly overdue at 120 days; Elevated priority weight of 50; Multiple ownership handoffs (8); Repeated rework or reopening count (6); Combined signals meet the at-risk review threshold
- Suggested review: Confirm ownership, identify blockers, and determine whether escalation is needed

### OPS-1087: Watch

- Exact score: 37.2
- Review score: 37
- Classification rule: `31 <= review_score <= 60`
- Status: Open
- Signals: overdue_days=60, handoff_count=8, priority_weight=50, rework_count=8
- Reasons: Overdue by 60 days; Elevated priority weight of 50; Multiple ownership handoffs (8); Repeated rework or reopening count (8); Combined signals meet the watch review threshold
- Suggested review: Confirm ownership and monitor during the next review

### OPS-1194: Watch

- Exact score: 50.3
- Review score: 50
- Classification rule: `31 <= review_score <= 60`
- Status: Blocked
- Signals: overdue_days=85, handoff_count=6, priority_weight=70, rework_count=5
- Reasons: Overdue by 85 days; Elevated priority weight of 70; Multiple ownership handoffs (6); Repeated rework or reopening count (5); Combined signals meet the watch review threshold
- Suggested review: Confirm ownership and monitor during the next review

### OPS-1288: Watch

- Exact score: 40.4
- Review score: 40
- Classification rule: `31 <= review_score <= 60`
- Status: In Review
- Signals: overdue_days=75, handoff_count=7, priority_weight=40, rework_count=3
- Reasons: Overdue by 75 days; Multiple ownership handoffs (7); 3 rework or reopening event(s); Combined signals meet the watch review threshold
- Suggested review: Confirm ownership and monitor during the next review
