"""Scoring engine for operational risk review.

The implementation follows the documented Phase 1 scoring model in
``logic/risk_scoring.md``. It intentionally uses transparent business rules
instead of predictive modeling so the same inputs reproduce the same output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


WEIGHTS = {
    "overdue_days": 0.4,
    "handoff_count": 0.3,
    "priority_weight": 0.2,
    "rework_count": 0.1,
}

STABLE_MAX = 30
WATCH_MAX = 60


@dataclass(frozen=True)
class OperationalItem:
    """Structured operational item used by the risk scoring model."""

    item_id: str
    status: str
    overdue_days: int
    handoff_count: int
    priority_weight: int
    rework_count: int

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError("item_id is required")
        if not self.status.strip():
            raise ValueError("status is required")

        for field_name in (
            "overdue_days",
            "handoff_count",
            "priority_weight",
            "rework_count",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "OperationalItem":
        """Create an operational item from a CSV or dictionary row."""

        return cls(
            item_id=str(row["item_id"]).strip(),
            status=str(row["status"]).strip(),
            overdue_days=_to_int(row["overdue_days"], "overdue_days"),
            handoff_count=_to_int(row["handoff_count"], "handoff_count"),
            priority_weight=_to_int(row["priority_weight"], "priority_weight"),
            rework_count=_to_int(row["rework_count"], "rework_count"),
        )


@dataclass(frozen=True)
class RiskEvaluation:
    """Structured risk evaluation result for analysis and reporting."""

    item_id: str
    status: str
    risk_score: float
    classification: str
    signals: dict[str, int]
    score_components: dict[str, float]
    reasons: list[str]
    suggested_review: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the evaluation."""

        return asdict(self)


def _to_int(value: Any, field_name: str) -> int:
    try:
        if isinstance(value, str):
            value = value.strip()
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc


def calculate_score(item: OperationalItem) -> float:
    """Calculate the weighted risk score before reporting rounding."""

    return (
        item.overdue_days * WEIGHTS["overdue_days"]
        + item.handoff_count * WEIGHTS["handoff_count"]
        + item.priority_weight * WEIGHTS["priority_weight"]
        + item.rework_count * WEIGHTS["rework_count"]
    )


def reported_score(item: OperationalItem) -> float:
    """Return the whole-number score used in review tables."""

    return float(round(calculate_score(item)))


def classify_score(score: float) -> str:
    """Classify a risk score using the documented thresholds."""

    if score <= STABLE_MAX:
        return "Stable"
    if score <= WATCH_MAX:
        return "Watch"
    return "At Risk"


def score_components(item: OperationalItem) -> dict[str, float]:
    """Return each weighted contribution to the total risk score."""

    return {
        "overdue_days": item.overdue_days * WEIGHTS["overdue_days"],
        "handoff_count": item.handoff_count * WEIGHTS["handoff_count"],
        "priority_weight": item.priority_weight * WEIGHTS["priority_weight"],
        "rework_count": item.rework_count * WEIGHTS["rework_count"],
    }


def explain_item(item: OperationalItem, classification: str) -> list[str]:
    """Generate reusable reasons based on the item's operational signals."""

    reasons: list[str] = []

    if item.overdue_days >= 90:
        reasons.append(f"Significantly overdue at {item.overdue_days} days")
    elif item.overdue_days > 0:
        reasons.append(f"Overdue by {item.overdue_days} days")

    if item.priority_weight >= 50:
        reasons.append(f"Elevated priority weight of {item.priority_weight}")

    if item.handoff_count >= 5:
        reasons.append(f"Multiple ownership handoffs ({item.handoff_count})")
    elif item.handoff_count > 0:
        reasons.append(f"{item.handoff_count} ownership handoff(s)")

    if item.rework_count >= 5:
        reasons.append(f"Repeated rework or reopening count ({item.rework_count})")
    elif item.rework_count > 0:
        reasons.append(f"{item.rework_count} rework or reopening event(s)")

    if not reasons:
        reasons.append("No elevated operational signals were detected")

    if classification == "At Risk":
        reasons.append("Combined signals meet the at-risk review threshold")
    elif classification == "Watch":
        reasons.append("Combined signals meet the watch review threshold")

    return reasons


def suggested_review_action(classification: str) -> str:
    """Return the review action associated with a classification."""

    if classification == "At Risk":
        return "Confirm ownership, identify blockers, and determine whether escalation is needed"
    if classification == "Watch":
        return "Confirm ownership and monitor during the next review"
    return "Continue normal tracking"


def evaluate_item(item: OperationalItem) -> RiskEvaluation:
    """Evaluate one operational item and return a structured result."""

    score = reported_score(item)
    classification = classify_score(score)

    return RiskEvaluation(
        item_id=item.item_id,
        status=item.status,
        risk_score=score,
        classification=classification,
        signals={
            "overdue_days": item.overdue_days,
            "handoff_count": item.handoff_count,
            "priority_weight": item.priority_weight,
            "rework_count": item.rework_count,
        },
        score_components=score_components(item),
        reasons=explain_item(item, classification),
        suggested_review=suggested_review_action(classification),
    )
