import unittest

from logic.risk_score import (
    OperationalItem,
    calculate_risk_score,
    classify_risk,
    evaluate_item,
)


class RiskScoringTests(unittest.TestCase):
    def test_documented_stable_example(self):
        item = OperationalItem("OPS-1110", 20, 1, 20, 0)
        self.assertEqual(calculate_risk_score(item), 12.3)
        self.assertEqual(evaluate_item(item)["classification"], "Stable")

    def test_documented_watch_example(self):
        item = OperationalItem("OPS-1087", 60, 8, 50, 8)
        self.assertEqual(calculate_risk_score(item), 37.2)
        self.assertEqual(evaluate_item(item)["classification"], "Watch")

    def test_documented_at_risk_example(self):
        item = OperationalItem("OPS-1042", 120, 8, 50, 6)
        self.assertEqual(calculate_risk_score(item), 61.0)
        self.assertEqual(evaluate_item(item)["classification"], "At Risk")

    def test_threshold_boundaries(self):
        self.assertEqual(classify_risk(30), "Stable")
        self.assertEqual(classify_risk(31), "Watch")
        self.assertEqual(classify_risk(60), "Watch")
        self.assertEqual(classify_risk(61), "At Risk")

    def test_negative_signals_are_rejected(self):
        with self.assertRaises(ValueError):
            OperationalItem("OPS-BAD", -1, 0, 0, 0)

    def test_score_is_deterministic(self):
        item = OperationalItem("OPS-DET", 40, 2, 25, 3)
        self.assertEqual(evaluate_item(item), evaluate_item(item))

    def test_weighted_score_calculation(self):
        item = OperationalItem("OPS-CALC", 10, 4, 20, 3)
        self.assertEqual(calculate_risk_score(item), 9.5)


if __name__ == "__main__":
    unittest.main()
