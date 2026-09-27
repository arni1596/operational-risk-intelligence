# Reporting Overview

This directory contains review-ready outputs produced from analysis.

Primary artifacts include:
- One-page decision briefs
- Risk summaries designed for leadership review
- Escalation-focused dashboard-style reporting

[risk_review_summary.md](risk_review_summary.md) is generated from the synthetic validated sample dataset and shows classification distribution, top review candidates, and reasons surfaced for flagged items.

[threshold_sensitivity_summary.md](threshold_sensitivity_summary.md) is generated from threshold sensitivity analysis and shows how illustrative threshold shifts affect classification volume and item-level movement.

[operational_review_dashboard.md](operational_review_dashboard.md) is generated from existing risk and threshold sensitivity workflows and consolidates current review volume, priority review candidates, and classification movement.

[operational_readiness_summary.md](operational_readiness_summary.md) is generated from the readiness policy, initiative inventory, and assessment snapshot. It summarizes readiness decisions, unresolved blocking and advisory controls, evidence coverage context, and decision traces for human review.

Generated reports are committed outputs. Authoritative changes should be made in renderer or source logic, then regenerated through the analysis scripts rather than edited manually. Regression tests and CI verify that protected generated artifacts stay synchronized with their renderers.

Reports prioritize clarity and actionability over visual complexity.
