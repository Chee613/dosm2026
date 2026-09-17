import csv
import unittest
from pathlib import Path

from scripts.stress_attribution import (
    FACTOR_GROUPS, INSIGHTS, MIN_STRESSOR_PUSH_PP, REPORT_STRESSORS, STRESSOR_GROUPS, top_stressor,
)
from scripts.train_models import FEATURES

ROOT = Path(__file__).resolve().parents[1]
STRESS = ROOT / "data/processed/stress_contributions.csv"
FEATURE_STRESS = ROOT / "data/processed/stress_feature_contributions.csv"
PRIORITIES = ROOT / "data/processed/reef_priority_predictions.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class StressAttributionTests(unittest.TestCase):
    def test_groups_partition_every_model_feature_exactly_once(self):
        grouped = [feature for names in FACTOR_GROUPS.values() for feature in names]
        self.assertEqual(sorted(grouped), sorted(FEATURES))
        self.assertEqual(len(grouped), len(set(grouped)))
        self.assertTrue(set(STRESSOR_GROUPS).issubset(FACTOR_GROUPS))

    def test_baseline_plus_groups_equals_each_published_prediction(self):
        predictions = {r["island"]: float(r["predicted_next_change_pct_per_year"]) for r in rows(PRIORITIES)}
        stress = rows(STRESS)
        self.assertEqual({r["island"] for r in stress}, set(predictions))
        for row in stress:
            total = float(row["baseline_pp"]) + sum(float(row[group]) for group in FACTOR_GROUPS)
            self.assertAlmostEqual(total, predictions[row["island"]], places=6, msg=row["island"])

    def test_top_stressor_follows_the_report_evidence_rule(self):
        evidence = {r["island"]: r["evidence"] for r in rows(PRIORITIES)}
        for row in rows(STRESS):
            stressor, insight = REPORT_STRESSORS[evidence[row["island"]]]
            self.assertEqual(row["top_stressor"], stressor or "", row["island"])
            self.assertEqual(row["insight"], insight, row["island"])
            expected_pp = float(row[stressor]) if stressor else 0.0
            self.assertAlmostEqual(float(row["top_stressor_pp"]), expected_pp, places=9, msg=row["island"])

    def test_model_attribution_follows_the_threshold_rule(self):
        for row in rows(STRESS):
            groups = {group: float(row[group]) for group in FACTOR_GROUPS}
            stressor, push = top_stressor(groups)
            self.assertEqual(row["model_top_stressor"], stressor or "", row["island"])
            self.assertEqual(row["model_insight"], INSIGHTS[stressor], row["island"])
            if stressor:
                self.assertLessEqual(push, -MIN_STRESSOR_PUSH_PP)
                self.assertIn(stressor, STRESSOR_GROUPS)

    def test_feature_contributions_add_up_to_each_group(self):
        groups = {row["island"]: row for row in rows(STRESS)}
        for row in rows(FEATURE_STRESS):
            for group, features in FACTOR_GROUPS.items():
                total = sum(float(row[feature]) for feature in features)
                self.assertAlmostEqual(total, float(groups[row["island"]][group]), places=9, msg=row["island"])

    def test_every_unit_has_a_report_reason_and_model_evidence(self):
        from scripts.build_web_dashboard_data import build_bundle
        for unit in build_bundle()["priorityIslands"]:
            stress = unit["stress"]
            self.assertTrue(stress["reportReason"]["label"], unit["island"])
            self.assertTrue(stress["reportReason"]["detail"], unit["island"])
            stressor_pushes = [group["pp"] for group in stress["groups"] if group["stressor"]]
            if min(stressor_pushes) < 0:
                evidence = stress["evidence"]
                self.assertEqual(evidence["pp"], min(stressor_pushes), unit["island"])
                # Only inputs that moved the prediction: none that round to 0.00 pp/yr.
                self.assertLessEqual(len(evidence["items"]), len(FACTOR_GROUPS[evidence["group"]]))
                for entry in evidence["items"]:
                    self.assertGreaterEqual(abs(entry["pp"]), 0.005, unit["island"])
            else:
                self.assertIsNone(stress["evidence"], unit["island"])

    def test_context_groups_never_become_the_top_stressor(self):
        groups = {group: 0.0 for group in FACTOR_GROUPS}
        groups["Starting condition & trend"] = -9.0
        groups["Region & survey year"] = -9.0
        self.assertEqual(top_stressor(groups), (None, 0.0))


if __name__ == "__main__":
    unittest.main()
