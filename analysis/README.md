# Analysis Overview

This directory contains the evaluation workflow used to turn validated operational items into scored review outputs.

[evaluate_operational_risk.py](evaluate_operational_risk.py) reads the validated sample dataset, evaluates each item with the scoring engine, summarizes classification counts, and writes a review summary to the reporting directory.

Planned analysis extensions include trend analysis across backlog and handoffs, plus retrospective calibration of risk thresholds.
