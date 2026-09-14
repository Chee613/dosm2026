# ReefSafe End-to-End System Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and integrate the complete ReefSafe evidence pipeline, including a comprehensive 7-phase educational Jupyter Notebook with all requested EDA/relationship/economic graphs, and an aligned 3-tab institutional decision dashboard.

**Architecture:** Refactor data extraction and preprocessing to incorporate the historical Marine Park visitor dataset (2000–2017) and 56-island accommodations dataset. Build the unified master notebook (`notebooks/01_reproducible_pipeline.ipynb`) rendering all 16 required visualizations with explicit narrative annotations. Restructure the web dashboard into 3 dedicated tabs (Tab 1: Economy & Map, Tab 2: Island Prediction & Controllable %, Tab 3: Factor Trends & Deep Diagnostics).

**Tech Stack:** Python 3.11+, Polars, Scikit-learn, Matplotlib, Vanilla HTML5/CSS3, JavaScript (ES6+), Leaflet.js, Unittest.

**Spec:** [docs/superpowers/specs/2026-09-14-reefsafe-end-to-end-architecture-design.md](file:///c:/Users/Chee/Documents/dosm2026/docs/superpowers/specs/2026-09-14-reefsafe-end-to-end-architecture-design.md)

## Global Constraints

- **No Fictional Daily Visitors:** Retain `island_accommodations.csv` as physical capacity ceilings. Never multiply rooms by arbitrary numbers to invent daily tourist footfall.
- **Full 16-Graph Coverage:** Ensure every single chart specified by the user (visitor gap, coral trajectory, heat history, 4 factor relationship plots, controllable matrix, 4-pillar economic ranking, NPV curve, feature importance, actual vs predicted, island % contributor gauges) is fully rendered in both the notebook and dashboard.
- **Strict Backward-Looking Evaluation:** Predictive models must use forward expanding-window validation (no future data leakage).
- **Zero Console Errors & Clean Test Suite:** All changes must pass `python -m unittest discover tests`.

---

## Required Visualizations Master Checklist

| # | Graph Name | Location in Notebook | Location in Dashboard |
|---|---|---|---|
| 1 | **Missingness / Null Inspection** | Phase 2 (Preprocessing) | Tab 3 (Diagnostics) |
| 2 | **The Tourism Data Gap (2000–2017)** | Phase 3 (EDA) | Tab 3 (Relationship Graphs) |
| 3 | **National Coral Cover Trajectory (2012–2025)** | Phase 3 (EDA) | Tab 1 (KPIs) & Tab 3 |
| 4 | **Thermal Heatwave & Bleaching Spike (2024–2025)** | Phase 3 (EDA) | Tab 3 (Factor Trends) |
| 5 | **Factor Relationship 1: NOAA DHW vs. Coral Change** | Phase 5 (Factor Analysis) | Tab 3 (Relationship Graphs) |
| 6 | **Factor Relationship 2: Anchor Damage vs. Coral Change** | Phase 5 (Factor Analysis) | Tab 3 (Relationship Graphs) |
| 7 | **Factor Relationship 3: Marine Debris/Trash vs. Coral Change** | Phase 5 (Factor Analysis) | Tab 3 (Relationship Graphs) |
| 8 | **Factor Relationship 4: River/Resort Runoff vs. Coral Change** | Phase 5 (Factor Analysis) | Tab 3 (Relationship Graphs) |
| 9 | **Controllable vs. Uncontrollable Factor Matrix** | Phase 5 (Factor Analysis) | Tab 3 (Diagnostics) |
| 10 | **RM 8.7B 4-Pillar Economic Valuation Ranking** | Phase 6 (Economics) | Tab 1 (Economy Section) |
| 11 | **Long-Term Preservation vs. Short-Term Sacrifice (NPV)** | Phase 6 (Economics) | Tab 1 (Trade-Off Curve) |
| 12 | **Gradient Boosting Feature Importance** | Phase 7 (Modeling) | Tab 3 (Model Performance) |
| 13 | **Model Forward Validation (Actual vs. Predicted)** | Phase 7 (Modeling) | Tab 3 (Model Performance) |
| 14 | **Island-Specific Contributor Breakdown (% Controllable)** | Phase 7 (Triage) | Tab 2 (Prediction Modal) |
| 15 | **Interactive 56-Island Leaflet Map** | Phase 7 (Triage) | Tab 1 (Hero Map) |
| 16 | **Top 10 Urgent Island Alert Queue** | Phase 7 (Triage) | Tab 1 (Alert Table) |

---

## Tasks

### Task 1: Data Provenance, Assumptions & Economic Valuation Engine

**Files:**
- Modify: `data/DATA_PROVENANCE.md`
- Modify: `docs/assumptions.md`
- Create: `scripts/economic_valuation.py`
- Create: `tests/test_economic_valuation.py`

**Interfaces:**
- Produces: `scripts.economic_valuation.get_economic_pillars()` -> `dict`
- Produces: `scripts.economic_valuation.simulate_npv_tradeoff(years=20, discount_rate=0.05)` -> `dict`

- [ ] **Step 1: Write failing unit test for economic valuation**

```python
# tests/test_economic_valuation.py
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
        
    def test_npv_tradeoff_preservation_wins(self):
        tradeoff = simulate_npv_tradeoff(years=20)
        self.assertIn("npv_sustainable_management_myr", tradeoff)
        self.assertIn("npv_no_action_myr", tradeoff)
        self.assertGreater(tradeoff["npv_sustainable_management_myr"], tradeoff["npv_no_action_myr"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_economic_valuation`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.economic_valuation'`

- [ ] **Step 3: Implement economic valuation logic and update docs**

Implement `scripts/economic_valuation.py` returning the RM 8.7B 4-pillar figures (Tourism RM 4.8B, Coastal Protection RM 2.3B, Fisheries RM 1.1B, Carbon RM 0.5B) and the 20-year NPV simulation comparison.
Update `data/DATA_PROVENANCE.md` and `docs/assumptions.md` with complete documentation for `archive.data.gov.my` marine park visitor series and economic parameters.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_economic_valuation`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add data/DATA_PROVENANCE.md docs/assumptions.md scripts/economic_valuation.py tests/test_economic_valuation.py
git commit -m "feat(economics): add 4-pillar economic valuation engine and update provenance registry"
```

---

### Task 2: Data Pipeline Integration & Export for Dashboard

**Files:**
- Modify: `scripts/pipeline.py`
- Modify: `scripts/build_web_dashboard_data.py`
- Modify: `tests/test_factor_diagnostics.py`

**Interfaces:**
- Consumes: `data/raw/structured/taman_laut_visitors_2000_2017.csv`
- Consumes: `data/raw/structured/infrastructure/island_accommodations.csv`
- Produces: `dashboard/data.js` (including visitor trend data, economic pillars, NPV curves, and island contributor % shares).

- [ ] **Step 1: Write failing test for new pipeline outputs**

```python
# tests/test_factor_diagnostics.py
def test_dashboard_data_has_visitor_gap_and_economics(self):
    import json
    from pathlib import Path
    data_js = Path("dashboard/data.js").read_text(encoding="utf-8")
    self.assertIn("window.TOURISM_DATA_GAP", data_js)
    self.assertIn("window.ECONOMIC_VALUATION", data_js)
    self.assertIn("window.NPV_TRADEOFF", data_js)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_factor_diagnostics.TestFactorDiagnostics.test_dashboard_data_has_visitor_gap_and_economics`
Expected: FAIL

- [ ] **Step 3: Update `scripts/build_web_dashboard_data.py`**

- Load `taman_laut_visitors_2000_2017.csv` and export annual visitor trends by state showing the 2017 cutoff and lack of Sabah/Sarawak.
- Integrate `scripts.economic_valuation` outputs into `dashboard/data.js`.
- Compute dynamic factor contribution percentages for each island:
  - % Uncontrollable Thermal Stress: based on normalized NOAA DHW.
  - % Controllable Local Disturbances: based on normalized Anchoring, Trash, Water Pollution, and Room Capacity.
- Export `window.TOURISM_DATA_GAP`, `window.ECONOMIC_VALUATION`, and updated `window.REEF_PREDICTIONS`.

- [ ] **Step 4: Run script and tests to verify pass**

Run:
```powershell
python -m scripts.build_web_dashboard_data
python -m unittest tests.test_factor_diagnostics
```
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add scripts/build_web_dashboard_data.py tests/test_factor_diagnostics.py dashboard/data.js
git commit -m "feat(pipeline): export tourism gap, economic pillars, and island contributor % to dashboard"
```

---

### Task 3: Comprehensive 7-Phase Master Jupyter Notebook

**Files:**
- Overwrite: `notebooks/01_reproducible_pipeline.ipynb`
- Modify: `tests/test_notebook.py`

**Interfaces:**
- Renders: All 16 required visualizations with explicit narrative markdown commentaries explaining:
  - The Tourism Data Gap (why visitor data is insufficient and unpredictable).
  - Coral Coverage Decline (57.1% to 39.8%).
  - Bleaching & Thermal Shock (2024 peak & 2025 lag).
  - Factor relationships (Heat, Anchor, Trash, Runoff) and Controllable vs. Uncontrollable matrix.
  - 4-Pillar Economic Valuation & NPV Trade-Off.
  - Predictive Model Feature Importance & Island Triage Queue.

- [ ] **Step 1: Update `tests/test_notebook.py` to assert all phases and figures exist**

```python
# tests/test_notebook.py
import json
import unittest
from pathlib import Path

class TestMasterNotebook(unittest.TestCase):
    def test_notebook_structure_and_headings(self):
        nb_path = Path("notebooks/01_reproducible_pipeline.ipynb")
        self.assertTrue(nb_path.exists())
        data = json.loads(nb_path.read_text(encoding="utf-8"))
        cell_sources = [c["source"] for c in data["cells"]]
        full_text = "\n".join("".join(s) for s in cell_sources)
        
        # Check all 7 phases exist
        self.assertIn("Phase 1: Data Provenance", full_text)
        self.assertIn("Phase 2: Preprocessing", full_text)
        self.assertIn("Phase 3: Exploratory Data Analysis", full_text)
        self.assertIn("Phase 4: Feature Engineering", full_text)
        self.assertIn("Phase 5: Factor Relationships", full_text)
        self.assertIn("Phase 6: Economic Valuation", full_text)
        self.assertIn("Phase 7: Predictive Modeling", full_text)
        
        # Check critical topics and graphs are addressed
        self.assertIn("Tourism Data Gap", full_text)
        self.assertIn("Controllable vs Uncontrollable", full_text)
        self.assertIn("RM 8.7 Billion", full_text)
        self.assertIn("NPV", full_text)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_notebook`
Expected: FAIL on missing phases.

- [ ] **Step 3: Construct the 7-Phase master notebook**

Build `notebooks/01_reproducible_pipeline.ipynb` with complete Python execution cells and rich markdown narratives:
- Phase 1: Interactive provenance table with working URLs.
- Phase 2: Loading raw files, checking missingness, schema verification.
- Phase 3: Visual EDA:
  - Chart 1: Marine Park visitor shortfall (2000–2017) with markdown explaining why visitor data is insufficient and stopped post-2017.
  - Chart 2: National mean live coral cover trend (2012–2025).
  - Chart 3: Thermal stress history (2024 heatwave and 2025 decline).
- Phase 4: Feature engineering: merging accommodations, calculating annualized change rates.
- Phase 5: Factor relationships:
  - Scatter plots & boxplots for DHW, Anchor, Trash, and Runoff against coral change.
  - Summary table distinguishing Controllable vs. Uncontrollable factors.
- Phase 6: Economic valuation:
  - Bar chart ranking the 4 pillars (RM 8.7B total).
  - 20-year NPV curve showing sustainable management out-values no-action degradation.
- Phase 7: Forward predictive modeling:
  - Gradient Boosting training and feature importance chart.
  - Actual vs. predicted evaluation.
  - 56-island priority queue with % contributor breakdown and recommended actions.

- [ ] **Step 4: Execute notebook verification**

Run: `python -m unittest tests.test_notebook`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add notebooks/01_reproducible_pipeline.ipynb tests/test_notebook.py
git commit -m "feat(notebook): implement comprehensive 7-phase master analysis notebook with all required graphs"
```

---

### Task 4: Interactive Web Dashboard 3-Tab Realignment

**Files:**
- Modify: `dashboard/index.html`
- Modify: `dashboard/app.js`
- Modify: `dashboard/style.css`

**Interfaces:**
- Consumes: `dashboard/data.js`
- Renders:
  - Tab 1: Live Overview & RM 8.7B Reef-Adjacent Economy (Leaflet Map, Top 10 High-Risk Alert Queue, Economic Pillars Breakdown, Long-Term vs. Short-Term NPV Curve).
  - Tab 2: Island Prediction & Diagnostics Modal (Island Dropdown, Coral Coverage Prediction with error bounds, Dynamic % Controllable vs % Uncontrollable Contributors, Action Trigger Card, Built Accommodations Card).
  - Tab 3: Scientific Diagnostics & Factor Trends (Historical Factor Trends, 3 Core Relationship Graphs: Tourism Gap, Factors-to-Coral, Coral-to-Economy, and Model Benchmark).

- [ ] **Step 1: Write integration test for dashboard HTML elements**

```python
# tests/test_dashboard_ui.py
import unittest
from pathlib import Path

class TestDashboardUI(unittest.TestCase):
    def test_three_tabs_and_sections_present(self):
        html = Path("dashboard/index.html").read_text(encoding="utf-8")
        self.assertIn('id="tab-overview"', html)
        self.assertIn('id="tab-diagnostics"', html)
        self.assertIn('id="tab-science"', html)
        self.assertIn('id="economic-pillars-chart"', html)
        self.assertIn('id="npv-tradeoff-chart"', html)
        self.assertIn('id="controllable-factor-bar"', html)
        self.assertIn('id="tourism-gap-chart"', html)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_dashboard_ui`
Expected: FAIL

- [ ] **Step 3: Update `dashboard/index.html`, `dashboard/app.js`, and `dashboard/style.css`**

- Refactor navigation into 3 clean, institutional tabs:
  1. `Executive Overview & Economy`
  2. `Island Predictions & Diagnostics`
  3. `Scientific Evidence & Factor Trends`
- In Tab 1: Add the Economic Impact Section (4-pillar breakdown chart and 20-year NPV curve), along with the Top 10 High-Risk table and Leaflet Map.
- In Tab 2: Enhance the island prediction card with a dynamic % Controllable vs. % Uncontrollable breakdown bar, actionable intervention trigger, and built accommodation metrics.
- In Tab 3: Add the 3 Core Relationship Graphs (Tourism Data Gap 2000–2017, Factors to Coral, Coral to Economy) and Model Benchmark Comparison.

- [ ] **Step 4: Run UI test to verify pass**

Run: `python -m unittest tests.test_dashboard_ui`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add dashboard/index.html dashboard/app.js dashboard/style.css tests/test_dashboard_ui.py
git commit -m "feat(ui): align 3-tab dashboard with economic valuation, island contributor % and factor trends"
```

---

### Task 5: End-to-End Regression Testing & Visual Verification

**Files:**
- Verify: Full test suite (`tests/`)
- Verify: Local web dashboard at `http://localhost:8088/`

- [ ] **Step 1: Run complete automated test suite**

Run: `python -m unittest discover tests`
Expected: All tests pass with 0 errors.

- [ ] **Step 2: Start local dashboard server and verify endpoints**

Run: `python dashboard_server.py`
Verify in browser subagent:
- Tab 1 displays map, top 10 queue, RM 8.7B economic chart, and NPV curve.
- Tab 2 displays island dropdown, predicted change, % contributor shares, and action recommendations.
- Tab 3 displays the tourism data gap graph, factor relationship graphs, and model performance metrics.

- [ ] **Step 3: Commit and finalize development**

```bash
git add .
git commit -m "chore(release): verify all 16 graphs, 7-phase notebook, and 3-tab dashboard"
```
