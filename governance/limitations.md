# Limitations and Failure Modes

## Scope
This repository represents Phase 1: batch analysis, deterministic risk logic, and static decision briefs intended to support review and escalation.

## Intentional exclusions
The system intentionally does not include:
- Real-time monitoring or streaming pipelines
- Predictive modeling or automated forecasting
- Automated execution of escalations or decisions
- Authentication or role-based access controls (Phase 2 consideration)

These exclusions reduce complexity and avoid false certainty while the core logic and governance model are validated.

## Known limitations
- Risk weights are illustrative and require calibration per organization
- Outputs depend on baseline data integrity
- Weekly cadence may be insufficient for high-velocity environments
- Nonlinear risk may be underrepresented without custom compounding rules

## Failure modes
- False negatives due to missing or delayed signals
- False positives caused by noisy inputs
- Metric gaming through superficial status updates

## Mitigations
- Human review remains mandatory for escalation
- Exceptions should be reviewed explicitly
- Risk logic should be tuned retrospectively
