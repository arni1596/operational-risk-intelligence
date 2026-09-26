import unittest
from pathlib import Path

from analysis.analyze_threshold_sensitivity import (
    analyze_threshold_sensitivity,
    render_markdown_summary as render_threshold_summary,
)
from analysis.build_operational_review_dashboard import render_dashboard
from analysis.evaluate_operational_risk import (
    evaluate_dataset,
    load_operational_items,
    render_markdown_summary as render_risk_summary,
)


ROOT = Path(__file__).resolve().parents[1]


class GeneratedReportConsistencyTests(unittest.TestCase):
    def assert_generated_report_current(
        self,
        report_path: Path,
        rendered_content: str,
        regeneration_command: str,
    ) -> None:
        report_bytes = report_path.read_bytes()
        self.assertNotIn(
            b"\r\n",
            report_bytes,
            f"{report_path.relative_to(ROOT)} contains CRLF line endings.",
        )
        committed_content = report_bytes.decode("utf-8")
        relative_path = report_path.relative_to(ROOT)

        self.assertEqual(
            committed_content,
            rendered_content,
            (
                f"{relative_path} is stale.\n\n"
                f"Regenerate with:\n{regeneration_command}\n\n"
                "Then commit the regenerated artifact."
            ),
        )

    def test_risk_review_summary_matches_renderer(self) -> None:
        items = load_operational_items()
        results = evaluate_dataset(items)

        self.assert_generated_report_current(
            ROOT / "reporting" / "risk_review_summary.md",
            render_risk_summary(results),
            "python analysis/evaluate_operational_risk.py",
        )

    def test_threshold_sensitivity_summary_matches_renderer(self) -> None:
        items = load_operational_items()
        results = analyze_threshold_sensitivity(items)

        self.assert_generated_report_current(
            ROOT / "reporting" / "threshold_sensitivity_summary.md",
            render_threshold_summary(results),
            "python analysis/analyze_threshold_sensitivity.py",
        )

    def test_operational_review_dashboard_matches_renderer(self) -> None:
        items = load_operational_items()
        risk_results = evaluate_dataset(items)
        sensitivity_results = analyze_threshold_sensitivity(items)

        self.assert_generated_report_current(
            ROOT / "reporting" / "operational_review_dashboard.md",
            render_dashboard(risk_results, sensitivity_results),
            "python analysis/build_operational_review_dashboard.py",
        )


if __name__ == "__main__":
    unittest.main()
