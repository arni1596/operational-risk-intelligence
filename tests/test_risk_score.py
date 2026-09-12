import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from analysis.evaluate_operational_risk import (
    CsvValidationError,
    classification_counts,
    load_operational_items,
    top_review_candidates,
)
from logic.risk_score import (
    DEFAULT_RISK_CONFIG,
    OperationalItem,
    RiskScoringConfig,
    calculate_exact_score,
    calculate_score,
    classify_score,
    evaluate_item,
    reported_score,
    round_review_score,
    score_components,
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
        self.assertEqual(result.review_score, 12)
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
        self.assertEqual(result.review_score, 37)
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
        self.assertEqual(result.review_score, 61)
        self.assertEqual(result.classification, "At Risk")
        self.assertIn("Combined signals meet the at-risk review threshold", result.reasons)

    def test_threshold_boundaries(self) -> None:
        self.assertEqual(classify_score(30), "Stable")
        self.assertEqual(classify_score(31), "Watch")
        self.assertEqual(classify_score(60), "Watch")
        self.assertEqual(classify_score(61), "At Risk")
        self.assertEqual(classify_score(30.0), "Stable")
        self.assertEqual(classify_score(Decimal("30")), "Stable")

    def test_half_up_rounding_boundaries(self) -> None:
        cases = (
            (Decimal("30.49"), 30, "Stable"),
            (Decimal("30.50"), 31, "Watch"),
            (Decimal("60.49"), 60, "Watch"),
            (Decimal("60.50"), 61, "At Risk"),
        )

        for exact_score, expected_review_score, expected_classification in cases:
            with self.subTest(exact_score=exact_score):
                review_score = round_review_score(exact_score)

                self.assertEqual(review_score, expected_review_score)
                self.assertEqual(classify_score(review_score), expected_classification)

    def test_half_point_reporting_rounds_up_before_classification(self) -> None:
        item = OperationalItem(
            item_id="OPS-EDGE",
            status="Open",
            overdue_days=76,
            handoff_count=0,
            priority_weight=0,
            rework_count=1,
        )

        self.assertAlmostEqual(calculate_score(item), 30.5)
        self.assertEqual(reported_score(item), 31.0)
        self.assertEqual(evaluate_item(item).classification, "Watch")

    def test_fractional_classification_rejection(self) -> None:
        for score in (60.9, Decimal("30.1")):
            with self.subTest(score=score):
                with self.assertRaises(ValueError):
                    classify_score(score)

    def test_classification_rejects_invalid_score_types(self) -> None:
        for score in (True, -1, "30"):
            with self.subTest(score=score):
                with self.assertRaises((TypeError, ValueError)):
                    classify_score(score)  # type: ignore[arg-type]

    def test_invalid_negative_values_for_each_signal(self) -> None:
        base = {
            "item_id": "OPS-2001",
            "status": "Open",
            "overdue_days": 0,
            "handoff_count": 0,
            "priority_weight": 10,
            "rework_count": 0,
        }

        for field_name in (
            "overdue_days",
            "handoff_count",
            "priority_weight",
            "rework_count",
        ):
            with self.subTest(field_name=field_name):
                payload = dict(base)
                payload[field_name] = -1
                with self.assertRaisesRegex(ValueError, field_name):
                    OperationalItem(**payload)

    def test_boolean_signal_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            OperationalItem(
                item_id="OPS-BOOL",
                status="Open",
                overdue_days=True,
                handoff_count=0,
                priority_weight=10,
                rework_count=0,
            )

    def test_malformed_mapping_values_fail_validation(self) -> None:
        base = {
            "item_id": "OPS-2001",
            "status": "Open",
            "overdue_days": "1",
            "handoff_count": "0",
            "priority_weight": "10",
            "rework_count": "0",
        }
        cases = {
            "abc": "valid integer",
            "": "required",
            "4.5": "whole-number integer",
            "-1": "cannot be negative",
            True: "must be an integer",
        }

        for value, message in cases.items():
            with self.subTest(value=value):
                payload = dict(base)
                payload["overdue_days"] = value
                with self.assertRaisesRegex((TypeError, ValueError), message):
                    OperationalItem.from_mapping(payload)

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
        self.assertEqual(calculate_exact_score(item), Decimal("37.2"))

    def test_exact_decimal_component_calculation(self) -> None:
        item = OperationalItem(
            item_id="OPS-1087",
            status="Open",
            overdue_days=60,
            handoff_count=8,
            priority_weight=50,
            rework_count=8,
        )

        self.assertEqual(
            score_components(item),
            {
                "overdue_days": Decimal("24.0"),
                "handoff_count": Decimal("2.4"),
                "priority_weight": Decimal("10.0"),
                "rework_count": Decimal("0.8"),
            },
        )
        self.assertEqual(calculate_exact_score(item), Decimal("37.2"))

    def test_custom_configuration_changes_result_without_mutating_default(self) -> None:
        item = OperationalItem(
            item_id="OPS-3001",
            status="Open",
            overdue_days=10,
            handoff_count=0,
            priority_weight=0,
            rework_count=0,
        )
        custom_config = RiskScoringConfig(
            overdue_days_weight=Decimal("4.0"),
            handoff_count_weight=Decimal("0.3"),
            priority_weight_weight=Decimal("0.2"),
            rework_count_weight=Decimal("0.1"),
            stable_upper_bound=30,
            watch_upper_bound=60,
        )

        default_result = evaluate_item(item)
        custom_result = evaluate_item(item, custom_config)

        self.assertEqual(default_result.review_score, 4)
        self.assertEqual(default_result.classification, "Stable")
        self.assertEqual(custom_result.review_score, 40)
        self.assertEqual(custom_result.classification, "Watch")
        self.assertEqual(DEFAULT_RISK_CONFIG.overdue_days_weight, Decimal("0.4"))

    def test_sample_dataset_distribution_regression(self) -> None:
        results = [evaluate_item(item) for item in load_operational_items()]

        self.assertEqual(
            classification_counts(results),
            {"At Risk": 1, "Watch": 3, "Stable": 4},
        )

    def test_deterministic_review_candidate_ranking(self) -> None:
        lower_exact = evaluate_item(
            OperationalItem(
                item_id="OPS-B",
                status="Open",
                overdue_days=77,
                handoff_count=0,
                priority_weight=0,
                rework_count=0,
            )
        )
        higher_exact = evaluate_item(
            OperationalItem(
                item_id="OPS-A",
                status="Open",
                overdue_days=78,
                handoff_count=0,
                priority_weight=0,
                rework_count=0,
            )
        )
        tie_second = evaluate_item(
            OperationalItem(
                item_id="OPS-D",
                status="Open",
                overdue_days=78,
                handoff_count=0,
                priority_weight=0,
                rework_count=0,
            )
        )
        tie_first = evaluate_item(
            OperationalItem(
                item_id="OPS-C",
                status="Open",
                overdue_days=78,
                handoff_count=0,
                priority_weight=0,
                rework_count=0,
            )
        )

        ranked = top_review_candidates(
            [lower_exact, tie_second, tie_first, higher_exact],
            limit=4,
        )

        self.assertEqual(
            [result.item_id for result in ranked],
            ["OPS-A", "OPS-C", "OPS-D", "OPS-B"],
        )


class CsvValidationTests(unittest.TestCase):
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

    def test_missing_required_header(self) -> None:
        path = self.write_csv(
            "item_id,status,priority_weight,overdue_days,handoff_count\n"
            "OPS-1,Open,10,0,0\n"
        )
        self.addCleanup(path.unlink)

        with self.assertRaisesRegex(CsvValidationError, "missing required column"):
            load_operational_items(path)

    def test_duplicate_required_header(self) -> None:
        path = self.write_csv(
            "item_id,status,priority_weight,overdue_days,handoff_count,rework_count,rework_count\n"
            "OPS-1,Open,10,0,0,0,0\n"
        )
        self.addCleanup(path.unlink)

        with self.assertRaisesRegex(CsvValidationError, "duplicate required column"):
            load_operational_items(path)

    def test_malformed_row_value(self) -> None:
        path = self.write_csv(
            "item_id,status,priority_weight,overdue_days,handoff_count,rework_count\n"
            "OPS-1,Open,10,abc,0,0\n"
        )
        self.addCleanup(path.unlink)

        with self.assertRaisesRegex(CsvValidationError, "row 2.*overdue_days"):
            load_operational_items(path)

    def test_missing_required_value(self) -> None:
        path = self.write_csv(
            "item_id,status,priority_weight,overdue_days,handoff_count,rework_count\n"
            "OPS-1,,10,0,0,0\n"
        )
        self.addCleanup(path.unlink)

        with self.assertRaisesRegex(CsvValidationError, "row 2.*status is required"):
            load_operational_items(path)

    def test_utf8_bom_header_handling(self) -> None:
        path = self.write_csv(
            "item_id,status,priority_weight,overdue_days,handoff_count,rework_count\n"
            "OPS-1,Open,10,0,0,0\n",
            encoding="utf-8-sig",
        )
        self.addCleanup(path.unlink)

        items = load_operational_items(path)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_id, "OPS-1")


if __name__ == "__main__":
    unittest.main()
