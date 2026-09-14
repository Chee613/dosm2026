import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_reproducible_pipeline.ipynb"
ASSUMPTIONS = ROOT / "docs" / "assumptions.md"


class NotebookTests(unittest.TestCase):
    def test_notebook_presents_four_evidence_bounded_objectives(self):
        self.assertTrue(NOTEBOOK.exists())
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        text = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
        outputs = [output for cell in notebook["cells"] for output in cell.get("outputs", [])]
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] == "code":
                compile("".join(cell["source"]), f"cell-{index}", "exec")

        self.assertFalse(any(output.get("output_type") == "error" for output in outputs))
        self.assertEqual(sum("image/png" in output.get("data", {}) for output in outputs), 10)

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

        for objective in (
            "Identify Associated Factors",
            "Compare Available Stressor Evidence",
            "Prioritise Field Verification",
            "Frame Conservation with Economic Context",
        ):
            self.assertIn(objective, text)

        self.assertIn("Tourism Data Gap", text)
        self.assertIn("RM8.7 billion", text)
        self.assertIn("six evaluated Malaysian marine-park archipelagos", text)
        self.assertIn("load_dmpm_tev", text)
        self.assertIn("best_candidate", text)

        for unsupported in (
            "Variance Attribution Percentage",
            "simulate_npv",
            "Net Capital Preserved",
            "Mandate Diver Quotas",
            "final_pipeline = make_pipeline",
            "RM 47.73",
        ):
            self.assertNotIn(unsupported, text)

        assumptions = ASSUMPTIONS.read_text(encoding="utf-8")
        self.assertIn("Tourism data gap", assumptions)
        self.assertIn("Economic valuation", assumptions)


if __name__ == "__main__":
    unittest.main()
