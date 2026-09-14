# Analysis Overview

This directory contains the evaluation workflow used to turn validated operational items into scored review outputs.

[evaluate_operational_risk.py](evaluate_operational_risk.py) reads the validated sample dataset, evaluates each item with the scoring engine, summarizes classification counts, and writes a review summary to the reporting directory.

[analyze_threshold_sensitivity.py](analyze_threshold_sensitivity.py) compares the current thresholds with illustrative earlier/later review scenarios while keeping the scoring model unchanged.

Planned analysis extensions include trend analysis across backlog and handoffs, plus dashboard-style review outputs.
