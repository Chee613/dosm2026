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
        
        # Overview: map with legend, field queue, and the two economics cards.
        self.assertIn('id="map"', html)
        self.assertIn('id="map-legend"', html)
        self.assertIn('id="top-priority-table"', html)
        self.assertIn('id="reef-economy-card"', html)
        self.assertIn('id="season-rest-card"', html)
        self.assertIn('id="rest-bars"', html)
        self.assertIn("Top 5 field-verification queue", html)
        for part in ('id="reef-potential-card"', 'id="reef-potential-donut"'):
            self.assertGreater(html.index(part), html.index('id="tab-overview"'))
            self.assertLess(html.index(part), html.index('id="tab-diagnostics"'))
        # The DMPM valuation card is removed from the dashboard for now.
        self.assertNotIn('id="economic-pillars-chart"', html)

        # Summary cards belong to the Overview tab only.
        overview = html.index('id="tab-overview"')
        self.assertGreater(html.index('class="kpi-grid"'), overview)
        self.assertLess(html.index('class="kpi-grid"'), html.index('id="tab-diagnostics"'))

        # Island view: one card, history chart on top, facts and stress breakdown below.
        self.assertIn('id="island-select"', html)
        card = html.index('id="next-observation-card"')
        chart = html.index('id="island-history-chart"')
        self.assertLess(card, chart)
        self.assertLess(chart, html.index('id="unit-cover"'))
        self.assertLess(chart, html.index('id="stress-breakdown"'))
        self.assertIn('id="legend-predicted"', html)
        self.assertLess(html.index('id="unit-top-stressor"'), html.index('id="unit-evidence"'))

        # Evidence view: data gap, associations, and honest validation.
        self.assertIn('src="figures/01_tourism_data_gap.png"', html)
        self.assertIn('id="factor-relationships-grid"', html)
        self.assertIn('id="model-benchmark-table"', html)
        self.assertIn('id="figure-lightbox"', html)


        for unsupported in (
            'id="npv-tradeoff-chart"',
            'id="controllable-factor-bar"',
            'id="island-infrastructure-card"',
            'id="btn-open-memo"',
            "visitor quota",
            "carrying capacity",
        ):
            self.assertNotIn(unsupported, html.lower())

    def test_app_js_handles_economics_and_navigation(self):
        self.assertTrue(APP_JS.exists())
        js = APP_JS.read_text(encoding="utf-8")
        self.assertIn("View Diagnostics", js)
        self.assertNotIn("≈", js)
        for unsupported in ("NPV_TRADEOFF", "controllable_pct", "uncontrollable_pct", "memo", "quota"):
            self.assertNotIn(unsupported, js)

        server = SERVER.read_text(encoding="utf-8")
        for unsupported in ("78%", "RM 842.5", "quota", "carrying capacity"):
            self.assertNotIn(unsupported.lower(), server.lower())

    def test_evidence_figures_exist_and_have_captions(self):
        import re
        html = HTML_FILE.read_text(encoding="utf-8")
        start = html.index('id="tab-science"')
        evidence = html[start:html.index("</section>", start)]
        sources = re.findall(r'<img src="(figures/[^"]+)"', evidence)
        self.assertEqual(len(sources), 10)
        for src in sources:
            self.assertTrue((ROOT / "dashboard" / src).exists(), src)
        self.assertEqual(evidence.count('class="figure-desc"'), 10)
        self.assertEqual(evidence.count('class="evidence-section-title'), 4)


if __name__ == "__main__":
    unittest.main()
