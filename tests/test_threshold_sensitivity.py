import unittest

from analysis.analyze_threshold_sensitivity import (
    SCENARIOS,
    analyze_threshold_sensitivity,
    render_markdown_summary,
)
from analysis.evaluate_operational_risk import classification_counts, load_operational_items
from logic.risk_score import DEFAULT_RISK_CONFIG, OperationalItem, evaluate_item


class ThresholdSensitivityTests(unittest.TestCase):
    def scenario_by_name(self) -> dict[str, object]:
        return {scenario.name: scenario for scenario in SCENARIOS}

    def test_scenario_definitions(self) -> None:
        scenarios = self.scenario_by_name()

        self.assertEqual(scenarios["Current"].config.stable_upper_bound, 30)
        self.assertEqual(scenarios["Current"].config.watch_upper_bound, 60)
        self.assertEqual(scenarios["Earlier Review"].config.stable_upper_bound, 25)
        self.assertEqual(scenarios["Earlier Review"].config.watch_upper_bound, 55)
        self.assertEqual(scenarios["Later Review"].config.stable_upper_bound, 35)
        self.assertEqual(scenarios["Later Review"].config.watch_upper_bound, 65)

    def test_default_config_is_not_mutated(self) -> None:
        before = DEFAULT_RISK_CONFIG

        analyze_threshold_sensitivity(load_operational_items())

        self.assertEqual(DEFAULT_RISK_CONFIG, before)
        self.assertEqual(DEFAULT_RISK_CONFIG.stable_upper_bound, 30)
        self.assertEqual(DEFAULT_RISK_CONFIG.watch_upper_bound, 60)

    def test_score_invariance_across_threshold_scenarios(self) -> None:
        item = OperationalItem(
            item_id="OPS-EDGE",
            status="Open",
            overdue_days=145,
            handoff_count=0,
            priority_weight=0,
            rework_count=0,
        )

        results = [evaluate_item(item, scenario.config) for scenario in SCENARIOS]

        self.assertEqual({result.exact_score for result in results}, {results[0].exact_score})
        self.assertEqual({result.review_score for result in results}, {58})

    def test_classification_transitions_near_boundaries(self) -> None:
        scenarios = self.scenario_by_name()
        cases = (
            (
                OperationalItem("OPS-28", "Open", 70, 0, 0, 0),
                {
                    "Current": "Stable",
                    "Earlier Review": "Watch",
                    "Later Review": "Stable",
                },
            ),
            (
                OperationalItem("OPS-58", "Open", 145, 0, 0, 0),
                {
                    "Current": "Watch",
                    "Earlier Review": "At Risk",
                    "Later Review": "Watch",
                },
            ),
            (
                OperationalItem("OPS-63", "Open", 157, 0, 0, 0),
                {
                    "Current": "At Risk",
                    "Earlier Review": "At Risk",
                    "Later Review": "Watch",
                },
            ),
        )

        for item, expected_by_scenario in cases:
            with self.subTest(item_id=item.item_id):
                for scenario_name, expected_classification in expected_by_scenario.items():
                    result = evaluate_item(item, scenarios[scenario_name].config)
                    self.assertEqual(result.classification, expected_classification)

    def test_analysis_is_deterministic(self) -> None:
        items = load_operational_items()

        first = analyze_threshold_sensitivity(items)
        second = analyze_threshold_sensitivity(items)

        self.assertEqual(first, second)

    def test_current_scenario_sample_distribution_regression(self) -> None:
        current_result = analyze_threshold_sensitivity(load_operational_items())[0]

        self.assertEqual(
            classification_counts(current_result.evaluations),
            {"At Risk": 1, "Watch": 3, "Stable": 4},
        )

    def test_report_rendering_contains_required_sections(self) -> None:
        report = render_markdown_summary(
            analyze_threshold_sensitivity(load_operational_items())
        )

        for expected_text in (
            "Threshold Sensitivity Analysis",
            "Current",
            "Earlier Review",
            "Later Review",
            "Classification Distribution",
            "Classification Changes",
        ):
            self.assertIn(expected_text, report)


if __name__ == "__main__":
    unittest.main()
