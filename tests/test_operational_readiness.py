import tempfile
import unittest
from pathlib import Path

from analysis.evaluate_operational_readiness import (
    ReadinessCsvValidationError,
    evaluate_readiness_dataset,
    load_readiness_assessments,
    load_readiness_initiatives,
    render_markdown_summary,
    review_queue,
    write_summary,
)
from logic.readiness_gate import AssessmentStatus, EvidenceState, ReadinessDecision


class ReadinessCsvValidationTests(unittest.TestCase):
    def write_csv(self, content: str, encoding: str = "utf-8") -> Path:
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            newline="",
            suffix=".csv",
            delete=False,
        )
        with temp_file:
            temp_file.write(content)
        return Path(temp_file.name)

    def test_initiative_csv_header_and_value_validation(self) -> None:
        cases = (
            (
                "initiative_name,description\nAlpha,Test\n",
                "missing required column",
            ),
            (
                "initiative_id,initiative_name,initiative_id\nINIT-1,Alpha,INIT-1\n",
                "duplicate required column",
            ),
            (
                "initiative_id,initiative_name\n,Alpha\n",
                "row 2.*initiative_id is required",
            ),
            (
                "initiative_id,initiative_name\nINIT-1,\n",
                "row 2.*initiative_name is required",
            ),
            (
                "initiative_id,initiative_name\nINIT-1,Alpha\nINIT-1,Bravo\n",
                "row 3.*duplicate initiative_id",
            ),
            (
                "initiative_id,initiative_name\nINIT-1,Alpha\n INIT-1 ,Bravo\n",
                "row 3.*duplicate initiative_id",
            ),
        )

        for content, expected_message in cases:
            with self.subTest(expected_message=expected_message):
                path = self.write_csv(content)
                self.addCleanup(path.unlink)
                with self.assertRaisesRegex(ReadinessCsvValidationError, expected_message):
                    load_readiness_initiatives(path)

    def test_assessment_csv_validation_and_referential_integrity(self) -> None:
        initiatives = load_readiness_initiatives()
        cases = (
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state\n"
                "INIT-ALPHA,TEST_EVIDENCE,PASS,QA Reviewer,SYN-1,CURRENT\n",
                "missing required column",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up,status\n"
                "INIT-ALPHA,TEST_EVIDENCE,PASS,QA Reviewer,SYN-1,CURRENT,,PASS\n",
                "duplicate required column",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up\n"
                "INIT-UNKNOWN,TEST_EVIDENCE,PASS,QA Reviewer,SYN-1,CURRENT,\n",
                "unknown initiative_id",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up\n"
                "INIT-ALPHA,UNKNOWN_CONTROL,PASS,QA Reviewer,SYN-1,CURRENT,\n",
                "unknown control_id",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up\n"
                "INIT-ALPHA,TEST_EVIDENCE,COMPLETE,QA Reviewer,SYN-1,CURRENT,\n",
                "unsupported status",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up\n"
                "INIT-ALPHA,TEST_EVIDENCE,PASS,QA Reviewer,SYN-1,RECENT,\n",
                "unsupported evidence_state",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up\n"
                "INIT-ALPHA,TEST_EVIDENCE,PASS,QA Reviewer,SYN-1,CURRENT,\n"
                "INIT-ALPHA,TEST_EVIDENCE,PASS,QA Reviewer,SYN-2,CURRENT,\n",
                "duplicate assessment",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up\n"
                "INIT-ALPHA,TEST_EVIDENCE,PASS,QA Reviewer,SYN-1,STALE,\n",
                "PASS requires CURRENT evidence",
            ),
            (
                "initiative_id,control_id,status,owner_role,evidence_ref,evidence_state,follow_up\n"
                "INIT-ALPHA,TEST_EVIDENCE,UNKNOWN,QA Reviewer,,MISSING,\n",
                "UNKNOWN requires follow_up",
            ),
        )

        for content, expected_message in cases:
            with self.subTest(expected_message=expected_message):
                path = self.write_csv(content)
                self.addCleanup(path.unlink)
                with self.assertRaisesRegex(ReadinessCsvValidationError, expected_message):
                    load_readiness_assessments(initiatives, path)


