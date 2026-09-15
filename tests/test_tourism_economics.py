import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARRIVALS = ROOT / "data/raw/structured/tourism/island_arrivals.csv"
DMPM_VISITORS = ROOT / "data/raw/structured/taman_laut_visitors_2000_2017.csv"
PARKS_CSV = ROOT / "data/processed/park_economics.csv"
ECONOMICS_JSON = ROOT / "data/processed/tourism_economics.json"
PRIORITIES = ROOT / "data/processed/reef_priority_predictions.csv"
BLEACHING_SITES = ROOT / "data/raw/structured/reef_check/bleaching_2024.csv"
BLEACHING_HEADLINE = ROOT / "data/raw/structured/reef_check/bleaching_2024_headline.csv"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class ArrivalsProvenanceTests(unittest.TestCase):
    def test_every_arrival_row_is_measured_and_sourced(self):
        for row in rows(ARRIVALS):
            self.assertGreater(float(row["arrivals_total"]), 0, row["island"])
            self.assertTrue(row["source_url"].startswith("https://"), row["island"])
            self.assertRegex(row["retrieved_date"], r"^\d{4}-\d{2}-\d{2}$", row["island"])

    def test_economics_never_uses_the_excluded_accommodation_table(self):
        source = (ROOT / "scripts/tourism_economics.py").read_text(encoding="utf-8")
        self.assertNotIn("island_accommodations", source)
        self.assertNotIn("estimated_room_capacity", source)


class ParkEconomicsTests(unittest.TestCase):
    def test_reef_adjacent_value_is_ten_percent_of_spending(self):
        for row in rows(PARKS_CSV):
            self.assertAlmostEqual(float(row["reef_adjacent_rm"]), float(row["spending_rm"]) * 0.10,
                                   delta=1.0, msg=row["park"])

    def test_peninsular_parks_average_recorded_years_2013_2017(self):
        source = rows(DMPM_VISITORS)
        department_parks = [p for p in rows(PARKS_CSV) if p["source_name"].startswith("Department of Marine Park")]
        self.assertEqual(len(department_parks), 5)
        for park in department_parks:
            # Zero totals are unrecorded years and are left out of the average.
            recorded = {int(r["year"]): int(r["total_visitors"]) for r in source
                        if r["state"] == park["state"] and 2013 <= int(r["year"]) <= 2017 and int(r["total_visitors"]) > 0}
            self.assertEqual(int(park["visitors_per_year"]), round(sum(recorded.values()) / len(recorded)), park["park"])
            self.assertEqual(park["basis"], f"{min(recorded)}-{max(recorded)} average", park["park"])
        labuan = next(p for p in department_parks if p["state"] == "Labuan")
        self.assertEqual(labuan["basis"], "2016-2017 average")

    def test_national_estimate_sums_the_parks_and_excludes_malacca(self):
        payload = json.loads(ECONOMICS_JSON.read_text(encoding="utf-8"))
        parks = rows(PARKS_CSV)
        self.assertEqual(payload["national_visitors"], sum(int(p["visitors_per_year"]) for p in parks))
        self.assertEqual(payload["national_reef_adjacent_rm"], sum(int(p["reef_adjacent_rm"]) for p in parks))
        units = {u for p in parks for u in p["units"].split("; ") if u}
        self.assertNotIn("Malacca", units)
        self.assertIn("Malacca", payload["units_excluded"])
        self.assertEqual(payload["units_covered"] + len(payload["units_excluded"]), payload["units_total"])

    def test_season_rest_covers_parks_holding_high_priority_units(self):
        payload = json.loads(ECONOMICS_JSON.read_text(encoding="utf-8"))
        tradeoff = payload["tradeoff"]
        high = {row["island"] for row in rows(PRIORITIES) if "High" in row["priority_tier"]}
        self.assertEqual(tradeoff["units_total"], len(high))
        self.assertTrue(set(tradeoff["units_covered_names"]).issubset(high))
        self.assertEqual(set(tradeoff["units_covered_names"]) | set(tradeoff["units_uncovered_names"]), high)
        self.assertEqual(tradeoff["recovery_mid_years"], 12.5)
        self.assertAlmostEqual(tradeoff["long_term_mid_rm"], tradeoff["reef_adjacent_annual_rm"] * 12.5, delta=1.0)
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
