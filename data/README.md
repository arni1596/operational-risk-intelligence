# Data Overview

This directory separates operational data by processing stage.

- `raw/`: source data as received, unchanged
- `validated/`: cleaned and normalized data used for analysis

Data separation is intentional to preserve traceability and auditability.

## Synthetic Demonstration Data

`validated/sample_operational_items.csv` is a fictional dataset created only to demonstrate the scoring and review workflow. It does not contain employer, customer, Salesforce, or other real operational data.

The sample includes Stable, Watch, and At Risk cases so the deterministic rules can be exercised consistently in tests and demonstrations.
