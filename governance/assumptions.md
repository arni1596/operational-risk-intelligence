# Assumptions

## Operating Assumptions

- Operational items can be represented with overdue days, ownership handoffs, priority weight, and rework count.
- Higher values for these signals may indicate delivery delay, ownership ambiguity, quality issues, or process friction.
- The sample data is fictional and intended only to exercise the scoring model.
- Risk classifications support review and escalation discussions; they do not automate decisions.

## Scoring Assumptions

- The documented weights in [../logic/risk_scoring.md](../logic/risk_scoring.md) are the source of truth for the current scoring model.
- Review outputs use whole-number scores for readability. Exact weighted scores remain available for audit and regression testing.
- Whole-number review scores use conventional half-up rounding before the documented classification thresholds are applied.
- Thresholds are stable for the current sample workflow and should be reviewed before use in a real operating context.
- Future nonlinear or interaction logic would require an explicit business definition and separate validation.
