"""Evaluate synthetic initiatives against the readiness assurance policy."""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logic.readiness_gate import (  # noqa: E402
    DEFAULT_READINESS_POLICY,
    AssessmentStatus,
    Criticality,
    EvidenceState,
    ReadinessAssessment,
    ReadinessDecision,
    ReadinessEvaluation,
    ReadinessInitiative,
    ReadinessPolicy,
    evaluate_readiness,
)


DEFAULT_INITIATIVES_INPUT = (
    ROOT / "data" / "validated" / "sample_readiness_initiatives.csv"
)
DEFAULT_ASSESSMENTS_INPUT = (
    ROOT / "data" / "validated" / "sample_readiness_assessments.csv"
)
DEFAULT_OUTPUT = ROOT / "reporting" / "operational_readiness_summary.md"

INITIATIVE_REQUIRED_COLUMNS = {"initiative_id", "initiative_name"}
ASSESSMENT_REQUIRED_COLUMNS = {
    "initiative_id",
    "control_id",
    "status",
    "owner_role",
    "evidence_ref",
    "evidence_state",
    "follow_up",
}


class ReadinessCsvValidationError(ValueError):
    """Raised when readiness CSV input fails schema or integrity validation."""


def validate_headers(
    fieldnames: list[str] | None,
    path: Path,
    required_columns: set[str],
) -> None:
    if fieldnames is None:
        raise ReadinessCsvValidationError(f"{path} is empty or missing a header row")

    duplicate_columns = sorted(
        {field_name for field_name in fieldnames if fieldnames.count(field_name) > 1}
    )
    duplicate_required_columns = [
        field_name for field_name in duplicate_columns if field_name in required_columns
    ]
    if duplicate_required_columns:
        joined = ", ".join(duplicate_required_columns)
        raise ReadinessCsvValidationError(
            f"{path} contains duplicate required column(s): {joined}"
        )

    missing_columns = sorted(required_columns.difference(fieldnames))
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ReadinessCsvValidationError(f"{path} is missing required column(s): {joined}")


def load_readiness_initiatives(
    path: Path = DEFAULT_INITIATIVES_INPUT,
) -> list[ReadinessInitiative]:
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        validate_headers(reader.fieldnames, path, INITIATIVE_REQUIRED_COLUMNS)

        initiatives: list[ReadinessInitiative] = []
        seen_rows: dict[str, int] = {}
        for row_number, row in enumerate(reader, start=2):
            try:
                initiative = ReadinessInitiative(
                    initiative_id=row.get("initiative_id", ""),
                    initiative_name=row.get("initiative_name", ""),
                    description=row.get("description", ""),
                )
            except (TypeError, ValueError) as exc:
                initiative_id = row.get("initiative_id") or "<missing initiative_id>"
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number} ({initiative_id}): {exc}"
                ) from exc

            first_seen_row = seen_rows.get(initiative.initiative_id)
            if first_seen_row is not None:
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number} ({initiative.initiative_id}): "
                    f"duplicate initiative_id; first seen at row {first_seen_row}"
                )
            seen_rows[initiative.initiative_id] = row_number
            initiatives.append(initiative)

    return initiatives


