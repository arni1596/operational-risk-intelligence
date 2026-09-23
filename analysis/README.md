# Analysis Overview

This directory contains the evaluation workflow used to turn validated operational items into scored review outputs.

[evaluate_operational_risk.py](evaluate_operational_risk.py) reads the validated sample dataset, evaluates each item with the scoring engine, summarizes classification counts, and writes a review summary to the reporting directory.

[analyze_threshold_sensitivity.py](analyze_threshold_sensitivity.py) compares the current thresholds with illustrative earlier/later review scenarios while keeping the scoring model unchanged.

[build_operational_review_dashboard.py](build_operational_review_dashboard.py) combines the current risk review and threshold sensitivity outputs into a dashboard-style markdown report for operational review.

Planned analysis extensions include trend analysis across backlog and handoffs, plus machine-readable exports for generated outputs.
