"""Analyze how illustrative threshold changes affect classifications."""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.evaluate_operational_risk import (  # noqa: E402
    classification_counts,
    load_operational_items,
)
from logic.risk_score import (  # noqa: E402
    DEFAULT_RISK_CONFIG,
    OperationalItem,
    RiskEvaluation,
    RiskScoringConfig,
    evaluate_item,
)


DEFAULT_OUTPUT = ROOT / "reporting" / "threshold_sensitivity_summary.md"


@dataclass(frozen=True)
class ThresholdScenario:
    """Illustrative threshold scenario for sensitivity analysis."""

    name: str
    description: str
    config: RiskScoringConfig


@dataclass(frozen=True)
class ClassificationChange:
    """Classification movement for one item under a threshold scenario."""

    item_id: str
    review_score: int
    current_classification: str
    scenario_classification: str
    change: str


@dataclass(frozen=True)
class ThresholdScenarioResult:
    """Evaluated results for one threshold scenario."""

    scenario: ThresholdScenario
    evaluations: list[RiskEvaluation]
    counts: Counter[str]
    changes: list[ClassificationChange]


def _config_with_thresholds(
    stable_upper_bound: int,
    watch_upper_bound: int,
) -> RiskScoringConfig:
    """Copy default scoring weights while changing only review thresholds."""

    return RiskScoringConfig(
        overdue_days_weight=DEFAULT_RISK_CONFIG.overdue_days_weight,
        handoff_count_weight=DEFAULT_RISK_CONFIG.handoff_count_weight,
        priority_weight_weight=DEFAULT_RISK_CONFIG.priority_weight_weight,
        rework_count_weight=DEFAULT_RISK_CONFIG.rework_count_weight,
        stable_upper_bound=stable_upper_bound,
        watch_upper_bound=watch_upper_bound,
    )


SCENARIOS = (
    ThresholdScenario(
        name="Current",
        description="Existing default review thresholds.",
        config=DEFAULT_RISK_CONFIG,
    ),
    ThresholdScenario(
        name="Earlier Review",
        description="Illustrative scenario where items enter review classifications earlier.",
        config=_config_with_thresholds(stable_upper_bound=25, watch_upper_bound=55),
    ),
    ThresholdScenario(
        name="Later Review",
        description="Illustrative scenario where items enter review classifications later.",
        config=_config_with_thresholds(stable_upper_bound=35, watch_upper_bound=65),
    ),
)


def evaluate_scenario(
    items: Iterable[OperationalItem],
    scenario: ThresholdScenario,
) -> list[RiskEvaluation]:
    """Evaluate operational items under one threshold scenario."""

    return [evaluate_item(item, scenario.config) for item in items]


def compare_to_current(
    current_results: list[RiskEvaluation],
    scenario_results: list[RiskEvaluation],
) -> list[ClassificationChange]:
    """Identify classification changes compared with the current thresholds."""

    current_by_item = {result.item_id: result for result in current_results}
    changes: list[ClassificationChange] = []

    for scenario_result in scenario_results:
        current_result = current_by_item[scenario_result.item_id]
        if current_result.classification == scenario_result.classification:
            continue
        changes.append(
            ClassificationChange(
                item_id=scenario_result.item_id,
                review_score=scenario_result.review_score,
                current_classification=current_result.classification,
                scenario_classification=scenario_result.classification,
                change=(
                    f"{current_result.classification} -> "
                    f"{scenario_result.classification}"
                ),
            )
        )

    return sorted(changes, key=lambda change: change.item_id)


def analyze_threshold_sensitivity(
    items: Iterable[OperationalItem],
    scenarios: tuple[ThresholdScenario, ...] = SCENARIOS,
) -> list[ThresholdScenarioResult]:
    """Evaluate all sensitivity scenarios and compare with Current."""

    item_list = list(items)
    evaluations_by_name = {
        scenario.name: evaluate_scenario(item_list, scenario) for scenario in scenarios
    }
    current_results = evaluations_by_name["Current"]

    return [
        ThresholdScenarioResult(
            scenario=scenario,
            evaluations=evaluations_by_name[scenario.name],
            counts=classification_counts(evaluations_by_name[scenario.name]),
            changes=[]
            if scenario.name == "Current"
            else compare_to_current(
                current_results,
                evaluations_by_name[scenario.name],
            ),
        )
        for scenario in scenarios
    ]


