"""Run a review-ready risk evaluation against validated sample data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from logic.risk_score import OperationalItem, evaluate_item


DEFAULT_INPUT = Path("data/validated/sample_operational_items.csv")


def load_items(path: Path) -> list[OperationalItem]:
    """Load validated operational items from CSV."""

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "item_id",
            "overdue_days",
            "handoff_count",
            "priority_weight",
            "rework_count",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required CSV columns: {sorted(missing)}")
        return [OperationalItem.from_mapping(row) for row in reader]


def build_review(items: list[OperationalItem], top_n: int = 5) -> dict[str, Any]:
    """Evaluate items and produce a compact decision-review summary."""

    results = [evaluate_item(item) for item in items]
    ranked = sorted(results, key=lambda row: row["risk_score"], reverse=True)
    counts = Counter(row["classification"] for row in results)

    return {
        "items_reviewed": len(results),
        "classification_counts": {
            label: counts.get(label, 0)
            for label in ("Stable", "Watch", "At Risk")
        },
        "top_review_candidates": ranked[:top_n],
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate operational items with deterministic risk rules."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Validated CSV input (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of highest-risk items to include as review candidates",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for JSON output; stdout is used when omitted",
    )
    args = parser.parse_args()

    if args.top < 1:
        raise ValueError("--top must be at least 1")

    review = build_review(load_items(args.input), top_n=args.top)
    payload = json.dumps(review, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
