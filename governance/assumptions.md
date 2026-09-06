# Assumptions

## Operating Assumptions

- Operational items can be represented with overdue days, ownership handoffs, priority weight, and rework count.
- Higher values for these signals may indicate delivery delay, ownership ambiguity, quality issues, or process friction.
- The sample data is fictional and intended only to exercise the scoring model.
- Risk classifications support review and escalation discussions; they do not automate decisions.

## Scoring Assumptions

- The documented weights in [../logic/risk_scoring.md](../logic/risk_scoring.md) are the source of truth for Phase 2 scoring.
- Scores are reported as whole numbers in review outputs for readability.
- Thresholds are stable for the current sample workflow and should be recalibrated before use in a real operating context.
- Additional rules, such as compounding conditions, should be added only when the business logic is explicitly defined.
