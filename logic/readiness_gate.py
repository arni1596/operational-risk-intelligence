"""Deterministic operational-readiness assurance rules.

This module is the authoritative source for readiness policy, assessment
validation, decision precedence, and trace generation. It intentionally stays
separate from the operational risk scoring model.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Iterable


class ReadinessControlArea(Enum):
    TEST_EVIDENCE = "TEST_EVIDENCE"
    ACCOUNTABLE_OWNERSHIP = "ACCOUNTABLE_OWNERSHIP"
    DEPENDENCY_RESOLUTION = "DEPENDENCY_RESOLUTION"
    APPROVAL_DECISION_GATE = "APPROVAL_DECISION_GATE"
    EXCEPTION_HANDLING = "EXCEPTION_HANDLING"
    BYPASS_LEGACY_PATH = "BYPASS_LEGACY_PATH"
    MONITORING_RECONCILIATION = "MONITORING_RECONCILIATION"
    TRACEABILITY = "TRACEABILITY"
    SUPPORT_READINESS = "SUPPORT_READINESS"
    OPERATIONAL_ENABLEMENT = "OPERATIONAL_ENABLEMENT"
    SOURCE_OF_TRUTH = "SOURCE_OF_TRUTH"
    POLICY_CONSTRAINTS = "POLICY_CONSTRAINTS"
    CLOSEOUT_CRITERIA = "CLOSEOUT_CRITERIA"


class Criticality(Enum):
    BLOCKING = "BLOCKING"
    ADVISORY = "ADVISORY"


class AssessmentStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class EvidenceState(Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    MISSING = "MISSING"


class ReadinessDecision(Enum):
    READY = "READY"
    READY_WITH_FOLLOW_UP = "READY_WITH_FOLLOW_UP"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    BLOCKED = "BLOCKED"


def normalize_identifier(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def normalize_text(value: str, field_name: str, *, required: bool = True) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be text")
    normalized = value.strip()
    if required and not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def coerce_enum(enum_type: type[Enum], value: Enum | str, field_name: str) -> Enum:
    if isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        normalized = value.strip()
        for member in enum_type:
            if member.value == normalized:
                return member
    raise ValueError(f"unsupported {field_name}: {value}")


@dataclass(frozen=True)
class ReadinessControlDefinition:
    control_id: str
    control_area: ReadinessControlArea
    criticality: Criticality
    description: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "control_id",
            normalize_identifier(self.control_id, "control_id"),
        )
        object.__setattr__(
            self,
            "control_area",
            coerce_enum(ReadinessControlArea, self.control_area, "control_area"),
        )
        object.__setattr__(
            self,
            "criticality",
            coerce_enum(Criticality, self.criticality, "criticality"),
        )
        object.__setattr__(
            self,
            "description",
            normalize_text(self.description, "description"),
        )


@dataclass(frozen=True)
class ReadinessPolicy:
    controls: tuple[ReadinessControlDefinition, ...]

    def __post_init__(self) -> None:
        controls = tuple(self.controls)
        if not controls:
            raise ValueError("ReadinessPolicy must contain at least one control")

        seen: set[str] = set()
        for control in controls:
            if not isinstance(control, ReadinessControlDefinition):
                raise TypeError("controls must contain ReadinessControlDefinition values")
            if control.control_id in seen:
                raise ValueError(f"duplicate control_id: {control.control_id}")
            seen.add(control.control_id)

        if not any(control.criticality == Criticality.BLOCKING for control in controls):
            raise ValueError("ReadinessPolicy must contain at least one BLOCKING control")

        object.__setattr__(self, "controls", controls)

    @property
    def controls_by_id(self) -> dict[str, ReadinessControlDefinition]:
        return {control.control_id: control for control in self.controls}

    @property
    def blocking_control_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                control.control_id
                for control in self.controls
                if control.criticality == Criticality.BLOCKING
            )
        )

    @property
    def advisory_control_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                control.control_id
                for control in self.controls
                if control.criticality == Criticality.ADVISORY
            )
        )


@dataclass(frozen=True)
class ReadinessInitiative:
    initiative_id: str
    initiative_name: str
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "initiative_id",
            normalize_identifier(self.initiative_id, "initiative_id"),
        )
        object.__setattr__(
            self,
            "initiative_name",
            normalize_text(self.initiative_name, "initiative_name"),
        )
        object.__setattr__(
            self,
            "description",
            normalize_text(self.description, "description", required=False),
        )


@dataclass(frozen=True)
class ReadinessAssessment:
    initiative_id: str
    control_id: str
    status: AssessmentStatus
    owner_role: str
    evidence_ref: str
    evidence_state: EvidenceState
    follow_up: str = ""

    def __post_init__(self) -> None:
        status = coerce_enum(AssessmentStatus, self.status, "status")
        evidence_state = coerce_enum(EvidenceState, self.evidence_state, "evidence_state")
        owner_role = normalize_text(self.owner_role, "owner_role")
        evidence_ref = normalize_text(
            self.evidence_ref,
            "evidence_ref",
            required=False,
        )
        follow_up = normalize_text(self.follow_up, "follow_up", required=False)

        if evidence_state == EvidenceState.CURRENT and not evidence_ref:
            raise ValueError("CURRENT evidence requires evidence_ref")
        if evidence_state == EvidenceState.STALE and not evidence_ref:
            raise ValueError("STALE evidence requires evidence_ref")
        if evidence_state == EvidenceState.MISSING and evidence_ref:
            raise ValueError("MISSING evidence cannot include evidence_ref")

        if status == AssessmentStatus.PASS:
            if not evidence_ref:
                raise ValueError("PASS requires evidence_ref")
            if evidence_state != EvidenceState.CURRENT:
                raise ValueError("PASS requires CURRENT evidence")
        else:
            if not follow_up:
                raise ValueError(f"{status.value} requires follow_up")

        object.__setattr__(
            self,
            "initiative_id",
            normalize_identifier(self.initiative_id, "initiative_id"),
        )
        object.__setattr__(
            self,
            "control_id",
            normalize_identifier(self.control_id, "control_id"),
        )
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "owner_role", owner_role)
        object.__setattr__(self, "evidence_ref", evidence_ref)
        object.__setattr__(self, "evidence_state", evidence_state)
        object.__setattr__(self, "follow_up", follow_up)


@dataclass(frozen=True)
class ReadinessControlTrace:
    control_id: str
    control_area: ReadinessControlArea
    criticality: Criticality
    assessment_state: AssessmentStatus | None
    evidence_state: EvidenceState | None
    owner_role: str
    evidence_ref: str
    follow_up: str
    is_resolved: bool
    decision_effect: str


@dataclass(frozen=True)
class ReadinessEvaluation:
    initiative_id: str
    initiative_name: str
    decision: ReadinessDecision
    expected_control_count: int
    assessed_control_count: int
    passed_controls: tuple[str, ...]
    failed_controls: tuple[str, ...]
    unknown_controls: tuple[str, ...]
    missing_controls: tuple[str, ...]
    blocking_failures: tuple[str, ...]
    blocking_unknowns: tuple[str, ...]
    blocking_missing: tuple[str, ...]
    advisory_failures: tuple[str, ...]
    advisory_unknowns: tuple[str, ...]
    advisory_missing: tuple[str, ...]
    stale_evidence_controls: tuple[str, ...]
    missing_evidence_controls: tuple[str, ...]
    unresolved_control_ids: tuple[str, ...]
    current_evidence_count: int
    evidence_coverage_percentage: str
    decision_rule: str
    decision_basis: str
    control_traces: tuple[ReadinessControlTrace, ...]

    @property
    def control_traces_by_id(self) -> dict[str, ReadinessControlTrace]:
        return {trace.control_id: trace for trace in self.control_traces}


def _control_definition(
    area: ReadinessControlArea,
    criticality: Criticality,
    description: str,
) -> ReadinessControlDefinition:
    return ReadinessControlDefinition(
        control_id=area.value,
        control_area=area,
        criticality=criticality,
        description=description,
    )


DEFAULT_READINESS_POLICY = ReadinessPolicy(
    (
        _control_definition(
            ReadinessControlArea.TEST_EVIDENCE,
            Criticality.BLOCKING,
            "Required test evidence is current and reviewable.",
        ),
        _control_definition(
            ReadinessControlArea.ACCOUNTABLE_OWNERSHIP,
            Criticality.BLOCKING,
            "An accountable owner is identified for readiness follow-up.",
        ),
        _control_definition(
            ReadinessControlArea.DEPENDENCY_RESOLUTION,
            Criticality.BLOCKING,
            "Blocking dependencies are resolved or explicitly addressed.",
        ),
        _control_definition(
            ReadinessControlArea.APPROVAL_DECISION_GATE,
            Criticality.BLOCKING,
            "Required decision-gate evidence is captured for review.",
        ),
        _control_definition(
            ReadinessControlArea.EXCEPTION_HANDLING,
            Criticality.BLOCKING,
            "Exceptions and alternate paths are documented for review.",
        ),
        _control_definition(
            ReadinessControlArea.BYPASS_LEGACY_PATH,
            Criticality.BLOCKING,
            "Bypass or legacy-path handling is documented where applicable.",
        ),
        _control_definition(
            ReadinessControlArea.MONITORING_RECONCILIATION,
            Criticality.ADVISORY,
            "Monitoring and reconciliation expectations are represented.",
        ),
        _control_definition(
            ReadinessControlArea.TRACEABILITY,
            Criticality.BLOCKING,
            "Readiness evidence is traceable to the reviewed initiative.",
        ),
        _control_definition(
            ReadinessControlArea.SUPPORT_READINESS,
            Criticality.ADVISORY,
            "Support handoff expectations are represented.",
        ),
        _control_definition(
            ReadinessControlArea.OPERATIONAL_ENABLEMENT,
            Criticality.ADVISORY,
            "Operational enablement needs are represented.",
        ),
        _control_definition(
            ReadinessControlArea.SOURCE_OF_TRUTH,
            Criticality.BLOCKING,
            "The source of truth for readiness review is identified.",
        ),
        _control_definition(
            ReadinessControlArea.POLICY_CONSTRAINTS,
            Criticality.ADVISORY,
            "Policy constraints are represented for follow-up review.",
        ),
        _control_definition(
            ReadinessControlArea.CLOSEOUT_CRITERIA,
            Criticality.BLOCKING,
            "Closeout criteria are represented before readiness is marked ready.",
        ),
    )
)


def _percentage(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.0%"
    percentage = (Decimal(numerator) * Decimal("100") / Decimal(denominator)).quantize(
        Decimal("0.1"),
        rounding=ROUND_HALF_UP,
    )
    return f"{percentage}%"


def evaluate_readiness(
    initiative: ReadinessInitiative,
    policy: ReadinessPolicy,
    assessments: Iterable[ReadinessAssessment],
) -> ReadinessEvaluation:
    controls_by_id = policy.controls_by_id
    sorted_controls = tuple(sorted(policy.controls, key=lambda control: control.control_id))
    assessment_by_control: dict[str, ReadinessAssessment] = {}

    for item in assessments:
        if item.initiative_id != initiative.initiative_id:
            continue
        if item.control_id not in controls_by_id:
            raise ValueError(f"unknown control_id: {item.control_id}")
        if item.control_id in assessment_by_control:
            raise ValueError(f"duplicate assessment for {initiative.initiative_id}/{item.control_id}")
        assessment_by_control[item.control_id] = item

    passed: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []
    missing: list[str] = []
    blocking_failures: list[str] = []
    blocking_unknowns: list[str] = []
    blocking_missing: list[str] = []
    advisory_failures: list[str] = []
    advisory_unknowns: list[str] = []
    advisory_missing: list[str] = []
    stale_evidence: list[str] = []
    missing_evidence: list[str] = []
    traces: list[ReadinessControlTrace] = []
    current_evidence_count = 0

    for control in sorted_controls:
        item = assessment_by_control.get(control.control_id)
        if item is None:
            missing.append(control.control_id)
            if control.criticality == Criticality.BLOCKING:
                blocking_missing.append(control.control_id)
                effect = "missing blocking assessment requires review"
            else:
                advisory_missing.append(control.control_id)
                effect = "missing advisory assessment requires follow-up"
            traces.append(
                ReadinessControlTrace(
                    control_id=control.control_id,
                    control_area=control.control_area,
                    criticality=control.criticality,
                    assessment_state=None,
                    evidence_state=None,
                    owner_role="",
                    evidence_ref="",
                    follow_up="",
                    is_resolved=False,
                    decision_effect=effect,
                )
            )
            continue

        if item.evidence_state == EvidenceState.CURRENT and item.evidence_ref:
            current_evidence_count += 1
        if item.evidence_state == EvidenceState.STALE:
            stale_evidence.append(control.control_id)
        if item.evidence_state == EvidenceState.MISSING:
            missing_evidence.append(control.control_id)

        is_resolved = item.status == AssessmentStatus.PASS
        if item.status == AssessmentStatus.PASS:
            passed.append(control.control_id)
            effect = "satisfies required readiness control"
        elif item.status == AssessmentStatus.FAIL:
            failed.append(control.control_id)
            if control.criticality == Criticality.BLOCKING:
                blocking_failures.append(control.control_id)
                effect = "blocking failure blocks readiness"
            else:
                advisory_failures.append(control.control_id)
                effect = "advisory failure requires follow-up"
        else:
            unknown.append(control.control_id)
            if control.criticality == Criticality.BLOCKING:
                blocking_unknowns.append(control.control_id)
                effect = "blocking unknown requires review"
            else:
                advisory_unknowns.append(control.control_id)
                effect = "advisory unknown requires follow-up"

        traces.append(
            ReadinessControlTrace(
                control_id=control.control_id,
                control_area=control.control_area,
                criticality=control.criticality,
                assessment_state=item.status,
                evidence_state=item.evidence_state,
                owner_role=item.owner_role,
                evidence_ref=item.evidence_ref,
                follow_up=item.follow_up,
                is_resolved=is_resolved,
                decision_effect=effect,
            )
        )

    unresolved = tuple(sorted(set(failed + unknown + missing)))

    if blocking_failures:
        decision = ReadinessDecision.BLOCKED
        decision_rule = "blocking control failed"
        decision_basis = (
            "Blocking control failure(s) prevent readiness: "
            + ", ".join(blocking_failures)
        )
    elif blocking_unknowns or blocking_missing:
        decision = ReadinessDecision.NEEDS_REVIEW
        decision_rule = "blocking control unknown or missing"
        blockers = tuple(sorted(blocking_unknowns + blocking_missing))
        decision_basis = (
            "Blocking control(s) need review before readiness: "
            + ", ".join(blockers)
        )
    elif advisory_failures or advisory_unknowns or advisory_missing:
        decision = ReadinessDecision.READY_WITH_FOLLOW_UP
        decision_rule = "advisory control unresolved"
        advisory = tuple(sorted(advisory_failures + advisory_unknowns + advisory_missing))
        decision_basis = (
            "Blocking controls pass; advisory follow-up remains: "
            + ", ".join(advisory)
        )
    else:
        decision = ReadinessDecision.READY
        decision_rule = "all required controls passed"
        decision_basis = "Every required policy control has current passing evidence."

    return ReadinessEvaluation(
        initiative_id=initiative.initiative_id,
        initiative_name=initiative.initiative_name,
        decision=decision,
        expected_control_count=len(policy.controls),
        assessed_control_count=len(assessment_by_control),
        passed_controls=tuple(sorted(passed)),
        failed_controls=tuple(sorted(failed)),
        unknown_controls=tuple(sorted(unknown)),
        missing_controls=tuple(sorted(missing)),
        blocking_failures=tuple(sorted(blocking_failures)),
        blocking_unknowns=tuple(sorted(blocking_unknowns)),
        blocking_missing=tuple(sorted(blocking_missing)),
        advisory_failures=tuple(sorted(advisory_failures)),
        advisory_unknowns=tuple(sorted(advisory_unknowns)),
        advisory_missing=tuple(sorted(advisory_missing)),
        stale_evidence_controls=tuple(sorted(stale_evidence)),
        missing_evidence_controls=tuple(sorted(missing_evidence)),
        unresolved_control_ids=unresolved,
        current_evidence_count=current_evidence_count,
        evidence_coverage_percentage=_percentage(current_evidence_count, len(policy.controls)),
        decision_rule=decision_rule,
        decision_basis=decision_basis,
        control_traces=tuple(traces),
    )
