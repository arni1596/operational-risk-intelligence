import unittest

from logic.readiness_gate import (
    DEFAULT_READINESS_POLICY,
    AssessmentStatus,
    Criticality,
    EvidenceState,
    ReadinessAssessment,
    ReadinessControlArea,
    ReadinessControlDefinition,
    ReadinessDecision,
    ReadinessInitiative,
    ReadinessPolicy,
    evaluate_readiness,
)


def assessment(
    control_id: str,
    status: AssessmentStatus = AssessmentStatus.PASS,
    evidence_state: EvidenceState = EvidenceState.CURRENT,
    owner_role: str = "Operations Reviewer",
    evidence_ref: str = "SYN-EVIDENCE-001",
    follow_up: str = "",
    initiative_id: str = "INIT-TEST",
) -> ReadinessAssessment:
    return ReadinessAssessment(
        initiative_id=initiative_id,
        control_id=control_id,
        status=status,
        owner_role=owner_role,
        evidence_ref=evidence_ref,
        evidence_state=evidence_state,
        follow_up=follow_up,
    )


def initiative(initiative_id: str = "INIT-TEST") -> ReadinessInitiative:
    return ReadinessInitiative(
        initiative_id=initiative_id,
        initiative_name="Synthetic Readiness Initiative",
        description="Fictional readiness scenario",
    )


