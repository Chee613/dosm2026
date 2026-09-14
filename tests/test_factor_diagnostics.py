import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import polars as pl


class FactorDiagnosticTests(unittest.TestCase):
    def test_factor_plot_renders_with_supported_matplotlib_api(self):
        from scripts.train_models import plot_factor_relationships

        transitions = pl.DataFrame({
            "noaa_max_dhw": [0.5, 0.8, 2.0, 3.0, 4.0, 6.0],
            "target_lcc_change_rate": [1.0, -1.0, 0.5, -2.0, -3.0, -4.0],
        })
        diagnostics = pl.DataFrame({
            "factor": ["noaa_max_dhw", "impact_anchor", "impact_trash", "impact_bleaching"],
            "statistic": [-0.8, -1.0, -0.5, -2.0],
        })
        heat_summary = pl.DataFrame({
            "heat_category": ["DHW < 1", "DHW 1–<4", "DHW ≥ 4"],
        })

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with (
                patch("scripts.train_models.OUTPUT", target),
                patch("scripts.train_models.FIGURES", target),
                patch("scripts.train_models.REPORTS_FIGURES", target),
                patch("scripts.train_models.DASHBOARD_FIGURES", target),
            ):
                plot_factor_relationships(transitions, diagnostics, heat_summary)

            self.assertTrue((target / "fig4_factor_relationships.png").exists())

    def test_dashboard_data_has_visitor_gap_and_economics(self):
        data_js_path = Path("dashboard/data.js")
        self.assertTrue(data_js_path.exists())
        data_js = data_js_path.read_text(encoding="utf-8")
        self.assertIn("window.TOURISM_DATA_GAP", data_js)
        self.assertIn("window.ECONOMIC_VALUATION", data_js)
        self.assertIn('"evaluated_archipelagos": 6', data_js)
        self.assertIn('"reported_total_myr": 8700000000', data_js)
        self.assertNotIn("window.NPV_TRADEOFF", data_js)
        self.assertNotIn("controllable_pct", data_js)
        self.assertNotIn("uncontrollable_pct", data_js)


if __name__ == "__main__":
    unittest.main()