class OperationalReadinessWorkflowTests(unittest.TestCase):
    def readiness_inputs(self):
        initiatives = load_readiness_initiatives()
        assessments = load_readiness_assessments(initiatives)
        evaluations = evaluate_readiness_dataset(initiatives, assessments)
        return initiatives, assessments, evaluations

    def test_sample_dataset_evaluates_all_initiatives_and_all_decisions(self) -> None:
        _, _, evaluations = self.readiness_inputs()
        by_id = {result.initiative_id: result for result in evaluations}

        self.assertEqual(len(evaluations), 5)
        self.assertEqual(by_id["INIT-ALPHA"].decision, ReadinessDecision.READY)
        self.assertEqual(
            by_id["INIT-BRAVO"].decision,
            ReadinessDecision.READY_WITH_FOLLOW_UP,
        )
        self.assertEqual(by_id["INIT-CHARLIE"].decision, ReadinessDecision.NEEDS_REVIEW)
        self.assertEqual(by_id["INIT-DELTA"].decision, ReadinessDecision.BLOCKED)
        self.assertEqual(by_id["INIT-FOXTROT"].decision, ReadinessDecision.NEEDS_REVIEW)
        self.assertEqual(by_id["INIT-CHARLIE"].blocking_missing, ("TRACEABILITY",))
        self.assertEqual(by_id["INIT-DELTA"].blocking_failures, ("DEPENDENCY_RESOLUTION",))

    def test_sample_dataset_demonstrates_all_evidence_states(self) -> None:
        _, assessments, _ = self.readiness_inputs()

        self.assertEqual(
            {assessment.evidence_state for assessment in assessments},
            {EvidenceState.CURRENT, EvidenceState.STALE, EvidenceState.MISSING},
        )

    def test_bravo_stale_advisory_scenario_remains_follow_up(self) -> None:
        _, assessments, evaluations = self.readiness_inputs()
        by_id = {result.initiative_id: result for result in evaluations}
        bravo_monitoring = next(
            assessment
            for assessment in assessments
            if assessment.initiative_id == "INIT-BRAVO"
            and assessment.control_id == "MONITORING_RECONCILIATION"
        )

        self.assertEqual(bravo_monitoring.status, AssessmentStatus.UNKNOWN)
        self.assertEqual(bravo_monitoring.evidence_state, EvidenceState.STALE)
        self.assertEqual(bravo_monitoring.evidence_ref, "SYN-BRAVO-MONITORING")
        self.assertEqual(
            by_id["INIT-BRAVO"].decision,
            ReadinessDecision.READY_WITH_FOLLOW_UP,
        )
        self.assertEqual(
            by_id["INIT-BRAVO"].stale_evidence_controls,
            ("MONITORING_RECONCILIATION",),
        )
        self.assertEqual(by_id["INIT-BRAVO"].evidence_coverage_percentage, "92.3%")

    def test_delta_blocker_can_have_full_current_evidence_coverage(self) -> None:
        _, _, evaluations = self.readiness_inputs()
        delta = {
            result.initiative_id: result
            for result in evaluations
        }["INIT-DELTA"]

        self.assertEqual(delta.decision, ReadinessDecision.BLOCKED)
        self.assertEqual(delta.blocking_failures, ("DEPENDENCY_RESOLUTION",))
        self.assertEqual(delta.current_evidence_count, delta.expected_control_count)
        self.assertEqual(delta.evidence_coverage_percentage, "100.0%")

    def test_initiative_with_zero_assessments_remains_visible(self) -> None:
        initiatives = load_readiness_initiatives()
        zero_assessment_initiative = [item for item in initiatives if item.initiative_id == "INIT-ALPHA"]

        evaluations = evaluate_readiness_dataset(zero_assessment_initiative, [])

        self.assertEqual(len(evaluations), 1)
        self.assertEqual(evaluations[0].decision, ReadinessDecision.NEEDS_REVIEW)
        self.assertEqual(len(evaluations[0].blocking_missing), 9)

    def test_review_queue_ordering_is_deterministic(self) -> None:
        _, _, evaluations = self.readiness_inputs()

        self.assertEqual(
            [result.initiative_id for result in review_queue(evaluations)],
            ["INIT-DELTA", "INIT-FOXTROT", "INIT-CHARLIE", "INIT-BRAVO", "INIT-ALPHA"],
        )

    def test_generated_markdown_contains_required_sections_and_boundaries(self) -> None:
        _, _, evaluations = self.readiness_inputs()
        markdown = render_markdown_summary(evaluations)

        for heading in (
            "# Operational Readiness Assurance",
            "## Decision Summary",
            "## Review Queue",
            "## Blocking Issues",
            "## Unknown And Missing Controls",
            "## Advisory Follow-Up",
            "## Evidence Coverage",
            "## Initiative Detail",
            "## Decision Rules",
            "## Assurance Boundaries",
        ):
            self.assertIn(heading, markdown)

        self.assertIn("READY does not authorize deployment", markdown)
        self.assertIn("no numerical readiness score exists", markdown)
        self.assertIn(
            "Current evidence coverage measures the availability of CURRENT referenced evidence, not control success.",
            markdown,
        )
        self.assertIn("SYN-BRAVO-MONITORING", markdown)
        self.assertIn("| INIT-DELTA | DEPENDENCY_RESOLUTION | DEPENDENCY_RESOLUTION | FAIL | CURRENT | Technical Owner | SYN-DELTA-DEPENDENCY |", markdown)
        self.assertIn("| INIT-CHARLIE | TRACEABILITY | BLOCKING | NOT_ASSESSED | N/A |", markdown)
        self.assertIn("| INIT-FOXTROT | EXCEPTION_HANDLING | BLOCKING | UNKNOWN | MISSING |", markdown)
        self.assertIn("| INIT-DELTA | BLOCKED |", markdown)
        self.assertIn("TRACEABILITY", markdown)

    def test_generated_markdown_is_deterministic_and_writer_matches_renderer(self) -> None:
        _, _, evaluations = self.readiness_inputs()
        expected = render_markdown_summary(evaluations)

        self.assertEqual(expected, render_markdown_summary(evaluations))

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "readiness.md"
            write_summary(evaluations, path)

            self.assertEqual(path.read_text(encoding="utf-8"), expected)
            self.assertNotIn(b"\r\n", path.read_bytes())


if __name__ == "__main__":
    unittest.main()
