import unittest
from scripts.economic_valuation import get_economic_pillars, simulate_npv_tradeoff

class TestEconomicValuation(unittest.TestCase):
    def test_economic_pillars_total(self):
        pillars = get_economic_pillars()
        self.assertIn("total_value_myr", pillars)
        self.assertAlmostEqual(pillars["total_value_myr"], 8.7e9, delta=0.2e9)
        self.assertEqual(len(pillars["breakdown"]), 4)
        # Tourism should be ranked #1
        self.assertEqual(pillars["breakdown"][0]["pillar"], "Marine Tourism & Recreation")
        self.assertGreater(pillars["breakdown"][0]["value_myr"], 4.0e9)
        
    def test_npv_tradeoff_preservation_wins(self):
        tradeoff = simulate_npv_tradeoff(years=20)
        self.assertIn("npv_sustainable_management_myr", tradeoff)
        self.assertIn("npv_no_action_myr", tradeoff)
        self.assertGreater(tradeoff["npv_sustainable_management_myr"], tradeoff["npv_no_action_myr"])
        self.assertIn("yearly_trajectories", tradeoff)
        self.assertEqual(len(tradeoff["yearly_trajectories"]), 20)

if __name__ == "__main__":
    unittest.main()
