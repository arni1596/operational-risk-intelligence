# Analysis Overview

This directory contains the evaluation workflow used to turn validated operational items into scored review outputs.

[evaluate_operational_risk.py](evaluate_operational_risk.py) reads the validated sample dataset, evaluates each item with the scoring engine, summarizes classification counts, and writes a review summary to the reporting directory.

[analyze_threshold_sensitivity.py](analyze_threshold_sensitivity.py) compares the current thresholds with illustrative earlier/later review scenarios while keeping the scoring model unchanged.

[build_operational_review_dashboard.py](build_operational_review_dashboard.py) combines the current risk review and threshold sensitivity outputs into a dashboard-style markdown report for operational review.

[evaluate_operational_readiness.py](evaluate_operational_readiness.py) reads the readiness initiative inventory and assessment snapshot, validates referential integrity, evaluates every initiative against the readiness policy, preserves missing controls, ranks initiatives for review, and writes a readiness summary to the reporting directory.

Risk scoring and readiness assurance are intentionally separate workflows. Risk answers what deserves attention; readiness answers which required evidence or controls remain unresolved.
