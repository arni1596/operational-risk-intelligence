# Data Overview

This directory contains operational data used by the system.

- `validated/`: fictional normalized input data used by the executable analysis workflows

A raw ingestion layer can be introduced later if a real ingestion and normalization example is added.

## Current Sample Data

[validated/sample_operational_items.csv](validated/sample_operational_items.csv) contains fictional sample records used to exercise the scoring model. The sample includes stable items, overdue work, elevated priority, repeated handoffs, rework, and combined risk factors.

[validated/sample_readiness_initiatives.csv](validated/sample_readiness_initiatives.csv) contains the fictional initiative inventory used by Operational Readiness Assurance. The inventory defines which initiatives must be evaluated and does not contain readiness outcomes.

[validated/sample_readiness_assessments.csv](validated/sample_readiness_assessments.csv) contains fictional readiness assessments for initiative/control pairs. Assessments report status, owner role, evidence reference, evidence state, and follow-up without redefining policy criticality.

The sample data does not represent a real employer, customer, Salesforce environment, or confidential operational system.
