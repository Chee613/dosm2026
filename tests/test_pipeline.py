import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_noaa_parser_reads_dhw_column(self):
        from scripts.pipeline import parse_noaa_row

        row = "2024 06 01 29.0 31.0 30.0 1.5 1.5 8.75 4".split()
        self.assertEqual(parse_noaa_row(row), (2024, 1.5, 8.75))

    def test_processed_data_has_no_generated_tourism_proxies(self):
        with (ROOT / "data/processed/master_reef_tourism_dataset.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            fields = csv.DictReader(stream).fieldnames

        self.assertNotIn("tourism_pressure_index", fields)
        self.assertNotIn("tourism_gdp_intensity_pct", fields)

    def test_next_observation_target_is_from_a_later_year(self):
        from scripts.pipeline import make_next_observation_rows

        rows = [
            {"island": "A", "survey_year": 2022, "lcc_change_rate": -1.0},
            {"island": "A", "survey_year": 2024, "lcc_change_rate": -3.5},
            {"island": "B", "survey_year": 2023, "lcc_change_rate": 2.0},
        ]

        result = make_next_observation_rows(rows)

        self.assertEqual(result, [{
            "island": "A",
            "survey_year": 2022,
            "lcc_change_rate": -1.0,
            "target_year": 2024,
            "target_lcc_change_rate": -3.5,
        }])

    def test_forward_splits_never_train_on_test_or_future_years(self):
        from scripts.pipeline import expanding_year_splits

        splits = expanding_year_splits([2018, 2019, 2020, 2021, 2022], test_years=2)

        self.assertEqual(splits, [
            ([0, 1, 2], [3]),
            ([0, 1, 2, 3], [4]),
        ])

    def test_heat_category_uses_declared_dhw_thresholds(self):
        from scripts.pipeline import heat_category

        self.assertEqual(
            [heat_category(value) for value in (None, 0.99, 1.0, 3.99, 4.0)],
            [None, "DHW < 1", "DHW 1–<4", "DHW 1–<4", "DHW ≥ 4"],
        )


if __name__ == "__main__":
    unittest.main()
