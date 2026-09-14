import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EconomicValuationTests(unittest.TestCase):
    def test_loader_returns_published_dmpm_values_and_scope(self):
        command = (
            "import json; "
            "from scripts.economic_valuation import load_dmpm_tev; "
            "print(json.dumps(load_dmpm_tev()))"
        )
        result = subprocess.run(
            [sys.executable, "-c", command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        valuation = json.loads(result.stdout)
        expected = {
            "Aesthetic value": 8_000_000_000,
            "Fisheries": 580_400_000,
            "Coastal protection": 56_250_000,
            "Carbon sequestration": 30_240_000,
            "Bequest value": 14_500_000,
            "Tourism": 4_600_000,
            "Biological support": 1_000_000,
        }
        actual = {
            component["component"]: component["annual_value_myr"]
            for component in valuation["components"]
        }

        self.assertEqual(actual, expected)
        self.assertEqual(valuation["calculated_total_myr"], 8_686_990_000)
        self.assertEqual(valuation["reported_total_myr"], 8_700_000_000)
        self.assertEqual(valuation["study_period"], "2011-2015")
        self.assertEqual(valuation["evaluated_archipelagos"], 6)
        self.assertEqual(
            valuation["source_url"],
            "https://wdpa.s3.amazonaws.com/Country_informations/MYS/"
            "TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf",
        )


if __name__ == "__main__":
    unittest.main()
