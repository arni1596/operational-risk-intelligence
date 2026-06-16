# Risk Scoring Logic

## Purpose

The risk score is designed to surface operational items that may require attention before issues become visible, costly, or difficult to recover from.

The score supports review and escalation decisions. It does not automate outcomes or replace human judgment.

## Design Philosophy

Operational risk is treated as structured, explainable judgment rather than prediction.

The logic is intentionally deterministic so that results can be questioned, defended, and adjusted as operating context changes.

## Risk Factors

Each operational item is evaluated using the following factors:

- Days overdue
- Number of ownership handoffs
- Priority level
- Rework or reopening count

These factors were selected because they can indicate delivery delay, accountability breakdown, quality risk, or process friction in operational environments.

## Base Scoring Model

```text
Risk Score =
(Overdue Days x 0.4)
+ (Number of Handoffs x 0.3)
+ (Priority Weight x 0.2)
+ (Rework Count x 0.1)
```

Weights are illustrative and should be calibrated to the operating context before real-world use.

## Compounding Condition

Items that are both high priority and overdue should move across risk thresholds faster than items meeting only one condition.

This reflects the nonlinear nature of operational failure: multiple moderate signals can combine into a larger review concern.

## Risk Thresholds

| Score Range | Label | Intended Meaning |
| --- | --- | --- |
| 0-30 | Stable | No immediate risk signal based on current rules |
| 31-60 | Watch | Review recommended |
| 61+ | At Risk | Escalation or closer follow-up may be needed |

Thresholds are used to prompt review, not to trigger automatic action.

## Intended Use

Risk scores are intended to:

- Focus attention
- Support escalation discussions
- Improve early intervention
- Create a clear explanation trail for review meetings

They are not intended for performance ranking, punitive evaluation, or automated decision-making.
