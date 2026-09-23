"""Build a dashboard-style operational review report from existing analyses."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping

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


def _percentage(count: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{(count / total) * 100:.1f}%"


def _movement_summary(result: ThresholdScenarioResult) -> str:
    changes = result.changes
    if not changes:
        return f"- {result.scenario.name}: no records changed classification."
    if len(changes) == 1:
        change = changes[0]
        return (
            f"- {result.scenario.name}: {change.item_id} moves "
            f"{change.current_classification} -> {change.scenario_classification}."
        )

    joined_changes = ", ".join(
        f"{change.item_id} ({change.change})" for change in changes
    )
    return (
        f"- {result.scenario.name}: {len(changes)} records changed classification: "
        f"{joined_changes}."
    )


def _signal_totals(review_queue: list[RiskEvaluation]) -> Mapping[str, int]:
    overdue_values = [result.signals["overdue_days"] for result in review_queue]
    handoff_values = [result.signals["handoff_count"] for result in review_queue]
    rework_values = [result.signals["rework_count"] for result in review_queue]

    return {
        "overdue_items": sum(1 for value in overdue_values if value > 0),
        "total_overdue_days": sum(overdue_values),
        "total_handoffs": sum(handoff_values),
        "total_rework": sum(rework_values),
        "max_overdue_days": max(overdue_values, default=0),
        "max_handoff_count": max(handoff_values, default=0),
        "max_rework_count": max(rework_values, default=0),
    }


def render_dashboard(
    risk_results: list[RiskEvaluation],
    sensitivity_results: list[ThresholdScenarioResult],
) -> str:
    """Render a consolidated markdown dashboard for operational review."""

    counts = classification_counts(risk_results)
    review_queue = top_review_candidates(risk_results, limit=len(risk_results))
    signal_totals = _signal_totals(review_queue)
    total_items = len(risk_results)
    current_review_volume = _review_volume(counts)

    lines = [
        "# Operational Review Dashboard",
        "",
        "Generated from the fictional sample dataset in `data/validated/sample_operational_items.csv` using the existing scoring and threshold sensitivity workflows.",
        "",
        "## Current Portfolio Snapshot",
        "",
        "| Metric | Count | Share |",
        "| --- | ---: | ---: |",
        f"| Total Items | {total_items} | {_percentage(total_items, total_items)} |",
        f"| Stable | {_count_value(counts, 'Stable')} | {_percentage(_count_value(counts, 'Stable'), total_items)} |",
        f"| Watch | {_count_value(counts, 'Watch')} | {_percentage(_count_value(counts, 'Watch'), total_items)} |",
        f"| At Risk | {_count_value(counts, 'At Risk')} | {_percentage(_count_value(counts, 'At Risk'), total_items)} |",
        f"| Review Queue | {current_review_volume} | {_percentage(current_review_volume, total_items)} |",
    ]

    lines.extend(
        [
            "",
            "## Priority Review Queue",
            "",
            "| Rank | Item ID | Status | Review Score | Exact Score | Classification | Overdue Days | Handoffs | Rework | Suggested Review |",
            "| ---: | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )

    for rank, result in enumerate(review_queue, start=1):
        lines.append(
            f"| {rank} | {result.item_id} | {result.status} | "
            f"{result.review_score} | {result.exact_score} | "
            f"{result.classification} | {result.signals['overdue_days']} | "
            f"{result.signals['handoff_count']} | {result.signals['rework_count']} | "
            f"{result.suggested_review} |"
        )

    lines.extend(
        [
            "",
            "## Signal Snapshot",
            "",
            "The current review queue includes only items classified as Watch or At Risk.",
            "",
            "| Signal | Value |",
            "| --- | ---: |",
            f"| Review queue items with overdue days | {signal_totals['overdue_items']} |",
            f"| Total overdue days across review queue | {signal_totals['total_overdue_days']} |",
            f"| Total handoffs across review queue | {signal_totals['total_handoffs']} |",
            f"| Total rework across review queue | {signal_totals['total_rework']} |",
            f"| Highest overdue-days value | {signal_totals['max_overdue_days']} |",
            f"| Highest handoff count | {signal_totals['max_handoff_count']} |",
            f"| Highest rework count | {signal_totals['max_rework_count']} |",
            "",
            "| Item ID | Overdue Days | Handoffs | Rework | Primary Reason |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )

    for result in review_queue:
        lines.append(
            f"| {result.item_id} | {result.signals['overdue_days']} | "
            f"{result.signals['handoff_count']} | {result.signals['rework_count']} | "
            f"{_primary_reason(result)} |"
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

    lines.extend(
        [
            "",
            "Scenario movement summary:",
            "",
        ]
    )

    for result in sensitivity_results:
        if result.scenario.name == "Current":
            continue
        lines.append(_movement_summary(result))

    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- Scoring is deterministic and follows the documented weighted rule set.",
            "- Threshold values are illustrative and should not be treated as production calibration.",
            "- Source data is fictional and intended for prototype review.",
            "- The dashboard supports prioritization and discussion; human operational judgment is still required.",
            "- Sensitivity scenarios are not recommendations and do not change the default scoring configuration.",
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
        "Current portfolio snapshot: "
        f"At Risk={_count_value(counts, 'At Risk')}, "
        f"Watch={_count_value(counts, 'Watch')}, "
        f"Stable={_count_value(counts, 'Stable')}"
    )
    print(f"Dashboard written to: {DEFAULT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