def load_readiness_assessments(
    initiatives: Iterable[ReadinessInitiative],
    path: Path = DEFAULT_ASSESSMENTS_INPUT,
    policy: ReadinessPolicy = DEFAULT_READINESS_POLICY,
) -> list[ReadinessAssessment]:
    initiative_ids = {initiative.initiative_id for initiative in initiatives}
    control_ids = set(policy.controls_by_id)

    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        validate_headers(reader.fieldnames, path, ASSESSMENT_REQUIRED_COLUMNS)

        assessments: list[ReadinessAssessment] = []
        seen_rows: dict[tuple[str, str], int] = {}
        for row_number, row in enumerate(reader, start=2):
            raw_initiative_id = (row.get("initiative_id") or "").strip()
            raw_control_id = (row.get("control_id") or "").strip()
            if not raw_initiative_id:
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number}: initiative_id is required"
                )
            if not raw_control_id:
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number} ({raw_initiative_id}): control_id is required"
                )
            if raw_initiative_id not in initiative_ids:
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number} ({raw_initiative_id}): unknown initiative_id"
                )
            if raw_control_id not in control_ids:
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number} ({raw_initiative_id}/{raw_control_id}): unknown control_id"
                )

            key = (raw_initiative_id, raw_control_id)
            first_seen_row = seen_rows.get(key)
            if first_seen_row is not None:
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number} ({raw_initiative_id}/{raw_control_id}): "
                    f"duplicate assessment; first seen at row {first_seen_row}"
                )

            try:
                assessment = ReadinessAssessment(
                    initiative_id=raw_initiative_id,
                    control_id=raw_control_id,
                    status=row.get("status", ""),
                    owner_role=row.get("owner_role", ""),
                    evidence_ref=row.get("evidence_ref", ""),
                    evidence_state=row.get("evidence_state", ""),
                    follow_up=row.get("follow_up", ""),
                )
            except (TypeError, ValueError) as exc:
                raise ReadinessCsvValidationError(
                    f"{path} row {row_number} ({raw_initiative_id}/{raw_control_id}): {exc}"
                ) from exc

            seen_rows[key] = row_number
            assessments.append(assessment)

    return assessments


def evaluate_readiness_dataset(
    initiatives: Iterable[ReadinessInitiative],
    assessments: Iterable[ReadinessAssessment],
    policy: ReadinessPolicy = DEFAULT_READINESS_POLICY,
) -> list[ReadinessEvaluation]:
    assessment_list = tuple(assessments)
    return [
        evaluate_readiness(initiative, policy, assessment_list)
        for initiative in sorted(initiatives, key=lambda item: item.initiative_id)
    ]


def decision_counts(evaluations: Iterable[ReadinessEvaluation]) -> Counter[ReadinessDecision]:
    return Counter(evaluation.decision for evaluation in evaluations)


def review_queue(evaluations: Iterable[ReadinessEvaluation]) -> list[ReadinessEvaluation]:
    decision_rank = {
        ReadinessDecision.BLOCKED: 0,
        ReadinessDecision.NEEDS_REVIEW: 1,
        ReadinessDecision.READY_WITH_FOLLOW_UP: 2,
        ReadinessDecision.READY: 3,
    }

    return sorted(
        evaluations,
        key=lambda item: (
            decision_rank[item.decision],
            -len(item.blocking_failures),
            -len(item.blocking_unknowns),
            -len(item.blocking_missing),
            -len(item.unresolved_control_ids),
            item.initiative_id,
        ),
    )


def unresolved_advisory_count(evaluation: ReadinessEvaluation) -> int:
    return (
        len(evaluation.advisory_failures)
        + len(evaluation.advisory_unknowns)
        + len(evaluation.advisory_missing)
    )


def next_review_focus(evaluation: ReadinessEvaluation) -> str:
    if evaluation.decision == ReadinessDecision.BLOCKED:
        base = "Resolve blocking failed controls before readiness can advance."
    elif evaluation.decision == ReadinessDecision.NEEDS_REVIEW:
        base = "Resolve blocking unknown or missing controls and capture current evidence."
    elif evaluation.decision == ReadinessDecision.READY_WITH_FOLLOW_UP:
        base = "Track advisory unresolved controls while preserving blocking-control evidence."
    else:
        base = "No unresolved controls in the modeled readiness policy."

    if evaluation.unresolved_control_ids:
        return f"{base} Focus: {', '.join(evaluation.unresolved_control_ids)}."
    return base


