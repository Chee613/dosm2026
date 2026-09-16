import csv
import json
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


class ModelOutputTests(unittest.TestCase):
    def test_pipeline_selects_lowest_mae_candidate(self):
        metrics = json.loads(
            (ROOT / "output/model_evaluation_metrics.json").read_text(encoding="utf-8")
        )
        candidates = {
            name: values["MAE"]
            for name, values in metrics["model_comparison"].items()
            if name != "Baseline mean"
        }
        self.assertEqual(metrics["best_candidate"], min(candidates, key=candidates.get))

    def test_pipeline_exports_sample_size_aware_trends(self):
        annual_path = PROCESSED / "survey_year_summary.csv"
        paired_path = PROCESSED / "paired_change_summary.csv"
        self.assertTrue(annual_path.exists())
        self.assertTrue(paired_path.exists())
        if not annual_path.exists() or not paired_path.exists():
            return

        annual = {
            int(row["survey_year"]): row
            for row in read_rows(annual_path)
        }
        paired = read_rows(paired_path)[0]
        self.assertEqual(int(annual[2012]["surveyed_units"]), 388)
        self.assertEqual(int(annual[2025]["surveyed_units"]), 487)
        self.assertEqual(int(paired["paired_units"]), 444)
        self.assertAlmostEqual(float(paired["change_pp"]), -0.4688027, places=4)

    def test_pipeline_exports_validation_by_year(self):
        path = PROCESSED / "model_validation_by_year.csv"
        self.assertTrue(path.exists())
        if not path.exists():
            return

        rows = read_rows(path)
        self.assertEqual([int(row["target_year"]) for row in rows], [2021, 2022, 2023, 2024, 2025])
        self.assertEqual(sum(int(row["n"]) for row in rows), 2405)

    def test_prediction_bounds_use_forward_residual_quantiles(self):
        validation = read_rows(PROCESSED / "model_validation_predictions.csv")
        residuals = np.array([
            float(row["target_lcc_change_rate"]) - float(row["predicted_change"])
            for row in validation
        ])
        expected_lower, expected_upper = np.quantile(residuals, [0.025, 0.975])

        priority = read_rows(PROCESSED / "reef_priority_predictions.csv")
        first = priority[0]
        predicted = float(first["predicted_next_change_pct_per_year"])
        self.assertAlmostEqual(float(first["prediction_lower"]) - predicted, expected_lower)
        self.assertAlmostEqual(float(first["prediction_upper"]) - predicted, expected_upper)


if __name__ == "__main__":
    unittest.main()
