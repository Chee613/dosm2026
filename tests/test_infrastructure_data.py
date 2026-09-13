import os
import unittest
import polars as pl
from pathlib import Path

class TestInfrastructureData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = str(Path(__file__).resolve().parents[1])
        cls.infr_path = os.path.join(cls.base_dir, "data", "raw", "structured", "infrastructure", "island_accommodations.csv")
        cls.geo_path = os.path.join(cls.base_dir, "data", "raw", "structured", "geocoding", "island_coordinates.csv")

    def test_file_exists(self):
        self.assertTrue(os.path.exists(self.infr_path), f"File not found: {self.infr_path}")

    def test_island_coverage_matches_geocoding(self):
        df_infr = pl.read_csv(self.infr_path)
        df_geo = pl.read_csv(self.geo_path)
        
        self.assertEqual(df_infr.shape[0], 56, f"Expected 56 islands, got {df_infr.shape[0]}")
        
        infr_islands = set(df_infr["island"].to_list())
        geo_islands = set(df_geo["island"].to_list())
        
        diff = geo_islands - infr_islands
        self.assertEqual(len(diff), 0, f"Missing islands in accommodations dataset: {diff}")

    def test_data_integrity_and_bounds(self):
        df_infr = pl.read_csv(self.infr_path)
        
        for row in df_infr.iter_rows(named=True):
            self.assertGreaterEqual(row["resort_count"], 0, f"Negative resort count for {row['island']}")
            self.assertGreaterEqual(row["estimated_room_capacity"], 0, f"Negative room capacity for {row['island']}")
            self.assertGreaterEqual(row["dive_center_count"], 0, f"Negative dive centers for {row['island']}")
            self.assertIn(row["has_commercial_jetty"], [0, 1], f"Invalid jetty flag for {row['island']}")
            self.assertTrue(bool(row["data_source"]), f"Missing data source for {row['island']}")

    def test_ground_truth_conservation_and_hotspots(self):
        df_infr = pl.read_csv(self.infr_path)
        data = {r["island"]: r for r in df_infr.iter_rows(named=True)}
        
        # Sipadan has a strict cabinet ban on overnight commercial lodging
        self.assertEqual(data["Sipadan"]["resort_count"], 0)
        self.assertEqual(data["Sipadan"]["estimated_room_capacity"], 0)
        
        # Major tourism hotspots have established room capacities
        self.assertGreater(data["Redang"]["estimated_room_capacity"], 500)
        self.assertGreater(data["Tioman"]["estimated_room_capacity"], 500)
        self.assertGreater(data["Perhentian"]["estimated_room_capacity"], 500)

if __name__ == "__main__":
    unittest.main()
