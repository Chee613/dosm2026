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
            with patch("scripts.train_models.OUTPUT", target), patch("scripts.train_models.FIGURES", target):
                plot_factor_relationships(transitions, diagnostics, heat_summary)

            self.assertTrue((target / "fig4_factor_relationships.png").exists())


if __name__ == "__main__":
    unittest.main()
