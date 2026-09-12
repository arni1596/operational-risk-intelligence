"""Scoring engine for operational risk review.

The implementation follows the documented Phase 1 scoring model in
``logic/risk_scoring.md``. Scoring uses ``Decimal`` arithmetic and explicit
ROUND_HALF_UP review-score rounding so the same validated inputs and
configuration always reproduce the same classification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class RiskScoringConfig:
    """Immutable business configuration for operational risk scoring."""

    overdue_days_weight: Decimal
    handoff_count_weight: Decimal
    priority_weight_weight: Decimal
    rework_count_weight: Decimal
    stable_upper_bound: int
    watch_upper_bound: int

    def __post_init__(self) -> None:
        for field_name in (
            "overdue_days_weight",
            "handoff_count_weight",
            "priority_weight_weight",
            "rework_count_weight",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, Decimal):
                raise TypeError(f"{field_name} must be a Decimal")
            if value < Decimal("0"):
                raise ValueError(f"{field_name} cannot be negative")

        for field_name in ("stable_upper_bound", "watch_upper_bound"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")

        if self.stable_upper_bound >= self.watch_upper_bound:
            raise ValueError("stable_upper_bound must be less than watch_upper_bound")


DEFAULT_RISK_CONFIG = RiskScoringConfig(
    overdue_days_weight=Decimal("0.4"),
    handoff_count_weight=Decimal("0.3"),
    priority_weight_weight=Decimal("0.2"),
    rework_count_weight=Decimal("0.1"),
    stable_upper_bound=30,
    watch_upper_bound=60,
)

# Compatibility constants retained for existing imports and examples.
WEIGHTS = MappingProxyType(
    {
        "overdue_days": DEFAULT_RISK_CONFIG.overdue_days_weight,
        "handoff_count": DEFAULT_RISK_CONFIG.handoff_count_weight,
        "priority_weight": DEFAULT_RISK_CONFIG.priority_weight_weight,
        "rework_count": DEFAULT_RISK_CONFIG.rework_count_weight,
    }
)
STABLE_MAX = DEFAULT_RISK_CONFIG.stable_upper_bound
WATCH_MAX = DEFAULT_RISK_CONFIG.watch_upper_bound


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
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValueError("item_id is required")
        if not isinstance(self.status, str) or not self.status.strip():
            raise ValueError("status is required")

        for field_name in (
            "overdue_days",
            "handoff_count",
            "priority_weight",
            "rework_count",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"{field_name} cannot be negative")

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "OperationalItem":
        """Create an operational item from a validated mapping row."""

        return cls(
            item_id=_required_text(row, "item_id"),
            status=_required_text(row, "status"),
            overdue_days=_to_int(row.get("overdue_days"), "overdue_days"),
            handoff_count=_to_int(row.get("handoff_count"), "handoff_count"),
            priority_weight=_to_int(row.get("priority_weight"), "priority_weight"),
            rework_count=_to_int(row.get("rework_count"), "rework_count"),
        )


@dataclass(frozen=True)
class RiskEvaluation:
    """Structured risk evaluation result for analysis and reporting."""

    item_id: str
    status: str
    exact_score: Decimal
    review_score: int
    classification: str
    signals: dict[str, int]
    score_components: dict[str, Decimal]
    reasons: list[str]
    suggested_review: str
    classification_rule: str
    config: RiskScoringConfig

    @property
    def risk_score(self) -> float:
        """Backward-compatible review score used by existing reports/tests."""

        return float(self.review_score)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the evaluation."""

        data = asdict(self)
        data["exact_score"] = str(self.exact_score)
        data["review_score"] = self.review_score
        data["risk_score"] = self.risk_score
        data["score_components"] = {
            key: str(value) for key, value in self.score_components.items()
        }
        data["config"] = {
            key: str(value) if isinstance(value, Decimal) else value
            for key, value in data["config"].items()
        }
        return data


