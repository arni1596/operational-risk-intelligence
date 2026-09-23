# Shared Task Notes

## 2026-09-11 - Add automated Python validation

### Changed
- Added GitHub Actions CI for pushes and pull requests targeting `main`.
- CI runs the unit test suite on Python 3.11 and 3.12.
- CI also executes the sample operational risk pipeline so workflow-level regressions are caught automatically.

### Why
The repository already had strong local regression coverage, but validation depended on developers remembering to run it manually. Automated CI turns the existing tests and sample pipeline into a repeatable merge gate without changing scoring behavior.

### Verified
- `python -m unittest discover -s tests` -> 22 tests passed locally.
- `python analysis/evaluate_operational_risk.py` -> 8 items evaluated; At Risk=1, Watch=3, Stable=4.

### Next
Consider adding threshold-calibration scenario analysis as a separate feature PR. Keep that work independent from CI so the validation infrastructure remains small and reusable.

## 2026-09-13 - Threshold Sensitivity Analysis

### What changed
- Added a threshold sensitivity analysis workflow with Current, Earlier Review, and Later Review scenarios.
- Generated a reproducible summary showing classification counts and item-level classification changes.
- Added focused tests for scenario definitions, score invariance, deterministic output, and report rendering.

### Why
The scoring pipeline can now show how review volume changes when thresholds move slightly earlier or later, without changing the default scoring model or recommending production threshold changes.

### Verification
- `python -m unittest discover -s tests`
- `python analysis/evaluate_operational_risk.py`
- `python analysis/analyze_threshold_sensitivity.py`

### Next
Add a dashboard-style operational review view that consumes existing generated analysis outputs.

## 2026-09-23 - Operational Review Dashboard

### What changed
- Added a generated markdown dashboard that consolidates current risk results, review queue signal totals, and threshold sensitivity results.
- Added tests for deterministic dashboard rendering, portfolio distribution, review queue membership and ordering, signal totals, and classification movements.
- Extended CI to run the threshold sensitivity and dashboard generation workflows.
- Updated analysis, reporting, and root documentation to reference the dashboard workflow.

### Why
The repository now has separate generated outputs for current risk review and threshold sensitivity. A consolidated dashboard gives reviewers one place to see current review volume, priority candidates, and the practical effect of threshold scenarios without changing the scoring engine.

### Verification
- `python -m unittest discover -s tests`
- `python analysis/evaluate_operational_risk.py`
- `python analysis/analyze_threshold_sensitivity.py`
- `python analysis/build_operational_review_dashboard.py`

### Next
Add machine-readable CSV or JSON exports for generated analysis outputs.
