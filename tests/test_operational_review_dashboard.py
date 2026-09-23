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
)


class OperationalReviewDashboardTests(unittest.TestCase):
    def dashboard_inputs(self):
        items = load_operational_items()
        risk_results = evaluate_dataset(items)
        sensitivity_results = analyze_threshold_sensitivity(items)
        return risk_results, sensitivity_results

    def test_dashboard_contains_required_sections(self) -> None:
        dashboard = render_dashboard(*self.dashboard_inputs())

        for expected_text in (
            "Operational Review Dashboard",
            "Current Risk Snapshot",
            "Priority Review Queue",
            "Threshold Sensitivity Snapshot",
            "Classification Movement",
            "Review Focus",
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

    def test_dashboard_includes_review_queue_and_movements(self) -> None:
        dashboard = render_dashboard(*self.dashboard_inputs())

        self.assertIn("| OPS-1042 | In Review | 61 | 61.0 | At Risk |", dashboard)
        self.assertIn(
            "| Earlier Review | OPS-1215 | 26 | Stable | Watch | Stable -> Watch |",
            dashboard,
        )
        self.assertIn(
            "| Later Review | OPS-1042 | 61 | At Risk | Watch | At Risk -> Watch |",
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
