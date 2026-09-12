"""Evaluate sample operational items and produce review-ready outputs."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logic.risk_score import (  # noqa: E402
    DEFAULT_RISK_CONFIG,
    OperationalItem,
    RiskEvaluation,
    RiskScoringConfig,
    evaluate_item,
)


DEFAULT_INPUT = ROOT / "data" / "validated" / "sample_operational_items.csv"
DEFAULT_OUTPUT = ROOT / "reporting" / "risk_review_summary.md"
REQUIRED_COLUMNS = {
    "item_id",
    "status",
    "priority_weight",
    "overdue_days",
    "handoff_count",
    "rework_count",
}


class CsvValidationError(ValueError):
    """Raised when a CSV file does not match the expected operational schema."""


def validate_headers(fieldnames: list[str] | None, path: Path) -> None:
    """Verify the CSV contains every required operational-item column."""

    if fieldnames is None:
        raise CsvValidationError(f"{path} is empty or missing a header row")

    duplicate_columns = sorted(
        {field_name for field_name in fieldnames if fieldnames.count(field_name) > 1}
    )
    duplicate_required_columns = [
        field_name for field_name in duplicate_columns if field_name in REQUIRED_COLUMNS
    ]
    if duplicate_required_columns:
        joined = ", ".join(duplicate_required_columns)
        raise CsvValidationError(
            f"{path} contains duplicate required column(s): {joined}"
        )

    missing_columns = sorted(REQUIRED_COLUMNS.difference(fieldnames))
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise CsvValidationError(f"{path} is missing required column(s): {joined}")


def load_operational_items(path: Path = DEFAULT_INPUT) -> list[OperationalItem]:
    """Load and validate operational items from a CSV file."""

    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        validate_headers(reader.fieldnames, path)

        items: list[OperationalItem] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                items.append(OperationalItem.from_mapping(row))
            except (TypeError, ValueError) as exc:
                item_id = row.get("item_id") or "<missing item_id>"
                raise CsvValidationError(
                    f"{path} row {row_number} ({item_id}): {exc}"
                ) from exc

    return items


def evaluate_dataset(
    items: Iterable[OperationalItem],
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> list[RiskEvaluation]:
    """Evaluate every item using the operational risk scoring engine."""

    return [evaluate_item(item, config) for item in items]


def classification_counts(results: Iterable[RiskEvaluation]) -> Counter[str]:
    """Summarize how many items fall into each review classification."""

    return Counter(result.classification for result in results)


def top_review_candidates(
    results: Iterable[RiskEvaluation],
    limit: int = 5,
) -> list[RiskEvaluation]:
    """Return the highest-risk Watch/At Risk items first for review."""

    review_items = [
        result for result in results if result.classification in {"At Risk", "Watch"}
    ]
    return sorted(
        review_items,
        key=lambda result: (-result.review_score, -result.exact_score, result.item_id),
    )[:limit]


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
            "| Item ID | Review Score | Exact Score | Flag | Primary Reason | Suggested Review |",
            "| --- | ---: | ---: | --- | --- | --- |",
        ]
    )

    for result in top_items:
        primary_reason = result.reasons[0] if result.reasons else "No reason provided"
        lines.append(
            f"| {result.item_id} | {result.review_score} | {result.exact_score} | "
            f"{result.classification} | {primary_reason} | {result.suggested_review} |"
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
        lines.append(f"- Exact score: {result.exact_score}")
        lines.append(f"- Review score: {result.review_score}")
        lines.append(f"- Classification rule: `{result.classification_rule}`")
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
