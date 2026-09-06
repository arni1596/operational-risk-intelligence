"""Evaluate sample operational items and produce review-ready outputs."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logic.risk_score import OperationalItem, RiskEvaluation, evaluate_item


DEFAULT_INPUT = ROOT / "data" / "validated" / "sample_operational_items.csv"
DEFAULT_OUTPUT = ROOT / "reporting" / "risk_review_summary.md"


def load_operational_items(path: Path = DEFAULT_INPUT) -> list[OperationalItem]:
    """Load validated operational items from a CSV file."""

    with path.open(newline="", encoding="utf-8") as csv_file:
        return [OperationalItem.from_mapping(row) for row in csv.DictReader(csv_file)]


def evaluate_dataset(items: list[OperationalItem]) -> list[RiskEvaluation]:
    """Evaluate every item using the operational risk scoring engine."""

    return [evaluate_item(item) for item in items]


def classification_counts(results: list[RiskEvaluation]) -> Counter[str]:
    """Summarize how many items fall into each review classification."""

    return Counter(result.classification for result in results)


def top_review_candidates(
    results: list[RiskEvaluation],
    limit: int = 5,
) -> list[RiskEvaluation]:
    """Return the highest-risk items first for operational review."""

    review_items = [
        result for result in results if result.classification in {"At Risk", "Watch"}
    ]
    return sorted(review_items, key=lambda result: result.risk_score, reverse=True)[
        :limit
    ]


def format_signals(signals: dict[str, int]) -> str:
    """Format signal values for a markdown review note."""

    return (
        f"overdue_days={signals['overdue_days']}, "
        f"handoff_count={signals['handoff_count']}, "
        f"priority_weight={signals['priority_weight']}, "
        f"rework_count={signals['rework_count']}"
    )


def render_markdown_summary(results: list[RiskEvaluation]) -> str:
    """Render evaluation results as a concise operational review summary."""

    counts = classification_counts(results)
    top_items = top_review_candidates(results)

    lines = [
        "# Operational Risk Review Summary",
        "",
        "Generated from the fictional sample dataset in `data/validated/sample_operational_items.csv` using the documented risk-scoring model.",
        "",
        "## Classification Distribution",
        "",
        "| Classification | Count |",
        "| --- | ---: |",
    ]

    for classification in ("At Risk", "Watch", "Stable"):
        lines.append(f"| {classification} | {counts.get(classification, 0)} |")

    lines.extend(
        [
            "",
            "## Top Review Candidates",
            "",
            "| Item ID | Risk Score | Flag | Primary Reason | Suggested Review |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )

    for result in top_items:
        primary_reason = result.reasons[0] if result.reasons else "No reason provided"
        lines.append(
            f"| {result.item_id} | {result.risk_score:.0f} | {result.classification} | "
            f"{primary_reason} | {result.suggested_review} |"
        )

    lines.extend(
        [
            "",
            "## Flag Explanations",
            "",
        ]
    )

    for result in results:
        if result.classification == "Stable":
            continue
        lines.append(f"### {result.item_id}: {result.classification}")
        lines.append("")
        lines.append(f"- Risk score: {result.risk_score:.0f}")
        lines.append(f"- Status: {result.status}")
        lines.append(f"- Signals: {format_signals(result.signals)}")
        lines.append(f"- Reasons: {'; '.join(result.reasons)}")
        lines.append(f"- Suggested review: {result.suggested_review}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_summary(
    results: list[RiskEvaluation],
    path: Path = DEFAULT_OUTPUT,
) -> None:
    """Write the review summary to the reporting directory."""

    path.write_text(render_markdown_summary(results), encoding="utf-8")


def main() -> None:
    """Run the sample operational risk evaluation workflow."""

    items = load_operational_items()
    results = evaluate_dataset(items)
    write_summary(results)

    counts = classification_counts(results)
    print("Operational risk evaluation complete.")
    print(f"Items evaluated: {len(results)}")
    print(
        "Classification distribution: "
        f"At Risk={counts.get('At Risk', 0)}, "
        f"Watch={counts.get('Watch', 0)}, "
        f"Stable={counts.get('Stable', 0)}"
    )
    print(f"Summary written to: {DEFAULT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
