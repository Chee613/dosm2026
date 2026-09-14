import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "dashboard" / "index.html"
APP_JS = ROOT / "dashboard" / "app.js"

class TestDashboardUI(unittest.TestCase):
    def test_three_tabs_and_sections_present(self):
        self.assertTrue(HTML_FILE.exists())
        html = HTML_FILE.read_text(encoding="utf-8")
        
        # Check 3 Tab Navigation
        self.assertIn('data-tab="overview"', html)
        self.assertIn('data-tab="diagnostics"', html)
        self.assertIn('data-tab="science"', html)
        
        # Tab 1 elements: Map, Top 10 Queue, Economic Pillars, NPV Curve
        self.assertIn('id="map"', html)
        self.assertIn('id="economic-pillars-chart"', html)
        self.assertIn('id="npv-tradeoff-chart"', html)
        self.assertIn('id="top-priority-table"', html)
        
        # Tab 2 elements: Dropdown, Prediction, Controllable % Breakdown, Action Trigger, Built Infrastructure
        self.assertIn('id="island-select"', html)
        self.assertIn('id="controllable-factor-bar"', html)
        self.assertIn('id="action-trigger-card"', html)
        self.assertIn('id="island-infrastructure-card"', html)
        
        # Tab 3 elements: Tourism Data Gap, Factor Relationships, Model Benchmark
        self.assertIn('id="tourism-gap-chart"', html)
        self.assertIn('id="factor-relationships-grid"', html)
        self.assertIn('id="model-benchmark-table"', html)

    def test_app_js_handles_economics_and_tourism_gap(self):
        self.assertTrue(APP_JS.exists())
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn("ECONOMIC_VALUATION", js)
        self.assertIn("NPV_TRADEOFF", js)
        self.assertIn("TOURISM_DATA_GAP", js)
        self.assertIn("controllable_pct", js)

if __name__ == "__main__":
    unittest.main()
