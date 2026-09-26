# Limitations and Failure Modes

## Scope
This repository provides batch analysis, deterministic risk logic, threshold sensitivity review, and generated reporting artifacts intended to support review and escalation discussions.

## Intentional exclusions
The system intentionally does not include:
- Real-time monitoring or streaming pipelines
- Predictive modeling or automated forecasting
- Automated execution of escalations or decisions
- Authentication or role-based access controls

These exclusions reduce complexity and avoid false certainty while the core logic and governance model are validated.

## Known limitations
- Sample data is synthetic and does not represent a real operating environment
- Risk weights and thresholds are illustrative and require review per organization
- Outputs depend on baseline data integrity
- The current scoring model is intentionally linear and does not model interactions among signals
- The generated reports are static outputs, not scheduled monitoring workflows

## Failure modes
- False negatives due to missing or delayed signals
- False positives caused by noisy inputs
- Metric gaming through superficial status updates
- Mistaking correlation between signals for causality

## Mitigations
- Human review remains mandatory for escalation
- Exceptions should be reviewed explicitly
- Risk logic should be reviewed retrospectively against operating context