def _required_text(row: Mapping[str, Any], field_name: str) -> str:
    value = row.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _to_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer")
    if isinstance(value, int):
        if value < 0:
            raise ValueError(f"{field_name} cannot be negative")
        return value
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an integer")

    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} is required")
    if stripped.startswith("-"):
        raise ValueError(f"{field_name} cannot be negative")
    if "." in stripped:
        raise ValueError(f"{field_name} must be a whole-number integer")
    if not stripped.isdigit():
        raise ValueError(f"{field_name} must be a valid integer")

    return int(stripped)


def _to_decimal_int(value: int) -> Decimal:
    return Decimal(value)


def score_components(
    item: OperationalItem,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> dict[str, Decimal]:
    """Return each weighted contribution to the total risk score."""

    return {
        "overdue_days": _to_decimal_int(item.overdue_days)
        * config.overdue_days_weight,
        "handoff_count": _to_decimal_int(item.handoff_count)
        * config.handoff_count_weight,
        "priority_weight": _to_decimal_int(item.priority_weight)
        * config.priority_weight_weight,
        "rework_count": _to_decimal_int(item.rework_count)
        * config.rework_count_weight,
    }


def calculate_exact_score(
    item: OperationalItem,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> Decimal:
    """Calculate the exact weighted risk score with Decimal arithmetic."""

    components = score_components(item, config)
    return sum(components.values(), Decimal("0"))


def calculate_score(
    item: OperationalItem,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> float:
    """Return the exact score as a float for compatibility.

    New audit-oriented code should use ``calculate_exact_score`` so Decimal
    precision is preserved end to end.
    """

    return float(calculate_exact_score(item, config))


def round_review_score(
    exact_score: Decimal,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> int:
    """Round an exact score to the public review score using ROUND_HALF_UP."""

    if not isinstance(exact_score, Decimal):
        raise TypeError("exact_score must be a Decimal")
    rounded = exact_score.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(rounded)


def reported_score(
    item: OperationalItem,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> float:
    """Return the whole-number review score used in review tables."""

    return float(round_review_score(calculate_exact_score(item, config), config))


def classify_score(
    score: int | Decimal | float,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> str:
    """Classify a rounded review score using the documented thresholds."""

    if isinstance(score, bool):
        raise TypeError("score must be numeric")
    if isinstance(score, int):
        review_score = score
    elif isinstance(score, Decimal):
        if score != score.to_integral_value():
            raise ValueError("score must be an integral review score")
        review_score = int(score)
    elif isinstance(score, float):
        if not score.is_integer():
            raise ValueError("score must be an integral review score")
        review_score = int(score)
    else:
        raise TypeError("score must be numeric")

    if review_score < 0:
        raise ValueError("score cannot be negative")

    if review_score <= config.stable_upper_bound:
        return "Stable"
    if review_score <= config.watch_upper_bound:
        return "Watch"
    return "At Risk"


def classification_rule(
    review_score: int,
    classification: str,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> str:
    """Describe the threshold rule that produced a classification."""

    if classification == "Stable":
        return f"review_score <= {config.stable_upper_bound}"
    if classification == "Watch":
        return (
            f"{config.stable_upper_bound + 1} <= review_score <= "
            f"{config.watch_upper_bound}"
        )
    return f"review_score >= {config.watch_upper_bound + 1}"


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


def evaluate_item(
    item: OperationalItem,
    config: RiskScoringConfig = DEFAULT_RISK_CONFIG,
) -> RiskEvaluation:
    """Evaluate one operational item and return a structured result."""

    exact_score = calculate_exact_score(item, config)
    review_score = round_review_score(exact_score, config)
    classification = classify_score(review_score, config)

    return RiskEvaluation(
        item_id=item.item_id,
        status=item.status,
        exact_score=exact_score,
        review_score=review_score,
        classification=classification,
        signals={
            "overdue_days": item.overdue_days,
            "handoff_count": item.handoff_count,
            "priority_weight": item.priority_weight,
            "rework_count": item.rework_count,
        },
        score_components=score_components(item, config),
        reasons=explain_item(item, classification),
        suggested_review=suggested_review_action(classification),
        classification_rule=classification_rule(review_score, classification, config),
        config=config,
    )