def _count_value(counts: Counter[str], classification: str) -> int:
    return counts.get(classification, 0)


def render_markdown_summary(results: list[ThresholdScenarioResult]) -> str:
    """Render threshold sensitivity results as a reproducible markdown report."""

    lines = [
        "# Threshold Sensitivity Analysis",
        "",
        "## Purpose",
        "",
        "This report tests how illustrative threshold changes affect review classifications for the fictional sample dataset. It does not recommend changing the default thresholds and does not represent production calibration.",
        "",
        "## Scenario Definitions",
        "",
        "| Scenario | Stable Upper Bound | Watch Upper Bound | Purpose |",
        "| --- | ---: | ---: | --- |",
    ]

    for result in results:
        scenario = result.scenario
        lines.append(
            f"| {scenario.name} | {scenario.config.stable_upper_bound} | "
            f"{scenario.config.watch_upper_bound} | {scenario.description} |"
        )

    lines.extend(
        [
            "",
            "## Classification Distribution",
            "",
            "| Scenario | Stable | Watch | At Risk |",
            "| --- | ---: | ---: | ---: |",
        ]
    )

    for result in results:
        lines.append(
            f"| {result.scenario.name} | "
            f"{_count_value(result.counts, 'Stable')} | "
            f"{_count_value(result.counts, 'Watch')} | "
            f"{_count_value(result.counts, 'At Risk')} |"
        )

    lines.extend(["", "## Classification Changes", ""])

    for result in results:
        if result.scenario.name == "Current":
            continue
        lines.append(f"### {result.scenario.name}")
        lines.append("")
        if not result.changes:
            lines.append("No records changed classification under this scenario.")
            lines.append("")
            continue
        lines.extend(
            [
                "| Item ID | Review Score | Current | Scenario | Change |",
                "| --- | ---: | --- | --- | --- |",
            ]
        )
        for change in result.changes:
            lines.append(
                f"| {change.item_id} | {change.review_score} | "
                f"{change.current_classification} | "
                f"{change.scenario_classification} | {change.change} |"
            )
        lines.append("")

    result_by_name = {result.scenario.name: result for result in results}
    earlier_changes = result_by_name["Earlier Review"].changes
    later_changes = result_by_name["Later Review"].changes
    earlier_review_volume = (
        _count_value(result_by_name["Earlier Review"].counts, "Watch")
        + _count_value(result_by_name["Earlier Review"].counts, "At Risk")
    )
    current_review_volume = (
        _count_value(result_by_name["Current"].counts, "Watch")
        + _count_value(result_by_name["Current"].counts, "At Risk")
    )
    later_review_volume = (
        _count_value(result_by_name["Later Review"].counts, "Watch")
        + _count_value(result_by_name["Later Review"].counts, "At Risk")
    )

    lines.extend(
        [
            "## Interpretation",
            "",
            f"- Earlier Review changes {len(earlier_changes)} record(s) compared with Current and moves review volume from {current_review_volume} to {earlier_review_volume}.",
            f"- Later Review changes {len(later_changes)} record(s) compared with Current and moves review volume from {current_review_volume} to {later_review_volume}.",
            "- These scenarios vary classification thresholds only; exact scores and review scores are unchanged for each operational item.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def write_summary(
    results: list[ThresholdScenarioResult],
    path: Path = DEFAULT_OUTPUT,
) -> None:
    """Write threshold sensitivity results to the reporting directory."""

    path.write_text(render_markdown_summary(results), encoding="utf-8")


def main() -> None:
    """Run threshold sensitivity analysis for the sample operational dataset."""

    items = load_operational_items()
    results = analyze_threshold_sensitivity(items)
    write_summary(results)

    print("Threshold sensitivity analysis complete.")
    for result in results:
        print(
            f"{result.scenario.name}: "
            f"Stable={_count_value(result.counts, 'Stable')}, "
            f"Watch={_count_value(result.counts, 'Watch')}, "
            f"At Risk={_count_value(result.counts, 'At Risk')}"
        )
    print(f"Summary written to: {DEFAULT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
