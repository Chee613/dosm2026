import csv
import unittest
from pathlib import Path

from scripts.train_models import FEATURES


ROOT = Path(__file__).resolve().parents[1]


class ProvenanceTests(unittest.TestCase):
    def test_unconfirmed_sources_do_not_enter_scored_model(self):
        self.assertNotIn("noaa_max_dhw", FEATURES)
        self.assertNotIn("noaa_mean_ssta", FEATURES)

        manifest_path = ROOT / "data" / "provenance_manifest.csv"
        with manifest_path.open(encoding="utf-8", newline="") as stream:
            sources = {row["dataset_id"]: row for row in csv.DictReader(stream)}

        self.assertEqual(sources["reef_check_surveys"]["status"], "verified_input")
        self.assertEqual(sources["dmpm_tev_2011_2015"]["status"], "verified_context")
        self.assertEqual(sources["noaa_crw_virtual_stations"]["status"], "eligibility_pending")
        # Every row of the visitor file matches one of five published state datasets.
        for state in ("johor", "kedah", "pahang", "terengganu", "labuan"):
            row = sources[f"marine_park_visitors_{state}_2000_2017"]
            self.assertEqual(row["status"], "verified_context")
            self.assertTrue(row["source_url"].startswith("https://archive.data.gov.my/"))
        self.assertNotIn("marine_park_visitors_2010_2017", sources)
        for dataset in ("island_arrivals_sabah_parks_2024", "island_arrivals_terengganu_2024", "bleaching_impact_2024"):
            self.assertEqual(sources[dataset]["status"], "verified_context")
            self.assertTrue(sources[dataset]["source_url"].startswith("https://"))
        self.assertEqual(sources["island_accommodations"]["status"], "excluded_unverified")

        coordinates = (ROOT / "data/raw/structured/geocoding/island_coordinates.csv").read_text(encoding="utf-8")
        self.assertIn("Labuan,5.3167,115.2167,Labuan,W.P. Labuan,Labuan Marine Park", coordinates)
        with (ROOT / "data/processed/reef_priority_predictions.csv").open(encoding="utf-8", newline="") as stream:
            priorities = {row["island"]: row for row in csv.DictReader(stream)}
        self.assertEqual(priorities["Labuan"]["state"], "W.P. Labuan")

        assumptions = (ROOT / "docs/assumptions.md").read_text(encoding="utf-8")
        self.assertIn("six evaluated archipelagos", assumptions)
        self.assertNotIn("simulate 20-year NPV", assumptions)


if __name__ == "__main__":
    unittest.main()