def render_markdown_summary(evaluations: list[ReadinessEvaluation]) -> str:
    counts = decision_counts(evaluations)
    queue = review_queue(evaluations)

    lines = [
        "# Operational Readiness Assurance",
        "",
        "Generated from fictional readiness inputs using the explicit readiness policy in `logic/readiness_gate.py`.",
        "",
        "## Decision Summary",
        "",
        "| Decision | Count |",
        "| --- | ---: |",
    ]

    for decision in (
        ReadinessDecision.READY,
        ReadinessDecision.READY_WITH_FOLLOW_UP,
        ReadinessDecision.NEEDS_REVIEW,
        ReadinessDecision.BLOCKED,
    ):
        lines.append(f"| {decision.value} | {counts.get(decision, 0)} |")

    lines.extend(
        [
            "",
            "## Review Queue",
            "",
            "| Rank | Initiative | Decision | Blocking Failures | Blocking Unknowns | Blocking Missing | Advisory Follow-Ups | Current Evidence | Next Review Focus |",
            "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )

    for rank, evaluation in enumerate(queue, start=1):
        lines.append(
            f"| {rank} | {evaluation.initiative_id} | {evaluation.decision.value} | "
            f"{len(evaluation.blocking_failures)} | {len(evaluation.blocking_unknowns)} | "
            f"{len(evaluation.blocking_missing)} | {unresolved_advisory_count(evaluation)} | "
            f"{evaluation.current_evidence_count}/{evaluation.expected_control_count} "
            f"({evaluation.evidence_coverage_percentage}) | {next_review_focus(evaluation)} |"
        )

    lines.extend(["", "## Blocking Issues", ""])
    blocking_rows = [
        (evaluation, trace)
        for evaluation in queue
        for trace in evaluation.control_traces
        if trace.criticality == Criticality.BLOCKING
        and trace.assessment_state == AssessmentStatus.FAIL
    ]
    if blocking_rows:
        lines.extend(
            [
                "| Initiative | Control | Area | Status | Evidence State | Owner Role | Evidence Ref | Follow-Up |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for evaluation, trace in blocking_rows:
            lines.append(
                f"| {evaluation.initiative_id} | {trace.control_id} | {trace.control_area.value} | "
                f"{trace.assessment_state.value if trace.assessment_state else 'MISSING'} | "
                f"{trace.evidence_state.value if trace.evidence_state else 'MISSING'} | "
                f"{trace.owner_role or 'Not provided'} | {trace.evidence_ref or 'Not provided'} | "
                f"{trace.follow_up or 'Not provided'} |"
            )
    else:
        lines.append("No blocking failures are present in the current sample.")

    lines.extend(["", "## Unknown And Missing Controls", ""])
    unresolved_rows = [
        (evaluation, trace)
        for evaluation in queue
        for trace in evaluation.control_traces
        if trace.assessment_state == AssessmentStatus.UNKNOWN
        or trace.assessment_state is None
    ]
    if unresolved_rows:
        lines.extend(
            [
                "| Initiative | Control | Criticality | Assessment | Evidence State | Owner Role | Follow-Up |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for evaluation, trace in unresolved_rows:
            assessment_state = (
                trace.assessment_state.value if trace.assessment_state else "MISSING"
            )
            evidence_state = trace.evidence_state.value if trace.evidence_state else "MISSING"
            lines.append(
                f"| {evaluation.initiative_id} | {trace.control_id} | {trace.criticality.value} | "
                f"{assessment_state} | {evidence_state} | {trace.owner_role or 'Not provided'} | "
                f"{trace.follow_up or 'Not provided'} |"
            )
    else:
        lines.append("No unknown or missing controls are present in the current sample.")

    lines.extend(["", "## Advisory Follow-Up", ""])
    advisory_rows = [
        (evaluation, trace)
        for evaluation in queue
        for trace in evaluation.control_traces
        if trace.criticality == Criticality.ADVISORY and not trace.is_resolved
    ]
    if advisory_rows:
        lines.extend(
            [
                "| Initiative | Control | Status | Evidence State | Owner Role | Follow-Up |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for evaluation, trace in advisory_rows:
            lines.append(
                f"| {evaluation.initiative_id} | {trace.control_id} | "
                f"{trace.assessment_state.value if trace.assessment_state else 'MISSING'} | "
                f"{trace.evidence_state.value if trace.evidence_state else 'MISSING'} | "
                f"{trace.owner_role or 'Not provided'} | {trace.follow_up or 'Not provided'} |"
            )
    else:
        lines.append("No advisory follow-up is present in the current sample.")

    lines.extend(
        [
            "",
            "## Evidence Coverage",
            "",
            "Evidence coverage is descriptive context, not a readiness score.",
            "",
            "| Initiative | Current Evidence | Evidence Coverage | Decision |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for evaluation in sorted(evaluations, key=lambda item: item.initiative_id):
        lines.append(
            f"| {evaluation.initiative_id} | "
            f"{evaluation.current_evidence_count}/{evaluation.expected_control_count} | "
            f"{evaluation.evidence_coverage_percentage} | {evaluation.decision.value} |"
        )

    lines.extend(["", "## Initiative Detail", ""])
    for evaluation in sorted(evaluations, key=lambda item: item.initiative_id):
        lines.extend(
            [
                f"### {evaluation.initiative_id}: {evaluation.initiative_name}",
                "",
                f"- Final decision: {evaluation.decision.value}",
                f"- Decision rule: {evaluation.decision_rule}",
                f"- Decision basis: {evaluation.decision_basis}",
                f"- Expected controls: {evaluation.expected_control_count}",
                f"- Assessed controls: {evaluation.assessed_control_count}",
                f"- Unresolved controls: {len(evaluation.unresolved_control_ids)}",
                f"- Evidence coverage: {evaluation.current_evidence_count}/{evaluation.expected_control_count} ({evaluation.evidence_coverage_percentage})",
                "",
            ]
        )
        if evaluation.unresolved_control_ids:
            lines.extend(
                [
                    "| Control | Criticality | Assessment | Evidence State | Owner Role | Follow-Up | Decision Effect |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                ]
            )
            for trace in evaluation.control_traces:
                if trace.control_id not in evaluation.unresolved_control_ids:
                    continue
                lines.append(
                    f"| {trace.control_id} | {trace.criticality.value} | "
                    f"{trace.assessment_state.value if trace.assessment_state else 'MISSING'} | "
                    f"{trace.evidence_state.value if trace.evidence_state else 'MISSING'} | "
                    f"{trace.owner_role or 'Not provided'} | {trace.follow_up or 'Not provided'} | "
                    f"{trace.decision_effect} |"
                )
            lines.append("")

    lines.extend(
        [
            "## Decision Rules",
            "",
            "- BLOCKED: any blocking control is FAIL.",
            "- NEEDS_REVIEW: no blocking failure exists, but at least one blocking control is UNKNOWN or MISSING.",
            "- READY_WITH_FOLLOW_UP: every blocking control is PASS and at least one advisory control is FAIL, UNKNOWN, or MISSING.",
            "- READY: every required policy control has a PASS assessment with CURRENT evidence, a valid owner, and an evidence reference.",
            "- Evidence coverage is descriptive only and never overrides decision precedence.",
            "",
            "## Assurance Boundaries",
            "",
            "- All data is synthetic.",
            "- The control model is illustrative.",
            "- Decisions are deterministic.",
            "- no numerical readiness score exists.",
            "- Missing evidence is not treated as success.",
            "- READY means only that modeled controls satisfy this policy snapshot.",
            "- READY does not authorize deployment.",
            "- READY does not certify compliance.",
            "- READY does not guarantee success.",
            "- Human organizational judgment remains required.",
            "- Evidence metadata is validated, but the system does not independently verify external artifact truth.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def write_summary(
    evaluations: list[ReadinessEvaluation],
    path: Path = DEFAULT_OUTPUT,
) -> None:
    path.write_text(
        render_markdown_summary(evaluations),
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    initiatives = load_readiness_initiatives()
    assessments = load_readiness_assessments(initiatives)
    evaluations = evaluate_readiness_dataset(initiatives, assessments)
    write_summary(evaluations)

    counts = decision_counts(evaluations)
    print("Operational readiness assurance complete.")
    print(f"Initiatives evaluated: {len(evaluations)}")
    print(
        "Decision distribution: "
        f"READY={counts.get(ReadinessDecision.READY, 0)}, "
        f"READY_WITH_FOLLOW_UP={counts.get(ReadinessDecision.READY_WITH_FOLLOW_UP, 0)}, "
        f"NEEDS_REVIEW={counts.get(ReadinessDecision.NEEDS_REVIEW, 0)}, "
        f"BLOCKED={counts.get(ReadinessDecision.BLOCKED, 0)}"
    )
    print(f"Summary written to: {DEFAULT_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
