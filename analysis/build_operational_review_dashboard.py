"""Build a dashboard-style operational review report from existing analyses."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.analyze_threshold_sensitivity import (  # noqa: E402
    ThresholdScenarioResult,
    analyze_threshold_sensitivity,
)
from analysis.evaluate_operational_risk import (  # noqa: E402
    classification_counts,
    evaluate_dataset,
    load_operational_items,
    top_review_candidates,
)
from logic.risk_score import RiskEvaluation  # noqa: E402


DEFAULT_OUTPUT = ROOT / "reporting" / "operational_review_dashboard.md"


def _count_value(counts: dict[str, int], classification: str) -> int:
    return counts.get(classification, 0)


def _primary_reason(result: RiskEvaluation) -> str:
    return result.reasons[0] if result.reasons else "No reason provided"


def _review_volume(counts: dict[str, int]) -> int:
    return _count_value(counts, "Watch") + _count_value(counts, "At Risk")


def render_dashboard(
    risk_results: list[RiskEvaluation],
    sensitivity_results: list[ThresholdScenarioResult],
) -> str:
    """Render a consolidated markdown dashboard for operational review."""

    counts = classification_counts(risk_results)
    top_items = top_review_candidates(risk_results, limit=5)
    sensitivity_by_name = {
        result.scenario.name: result for result in sensitivity_results
    }
    current_review_volume = _review_volume(counts)

    lines = [
        "# Operational Review Dashboard",
        "",
        "Generated from the fictional sample dataset in `data/validated/sample_operational_items.csv` using the existing scoring and threshold sensitivity workflows.",
        "",
        "## Current Risk Snapshot",
        "",
        "| Classification | Count |",
        "| --- | ---: |",
    ]

    for classification in ("At Risk", "Watch", "Stable"):
        lines.append(f"| {classification} | {_count_value(counts, classification)} |")

    lines.extend(
        [
            "",
            f"Current review volume: {current_review_volume} item(s) classified as Watch or At Risk.",
            "",
            "## Priority Review Queue",
            "",
            "| Item ID | Status | Review Score | Exact Score | Flag | Primary Reason | Suggested Review |",
            "| --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )

    for result in top_items:
        lines.append(
            f"| {result.item_id} | {result.status} | {result.review_score} | "
            f"{result.exact_score} | {result.classification} | "
            f"{_primary_reason(result)} | {result.suggested_review} |"
        )

    lines.extend(
        [
            "",
            "## Threshold Sensitivity Snapshot",
            "",
            "| Scenario | Stable | Watch | At Risk | Review Volume |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )

    for result in sensitivity_results:
        stable_count = _count_value(result.counts, "Stable")
        watch_count = _count_value(result.counts, "Watch")
        at_risk_count = _count_value(result.counts, "At Risk")
        lines.append(
            f"| {result.scenario.name} | {stable_count} | {watch_count} | "
            f"{at_risk_count} | {watch_count + at_risk_count} |"
        )

    lines.extend(
        [
            "",
            "## Classification Movement",
            "",
            "| Scenario | Item ID | Review Score | Current | Scenario | Change |",
            "| --- | --- | ---: | --- | --- | --- |",
        ]
    )

    movement_rows = 0
    for result in sensitivity_results:
        if result.scenario.name == "Current":
            continue
        for change in result.changes:
            movement_rows += 1
            lines.append(
                f"| {result.scenario.name} | {change.item_id} | "
                f"{change.review_score} | {change.current_classification} | "
                f"{change.scenario_classification} | {change.change} |"
            )

    if movement_rows == 0:
        lines.append("| No scenario | No item | 0 | No change | No change | No movement |")

    at_risk_count = _count_value(counts, "At Risk")
    earlier_review_volume = _review_volume(sensitivity_by_name["Earlier Review"].counts)
    later_review_volume = _review_volume(sensitivity_by_name["Later Review"].counts)

    lines.extend(
        [
            "",
            "## Review Focus",
            "",
            f"- {at_risk_count} item(s) currently meet the At Risk threshold.",
            f"- The Earlier Review scenario moves review volume from {current_review_volume} to {earlier_review_volume} item(s).",
            f"- The Later Review scenario keeps review volume at {later_review_volume} item(s), but changes the classification for OPS-1042.",
            "- Scenario results are for threshold sensitivity review only; they do not change the default scoring configuration.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def write_dashboard(
    risk_results: list[RiskEvaluation],
    sensitivity_results: list[ThresholdScenarioResult],
    path: Path = DEFAULT_OUTPUT,
) -> None:
    """Write the consolidated dashboard report to the reporting directory."""

    path.write_text(
        render_dashboard(risk_results, sensitivity_results),
        encoding="utf-8",
    )


def main() -> None:
    """Run the dashboard report build from the sample operational dataset."""

    items = load_operational_items()
    risk_results = evaluate_dataset(items)
    sensitivity_results = analyze_threshold_sensitivity(items)
    write_dashboard(risk_results, sensitivity_results)

    counts = classification_counts(risk_results)
    print("Operational review dashboard complete.")
    print(
        "Current risk snapshot: "
        f"At Risk={_count_value(counts, 'At Risk')}, "
        f"Watch={_count_value(counts, 'Watch')}, "
        f"Stable={_count_value(counts, 'Stable')}"
    )
    print(f"Dashboard written to: {DEFAULT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
