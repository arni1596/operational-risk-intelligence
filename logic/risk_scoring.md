@'
# Risk Scoring Logic

## Purpose
The risk score is designed to surface operational items that require attention before issues become visible, costly, or reputationally damaging.

The score supports review and escalation decisions. It does not automate outcomes or replace judgment.

## Design philosophy
Operational risk is treated as structured, explainable judgment rather than prediction.

The logic is intentionally deterministic so that results can be questioned, defended, and adjusted as operating context changes.

## Risk factors
Each operational item is evaluated using the following factors:

- Days overdue  
- Number of ownership handoffs  
- Priority level  
- Rework or reopening count  

These factors were selected because they consistently correlate with delivery delay, accountability breakdown, and quality risk in real operational environments.

## Base scoring model

Risk Score =
(Overdue Days × 0.4)
+ (Number of Handoffs × 0.3)
+ (Priority Weight × 0.2)
+ (Rework Count × 0.1)

Weights are illustrative and intended to be calibrated to organizational context.

## Compounding condition
Items that are both high priority and overdue accelerate across risk thresholds faster than items meeting only one condition.

This reflects the nonlinear nature of operational failure.

## Risk thresholds
- 0–30: Stable  
- 31–60: Watch  
- 61+: At Risk  

Thresholds are used to prompt review, not to trigger automatic action.

## Intended use
Risk scores are intended to:
- Focus attention
- Support escalation discussions
- Improve early intervention

They are not intended for performance ranking, punitive evaluation, or automated decision-making.
'@ | Set-Content .\logic\risk_scoring.md -Encoding UTF8
