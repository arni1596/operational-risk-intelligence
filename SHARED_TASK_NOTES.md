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
