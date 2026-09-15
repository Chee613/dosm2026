import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARRIVALS = ROOT / "data/raw/structured/tourism/island_arrivals.csv"
ECONOMICS_CSV = ROOT / "data/processed/island_economics.csv"
ECONOMICS_JSON = ROOT / "data/processed/tourism_economics.json"
PRIORITIES = ROOT / "data/processed/reef_priority_predictions.csv"
BLEACHING_SITES = ROOT / "data/raw/structured/reef_check/bleaching_2024.csv"
BLEACHING_HEADLINE = ROOT / "data/raw/structured/reef_check/bleaching_2024_headline.csv"
ACCOMMODATION = "island_accommodations"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class ArrivalsProvenanceTests(unittest.TestCase):
    def test_every_arrival_row_is_measured_and_sourced(self):
        arrivals = rows(ARRIVALS)
        self.assertEqual(len(arrivals), 11)
        for row in arrivals:
            self.assertGreater(float(row["arrivals_total"]), 0, row["island"])
            self.assertIn(int(row["period_months"]), {8, 12}, row["island"])
            self.assertTrue(row["source_url"].startswith("https://"), row["island"])
            self.assertRegex(row["retrieved_date"], r"^\d{4}-\d{2}-\d{2}$", row["island"])

    def test_economics_never_uses_the_excluded_accommodation_table(self):
        source = (ROOT / "scripts/tourism_economics.py").read_text(encoding="utf-8")
        self.assertNotIn(ACCOMMODATION, source)
        self.assertNotIn("estimated_room_capacity", source)


class TourismEconomicsTests(unittest.TestCase):
    def test_reef_adjacent_value_is_ten_percent_of_spending(self):
        for row in rows(ECONOMICS_CSV):
            self.assertAlmostEqual(float(row["reef_adjacent_rm"]), float(row["spending_rm"]) * 0.10,
                                   delta=1.0, msg=row["island"])

    def test_only_islands_with_published_arrivals_are_valued(self):
        measured = {row["island"] for row in rows(ARRIVALS)}
        valued = {row["island"] for row in rows(ECONOMICS_CSV)}
        self.assertTrue(valued.issubset(measured))

    def test_season_rest_uses_current_high_priority_islands_and_discloses_its_ratio(self):
        payload = json.loads(ECONOMICS_JSON.read_text(encoding="utf-8"))
        tradeoff = payload["tradeoff"]
        high = {row["island"] for row in rows(PRIORITIES) if "High" in row["priority_tier"]}
        self.assertTrue(set(tradeoff["island_names"]).issubset(high))
        self.assertEqual(tradeoff["islands_total"], len(high))
        # The ratio is an identity of the assumptions and must be labelled, never shown as a finding.
        self.assertNotIn("ratio_low", tradeoff)
        self.assertIn("by construction", tradeoff["ratio_note"])


class BleachingEvidenceTests(unittest.TestCase):
    def test_headline_figures_match_the_published_report(self):
        headline = {row["metric"]: float(row["value_pct"]) for row in rows(BLEACHING_HEADLINE)}
        self.assertEqual(headline["corals_bleached"], 50.7)
        self.assertEqual(headline["mean_bleaching_mortality"], 34.1)
        self.assertEqual(headline["terengganu_mean_mortality"], 44.2)

    def test_site_table_matches_report_table_one(self):
        sites = {(row["island"], row["site"]): row for row in rows(BLEACHING_SITES)}
        self.assertEqual(len(rows(BLEACHING_SITES)), 26)
        self.assertEqual(float(sites[("Redang", "Pulau Pinang")]["mortality_pct"]), 63.6)
        self.assertEqual(float(sites[("Lang Tengah", "Pasir Besar")]["mortality_pct"]), 56.8)
        self.assertEqual(float(sites[("Tioman", "Renggis")]["mortality_pct"]), 37.5)


if __name__ == "__main__":
    unittest.main()
