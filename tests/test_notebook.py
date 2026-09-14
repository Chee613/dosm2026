import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_reproducible_pipeline.ipynb"
ASSUMPTIONS = ROOT / "docs" / "assumptions.md"


class NotebookTests(unittest.TestCase):
    def test_notebook_has_all_7_phases_and_core_analyses(self):
        self.assertTrue(NOTEBOOK.exists())
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        text = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        
        # Check all 7 phases exist
        for phase in (
            "Phase 1: Data Provenance",
            "Phase 2: Preprocessing",
            "Phase 3: Exploratory Data Analysis",
            "Phase 4: Feature Engineering",
            "Phase 5: Factor Relationships",
            "Phase 6: Economic Valuation",
            "Phase 7: Predictive Modeling",
        ):
            self.assertIn(phase, text)
            
        # Check key topics and required narrative elements
        self.assertIn("Tourism Data Gap", text)
        self.assertIn("archive.data.gov.my", text)
        self.assertIn("Controllable vs Uncontrollable", text)
        self.assertIn("RM 8.7 Billion", text)
        self.assertIn("NPV", text)
        self.assertIn("scripts.run_preprocessing", text)
        self.assertIn("scripts.train_models", text)

        assumptions = ASSUMPTIONS.read_text(encoding="utf-8")
        self.assertIn("Tourism data gap", assumptions)
        self.assertIn("Economic valuation", assumptions)


if __name__ == "__main__":
    unittest.main()
