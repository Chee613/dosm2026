import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_reproducible_pipeline.ipynb"
ASSUMPTIONS = ROOT / "docs" / "assumptions.md"


class NotebookTests(unittest.TestCase):
    def test_notebook_is_complete_and_uses_tested_pipeline(self):
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        text = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        for section in (
            "Data provenance",
            "Rebuild the processed data",
            "Integrity checks",
            "Forward-test model comparison",
            "Factor relationships",
            "Priority explorer",
            "Project assumptions",
            "Decision guardrails",
        ):
            self.assertIn(section, text)
        self.assertIn("scripts.run_preprocessing", text)
        self.assertIn("scripts.train_models", text)
        self.assertNotIn("GroupKFold", text)
        self.assertNotIn("RandomForestRegressor", text)

        assumptions = ASSUMPTIONS.read_text(encoding="utf-8")
        self.assertIn("NOAA regional station", assumptions)
        self.assertIn("top quartile", assumptions)


if __name__ == "__main__":
    unittest.main()
