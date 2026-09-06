"""Deterministic operational risk scoring engine.

This module implements the Phase 1 scoring model documented in
``logic/risk_scoring.md``. It supports explainable decision support and human
review; it does not automate operational outcomes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from numbers import Real
from typing import Any, Mapping


WEIGHTS = {
    "overdue_days": 0.4,
    "handoff_count": 0.3,
    "priority_weight": 0.2,
    "rework_count": 0.1,
}


@dataclass(frozen=True)
class OperationalItem:
    """Structured operational signals used by the deterministic scoring model."""

    item_id: str
    overdue_days: float
    handoff_count: float
    priority_weight: float
    rework_count: float

    def __post_init__(self) -> None:
        if not self.item_id or not self.item_id.strip():
            raise ValueError("item_id must be a non-empty string")

        for field_name in WEIGHTS:
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{field_name} must be numeric")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "OperationalItem":
        """Create an item from CSV-like string or numeric values."""

        return cls(
            item_id=str(row["item_id"]).strip(),
            overdue_days=float(row["overdue_days"]),
            handoff_count=float(row["handoff_count"]),
            priority_weight=float(row["priority_weight"]),
            rework_count=float(row["rework_count"]),
        )


def calculate_contributions(item: OperationalItem) -> dict[str, float]:
    """Return the weighted contribution of each signal to the total score."""

    return {
        signal: round(float(getattr(item, signal)) * weight, 2)
        for signal, weight in WEIGHTS.items()
    }


def calculate_risk_score(item: OperationalItem) -> float:
    """Calculate the documented deterministic risk score."""

    score = sum(
        float(getattr(item, signal)) * weight
        for signal, weight in WEIGHTS.items()
    )
    return round(score, 2)


def classify_risk(score: float) -> str:
    """Translate a non-negative score into its documented review label."""

    if isinstance(score, bool) or not isinstance(score, Real):
        raise TypeError("score must be numeric")
    if score < 0:
        raise ValueError("score cannot be negative")

    if score >= 61:
        return "At Risk"
    if score >= 31:
        return "Watch"
    return "Stable"


def explain_contributions(contributions: Mapping[str, float]) -> list[str]:
    """Create traceable explanations directly from weighted contributions."""

    labels = {
        "overdue_days": "Overdue days",
        "handoff_count": "Ownership handoffs",
        "priority_weight": "Priority weight",
        "rework_count": "Rework",
    }

    reasons = [
        f"{labels[signal]} weighted contribution: {points:g}"
        for signal, points in contributions.items()
        if points > 0
    ]
    return reasons or ["No weighted risk contribution from the current signals"]


def evaluate_item(item: OperationalItem) -> dict[str, Any]:
    """Evaluate one item and return an auditable, reporting-ready result."""

    contributions = calculate_contributions(item)
    score = calculate_risk_score(item)

    return {
        "item_id": item.item_id,
        "risk_score": score,
        "classification": classify_risk(score),
        "signals": asdict(item),
        "contributions": contributions,
        "reasons": explain_contributions(contributions),
    }