class ReadinessPolicyTests(unittest.TestCase):
    def test_policy_requires_controls_and_blocking_control(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one control"):
            ReadinessPolicy(())

        advisory_only = ReadinessControlDefinition(
            control_id="ADVISORY-ONLY",
            control_area=ReadinessControlArea.SUPPORT_READINESS,
            criticality=Criticality.ADVISORY,
            description="Advisory-only test control",
        )

        with self.assertRaisesRegex(ValueError, "BLOCKING"):
            ReadinessPolicy((advisory_only,))

    def test_policy_rejects_duplicate_normalized_control_ids(self) -> None:
        first = ReadinessControlDefinition(
            control_id="CONTROL-1",
            control_area=ReadinessControlArea.TEST_EVIDENCE,
            criticality=Criticality.BLOCKING,
            description="First control",
        )
        second = ReadinessControlDefinition(
            control_id=" CONTROL-1 ",
            control_area=ReadinessControlArea.TRACEABILITY,
            criticality=Criticality.BLOCKING,
            description="Duplicate control",
        )

        with self.assertRaisesRegex(ValueError, "duplicate control_id"):
            ReadinessPolicy((first, second))

    def test_default_policy_contains_expected_criticality_assignments(self) -> None:
        blocking = set(DEFAULT_READINESS_POLICY.blocking_control_ids)
        advisory = set(DEFAULT_READINESS_POLICY.advisory_control_ids)

        self.assertIn("TEST_EVIDENCE", blocking)
        self.assertIn("EXCEPTION_HANDLING", blocking)
        self.assertIn("CLOSEOUT_CRITERIA", blocking)
        self.assertIn("MONITORING_RECONCILIATION", advisory)
        self.assertIn("SUPPORT_READINESS", advisory)
        self.assertEqual(len(DEFAULT_READINESS_POLICY.controls), 13)


class ReadinessDecisionTests(unittest.TestCase):
    def passing_assessments(self, *, initiative_id: str = "INIT-TEST") -> list[ReadinessAssessment]:
        return [
            assessment(control.control_id, initiative_id=initiative_id)
            for control in DEFAULT_READINESS_POLICY.controls
        ]

    def test_all_required_controls_pass_ready(self) -> None:
        result = evaluate_readiness(
            initiative(),
            DEFAULT_READINESS_POLICY,
            self.passing_assessments(),
        )

        self.assertEqual(result.decision, ReadinessDecision.READY)
        self.assertEqual(result.expected_control_count, 13)
        self.assertEqual(result.assessed_control_count, 13)
        self.assertEqual(result.unresolved_control_ids, ())
        self.assertEqual(result.evidence_coverage_percentage, "100.0%")

    def test_decision_precedence_sequence(self) -> None:
        initiative_under_review = initiative()
        base = {
            item.control_id: item
            for item in self.passing_assessments()
        }
        base["DEPENDENCY_RESOLUTION"] = assessment(
            "DEPENDENCY_RESOLUTION",
            AssessmentStatus.FAIL,
            EvidenceState.MISSING,
            follow_up="Resolve dependency owner handoff.",
            evidence_ref="",
        )
        base["EXCEPTION_HANDLING"] = assessment(
            "EXCEPTION_HANDLING",
            AssessmentStatus.UNKNOWN,
            EvidenceState.MISSING,
            follow_up="Confirm exception path.",
            evidence_ref="",
        )
        base["SUPPORT_READINESS"] = assessment(
            "SUPPORT_READINESS",
            AssessmentStatus.UNKNOWN,
            EvidenceState.MISSING,
            follow_up="Confirm support coverage.",
            evidence_ref="",
        )

        result = evaluate_readiness(
            initiative_under_review,
            DEFAULT_READINESS_POLICY,
            base.values(),
        )
        self.assertEqual(result.decision, ReadinessDecision.BLOCKED)

        base["DEPENDENCY_RESOLUTION"] = assessment("DEPENDENCY_RESOLUTION")
        result = evaluate_readiness(
            initiative_under_review,
            DEFAULT_READINESS_POLICY,
            base.values(),
        )
        self.assertEqual(result.decision, ReadinessDecision.NEEDS_REVIEW)

        base["EXCEPTION_HANDLING"] = assessment("EXCEPTION_HANDLING")
        result = evaluate_readiness(
            initiative_under_review,
            DEFAULT_READINESS_POLICY,
            base.values(),
        )
        self.assertEqual(result.decision, ReadinessDecision.READY_WITH_FOLLOW_UP)

        base["SUPPORT_READINESS"] = assessment("SUPPORT_READINESS")
        result = evaluate_readiness(
            initiative_under_review,
            DEFAULT_READINESS_POLICY,
            base.values(),
        )
        self.assertEqual(result.decision, ReadinessDecision.READY)

    def test_missing_blocking_and_advisory_controls_keep_distinct_meanings(self) -> None:
        blocking_missing = [
            item
            for item in self.passing_assessments()
            if item.control_id != "TRACEABILITY"
        ]
        result = evaluate_readiness(
            initiative(),
            DEFAULT_READINESS_POLICY,
            blocking_missing,
        )
        self.assertEqual(result.decision, ReadinessDecision.NEEDS_REVIEW)
        self.assertEqual(result.blocking_missing, ("TRACEABILITY",))

        advisory_missing = [
            item
            for item in self.passing_assessments()
            if item.control_id != "SUPPORT_READINESS"
        ]
        result = evaluate_readiness(
            initiative(),
            DEFAULT_READINESS_POLICY,
            advisory_missing,
        )
        self.assertEqual(result.decision, ReadinessDecision.READY_WITH_FOLLOW_UP)
        self.assertEqual(result.advisory_missing, ("SUPPORT_READINESS",))

    def test_blocking_unknown_takes_precedence_over_advisory_failure(self) -> None:
        rows = {
            item.control_id: item
            for item in self.passing_assessments()
        }
        rows["EXCEPTION_HANDLING"] = assessment(
            "EXCEPTION_HANDLING",
            AssessmentStatus.UNKNOWN,
            EvidenceState.MISSING,
            follow_up="Confirm exception owner.",
            evidence_ref="",
        )
        rows["SUPPORT_READINESS"] = assessment(
            "SUPPORT_READINESS",
            AssessmentStatus.FAIL,
            EvidenceState.MISSING,
            follow_up="Create support handoff note.",
            evidence_ref="",
        )

        result = evaluate_readiness(initiative(), DEFAULT_READINESS_POLICY, rows.values())

        self.assertEqual(result.decision, ReadinessDecision.NEEDS_REVIEW)
        self.assertEqual(result.blocking_unknowns, ("EXCEPTION_HANDLING",))
        self.assertEqual(result.advisory_failures, ("SUPPORT_READINESS",))

    def test_evidence_coverage_is_descriptive_and_cannot_override_failure(self) -> None:
        rows = {
            item.control_id: item
            for item in self.passing_assessments()
        }
        rows["DEPENDENCY_RESOLUTION"] = assessment(
            "DEPENDENCY_RESOLUTION",
            AssessmentStatus.FAIL,
            EvidenceState.CURRENT,
            follow_up="Resolve dependency issue.",
        )

        result = evaluate_readiness(initiative(), DEFAULT_READINESS_POLICY, rows.values())

        self.assertEqual(result.evidence_coverage_percentage, "100.0%")
        self.assertEqual(result.decision, ReadinessDecision.BLOCKED)
        self.assertIn("DEPENDENCY_RESOLUTION", result.decision_basis)

    def test_decision_trace_is_deterministic_and_explainable(self) -> None:
        rows = {
            item.control_id: item
            for item in self.passing_assessments()
        }
        rows["DEPENDENCY_RESOLUTION"] = assessment(
            "DEPENDENCY_RESOLUTION",
            AssessmentStatus.FAIL,
            EvidenceState.STALE,
            owner_role="Technical Owner",
            evidence_ref="SYN-EVIDENCE-DEP-001",
            follow_up="Resolve dependency before review can advance.",
        )

        first = evaluate_readiness(initiative(), DEFAULT_READINESS_POLICY, rows.values())
        second = evaluate_readiness(initiative(), DEFAULT_READINESS_POLICY, reversed(tuple(rows.values())))

        self.assertEqual(first, second)
        trace = first.control_traces_by_id["DEPENDENCY_RESOLUTION"]
        self.assertEqual(trace.criticality, Criticality.BLOCKING)
        self.assertEqual(trace.assessment_state, AssessmentStatus.FAIL)
        self.assertEqual(trace.owner_role, "Technical Owner")
        self.assertEqual(trace.evidence_state, EvidenceState.STALE)
        self.assertIn("blocks readiness", trace.decision_effect)
        self.assertEqual(first.decision_rule, "blocking control failed")

    def test_policy_order_does_not_change_final_decision(self) -> None:
        reversed_policy = ReadinessPolicy(tuple(reversed(DEFAULT_READINESS_POLICY.controls)))

        result = evaluate_readiness(
            initiative(),
            reversed_policy,
            self.passing_assessments(),
        )

        self.assertEqual(result.decision, ReadinessDecision.READY)
        self.assertEqual(
            tuple(trace.control_id for trace in result.control_traces),
            tuple(sorted(control.control_id for control in DEFAULT_READINESS_POLICY.controls)),
        )

    def test_custom_policy_does_not_mutate_default_policy(self) -> None:
        before = DEFAULT_READINESS_POLICY.controls
        custom = ReadinessPolicy(
            (
                ReadinessControlDefinition(
                    control_id="CUSTOM_BLOCKER",
                    control_area=ReadinessControlArea.TEST_EVIDENCE,
                    criticality=Criticality.BLOCKING,
                    description="Custom blocking control",
                ),
            )
        )

        result = evaluate_readiness(
            ReadinessInitiative("INIT-CUSTOM", "Custom"),
            custom,
            (assessment("CUSTOM_BLOCKER", initiative_id="INIT-CUSTOM"),),
        )

        self.assertEqual(result.decision, ReadinessDecision.READY)
        self.assertEqual(DEFAULT_READINESS_POLICY.controls, before)


class ReadinessAssessmentValidationTests(unittest.TestCase):
    def test_pass_requires_owner_current_evidence_and_reference(self) -> None:
        cases = (
            {"owner_role": "", "evidence_ref": "SYN-1", "evidence_state": EvidenceState.CURRENT},
            {"owner_role": "Owner", "evidence_ref": "", "evidence_state": EvidenceState.CURRENT},
            {"owner_role": "Owner", "evidence_ref": "SYN-1", "evidence_state": EvidenceState.STALE},
            {"owner_role": "Owner", "evidence_ref": "SYN-1", "evidence_state": EvidenceState.MISSING},
        )

        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    assessment("TEST_EVIDENCE", **case)

    def test_unresolved_status_requires_owner_and_follow_up(self) -> None:
        cases = (
            (AssessmentStatus.FAIL, "", "Follow up"),
            (AssessmentStatus.FAIL, "Owner", ""),
            (AssessmentStatus.UNKNOWN, "", "Follow up"),
            (AssessmentStatus.UNKNOWN, "Owner", ""),
        )

        for status, owner_role, follow_up in cases:
            with self.subTest(status=status, owner_role=owner_role, follow_up=follow_up):
                with self.assertRaises(ValueError):
                    assessment(
                        "TEST_EVIDENCE",
                        status=status,
                        evidence_state=EvidenceState.MISSING,
                        owner_role=owner_role,
                        evidence_ref="",
                        follow_up=follow_up,
                    )

    def test_evidence_state_requires_consistent_evidence_reference(self) -> None:
        cases = (
            (AssessmentStatus.FAIL, EvidenceState.CURRENT, "", "CURRENT evidence requires evidence_ref"),
            (AssessmentStatus.UNKNOWN, EvidenceState.CURRENT, "", "CURRENT evidence requires evidence_ref"),
            (AssessmentStatus.FAIL, EvidenceState.STALE, "", "STALE evidence requires evidence_ref"),
            (AssessmentStatus.UNKNOWN, EvidenceState.STALE, "", "STALE evidence requires evidence_ref"),
            (AssessmentStatus.FAIL, EvidenceState.MISSING, "SYN-1", "MISSING evidence cannot include evidence_ref"),
            (AssessmentStatus.UNKNOWN, EvidenceState.MISSING, "SYN-1", "MISSING evidence cannot include evidence_ref"),
        )

        for status, evidence_state, evidence_ref, expected_message in cases:
            with self.subTest(status=status, evidence_state=evidence_state):
                with self.assertRaisesRegex(ValueError, expected_message):
                    assessment(
                        "TEST_EVIDENCE",
                        status=status,
                        evidence_state=evidence_state,
                        evidence_ref=evidence_ref,
                        follow_up="Resolve evidence issue.",
                    )

    def test_unresolved_status_accepts_consistent_evidence_states(self) -> None:
        cases = (
            (AssessmentStatus.FAIL, EvidenceState.CURRENT, "SYN-CURRENT"),
            (AssessmentStatus.UNKNOWN, EvidenceState.STALE, "SYN-STALE"),
            (AssessmentStatus.UNKNOWN, EvidenceState.MISSING, ""),
        )

        for status, evidence_state, evidence_ref in cases:
            with self.subTest(status=status, evidence_state=evidence_state):
                result = assessment(
                    "TEST_EVIDENCE",
                    status=status,
                    evidence_state=evidence_state,
                    evidence_ref=evidence_ref,
                    follow_up="Resolve evidence issue.",
                )

                self.assertEqual(result.status, status)
                self.assertEqual(result.evidence_state, evidence_state)
                self.assertEqual(result.evidence_ref, evidence_ref)


if __name__ == "__main__":
    unittest.main()
