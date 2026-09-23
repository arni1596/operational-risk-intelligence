import tempfile
import unittest
from pathlib import Path

from analysis.analyze_threshold_sensitivity import analyze_threshold_sensitivity
from analysis.build_operational_review_dashboard import (
    render_dashboard,
    write_dashboard,
)
from analysis.evaluate_operational_risk import (
    classification_counts,
    evaluate_dataset,
    load_operational_items,
    top_review_candidates,
)


class OperationalReviewDashboardTests(unittest.TestCase):
    def dashboard_inputs(self):
        items = load_operational_items()
        risk_results = evaluate_dataset(items)
        sensitivity_results = analyze_threshold_sensitivity(items)
        return risk_results, sensitivity_results

    def risk_results_by_id(self):
        risk_results, _ = self.dashboard_inputs()
        return {result.item_id: result for result in risk_results}

    def sensitivity_results_by_name(self):
        _, sensitivity_results = self.dashboard_inputs()
        return {result.scenario.name: result for result in sensitivity_results}

    def test_dashboard_contains_required_sections(self) -> None:
        dashboard = render_dashboard(*self.dashboard_inputs())

        for expected_text in (
            "Operational Review Dashboard",
            "Current Portfolio Snapshot",
            "Priority Review Queue",
            "Signal Snapshot",
            "Threshold Sensitivity Snapshot",
            "Classification Movement",
            "Review Notes",
        ):
            self.assertIn(expected_text, dashboard)

    def test_dashboard_preserves_current_distribution(self) -> None:
        risk_results, sensitivity_results = self.dashboard_inputs()
        dashboard = render_dashboard(risk_results, sensitivity_results)

        self.assertEqual(
            classification_counts(risk_results),
            {"At Risk": 1, "Watch": 3, "Stable": 4},
        )
        self.assertIn("| At Risk | 1 |", dashboard)
        self.assertIn("| Watch | 3 |", dashboard)
        self.assertIn("| Stable | 4 |", dashboard)

    def test_dashboard_evaluates_all_sample_records(self) -> None:
        risk_results, _ = self.dashboard_inputs()

        self.assertEqual(len(risk_results), 8)

    def test_review_queue_membership_and_order(self) -> None:
        risk_results, _ = self.dashboard_inputs()

        review_queue = top_review_candidates(risk_results, limit=len(risk_results))

        self.assertEqual(
            [result.item_id for result in review_queue],
            ["OPS-1042", "OPS-1194", "OPS-1288", "OPS-1087"],
        )
        self.assertEqual(len(review_queue), 4)
        self.assertEqual(
            {result.classification for result in review_queue},
            {"At Risk", "Watch"},
        )
        self.assertNotIn("OPS-1110", {result.item_id for result in review_queue})

    def test_known_item_regressions(self) -> None:
        results_by_id = self.risk_results_by_id()

        self.assertEqual(results_by_id["OPS-1042"].review_score, 61)
        self.assertEqual(results_by_id["OPS-1042"].classification, "At Risk")
        self.assertEqual(results_by_id["OPS-1087"].review_score, 37)
        self.assertEqual(results_by_id["OPS-1087"].classification, "Watch")
        self.assertEqual(results_by_id["OPS-1110"].review_score, 12)
        self.assertEqual(results_by_id["OPS-1110"].classification, "Stable")

    def test_dashboard_portfolio_snapshot_values(self) -> None:
        dashboard = render_dashboard(*self.dashboard_inputs())

        self.assertIn("| Total Items | 8 | 100.0% |", dashboard)
        self.assertIn("| Stable | 4 | 50.0% |", dashboard)
        self.assertIn("| Watch | 3 | 37.5% |", dashboard)
        self.assertIn("| At Risk | 1 | 12.5% |", dashboard)
        self.assertIn("| Review Queue | 4 | 50.0% |", dashboard)

    def test_dashboard_includes_review_queue_signals_and_movements(self) -> None:
        dashboard = render_dashboard(*self.dashboard_inputs())

        self.assertIn(
            "| 1 | OPS-1042 | In Review | 61 | 61.0 | At Risk | 120 | 8 | 6 |",
            dashboard,
        )
        self.assertIn("| Review queue items with overdue days | 4 |", dashboard)
        self.assertIn("| Total overdue days across review queue | 340 |", dashboard)
        self.assertIn("| Total handoffs across review queue | 29 |", dashboard)
        self.assertIn("| Total rework across review queue | 22 |", dashboard)
        self.assertIn("| Highest overdue-days value | 120 |", dashboard)
        self.assertIn("| Highest handoff count | 8 |", dashboard)
        self.assertIn("| Highest rework count | 8 |", dashboard)
        self.assertIn(
            "| Earlier Review | OPS-1215 | 26 | Stable | Watch | Stable -> Watch |",
            dashboard,
        )
        self.assertIn(
            "| Later Review | OPS-1042 | 61 | At Risk | Watch | At Risk -> Watch |",
            dashboard,
        )

    def test_threshold_scenario_counts_and_movements(self) -> None:
        sensitivity_by_name = self.sensitivity_results_by_name()

        expected_counts = {
            "Current": {"Stable": 4, "Watch": 3, "At Risk": 1},
            "Earlier Review": {"Stable": 3, "Watch": 4, "At Risk": 1},
            "Later Review": {"Stable": 4, "Watch": 4, "At Risk": 0},
        }

        for scenario_name, expected in expected_counts.items():
            with self.subTest(scenario=scenario_name):
                counts = sensitivity_by_name[scenario_name].counts
                actual = {
                    classification: counts.get(classification, 0)
                    for classification in expected
                }
                self.assertEqual(
                    actual,
                    expected,
                )

        earlier_changes = {
            change.item_id: change for change in sensitivity_by_name["Earlier Review"].changes
        }
        later_changes = {
            change.item_id: change for change in sensitivity_by_name["Later Review"].changes
        }

        self.assertEqual(earlier_changes["OPS-1215"].change, "Stable -> Watch")
        self.assertEqual(later_changes["OPS-1042"].change, "At Risk -> Watch")

    def test_dashboard_does_not_use_hard_coded_movement_interpretation(self) -> None:
        dashboard = render_dashboard(*self.dashboard_inputs())

        self.assertNotIn(
            "changes the classification for OPS-1042",
            dashboard,
        )

    def test_dashboard_rendering_is_deterministic(self) -> None:
        inputs = self.dashboard_inputs()

        self.assertEqual(render_dashboard(*inputs), render_dashboard(*inputs))

    def test_write_dashboard_matches_renderer(self) -> None:
        risk_results, sensitivity_results = self.dashboard_inputs()
        expected = render_dashboard(risk_results, sensitivity_results)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dashboard.md"
            write_dashboard(risk_results, sensitivity_results, path)

            self.assertEqual(path.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
