import unittest

from logic.risk_score import (
    OperationalItem,
    calculate_score,
    classify_score,
    evaluate_item,
)


class RiskScoreTests(unittest.TestCase):
    def test_stable_example(self) -> None:
        item = OperationalItem(
            item_id="OPS-1110",
            status="In Progress",
            overdue_days=20,
            handoff_count=1,
            priority_weight=20,
            rework_count=0,
        )

        result = evaluate_item(item)

        self.assertEqual(result.risk_score, 12.0)
        self.assertEqual(result.classification, "Stable")

    def test_watch_example(self) -> None:
        item = OperationalItem(
            item_id="OPS-1087",
            status="Open",
            overdue_days=60,
            handoff_count=8,
            priority_weight=50,
            rework_count=8,
        )

        result = evaluate_item(item)

        self.assertEqual(result.risk_score, 37.0)
        self.assertEqual(result.classification, "Watch")

    def test_at_risk_example(self) -> None:
        item = OperationalItem(
            item_id="OPS-1042",
            status="In Review",
            overdue_days=120,
            handoff_count=8,
            priority_weight=50,
            rework_count=6,
        )

        result = evaluate_item(item)

        self.assertEqual(result.risk_score, 61.0)
        self.assertEqual(result.classification, "At Risk")
        self.assertIn("Combined signals meet the at-risk review threshold", result.reasons)

    def test_threshold_boundaries(self) -> None:
        self.assertEqual(classify_score(30), "Stable")
        self.assertEqual(classify_score(31), "Watch")
        self.assertEqual(classify_score(60), "Watch")
        self.assertEqual(classify_score(61), "At Risk")

    def test_invalid_negative_values(self) -> None:
        with self.assertRaises(ValueError):
            OperationalItem(
                item_id="OPS-2001",
                status="Open",
                overdue_days=-1,
                handoff_count=0,
                priority_weight=10,
                rework_count=0,
            )

    def test_deterministic_output(self) -> None:
        item = OperationalItem(
            item_id="OPS-1042",
            status="In Review",
            overdue_days=120,
            handoff_count=8,
            priority_weight=50,
            rework_count=6,
        )

        first = evaluate_item(item).to_dict()
        second = evaluate_item(item).to_dict()

        self.assertEqual(first, second)

    def test_scoring_calculation_correctness(self) -> None:
        item = OperationalItem(
            item_id="OPS-1087",
            status="Open",
            overdue_days=60,
            handoff_count=8,
            priority_weight=50,
            rework_count=8,
        )

        self.assertAlmostEqual(calculate_score(item), 37.2)


if __name__ == "__main__":
    unittest.main()
