import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "dashboard" / "index.html"
APP_JS = ROOT / "dashboard" / "app.js"
SERVER = ROOT / "dashboard_server.py"

class TestDashboardUI(unittest.TestCase):
    def test_three_tabs_and_sections_present(self):
        self.assertTrue(HTML_FILE.exists())
        html = HTML_FILE.read_text(encoding="utf-8")
        
        # Check 3 Tab Navigation
        self.assertIn('data-tab="overview"', html)
        self.assertIn('data-tab="diagnostics"', html)
        self.assertIn('data-tab="science"', html)
        
        # Overview: map, field queue, and source-backed economic context.
        self.assertIn('id="map"', html)
        self.assertIn('id="economic-pillars-chart"', html)
        self.assertIn('id="top-priority-table"', html)

        # Island view: one next-observation estimate and its empirical range.
        self.assertIn('id="island-select"', html)
        self.assertIn('id="next-observation-card"', html)
        self.assertIn('id="island-history-chart"', html)

        # Evidence view: data gap, associations, and honest validation.
        self.assertIn('id="tourism-gap-chart"', html)
        self.assertIn('id="factor-relationships-grid"', html)
        self.assertIn('id="model-benchmark-table"', html)

        for unsupported in (
            'id="npv-tradeoff-chart"',
            'id="controllable-factor-bar"',
            'id="island-infrastructure-card"',
            'id="btn-open-memo"',
            "visitor quota",
            "carrying capacity",
        ):
            self.assertNotIn(unsupported, html.lower())

    def test_app_js_handles_economics_and_tourism_gap(self):
        self.assertTrue(APP_JS.exists())
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn("ECONOMIC_VALUATION", js)
        self.assertIn("TOURISM_DATA_GAP", js)
        for unsupported in ("NPV_TRADEOFF", "controllable_pct", "uncontrollable_pct", "memo", "quota"):
            self.assertNotIn(unsupported, js)

        server = SERVER.read_text(encoding="utf-8")
        for unsupported in ("78%", "RM 842.5", "quota", "carrying capacity", "gemini"):
            self.assertNotIn(unsupported.lower(), server.lower())

if __name__ == "__main__":
    unittest.main()
