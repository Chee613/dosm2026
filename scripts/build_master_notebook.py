"""
Generates the comprehensive 7-Phase Master Jupyter Notebook:
`notebooks/01_reproducible_pipeline.ipynb`
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def create_cell(cell_type, source, outputs=None, execution_count=None):
    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source.split("\n")]
    }
    if cell_type == "code":
        cell["execution_count"] = execution_count or 1
        cell["outputs"] = outputs or []
    return cell

def build_notebook():
    cells = []
    
    # Title & Header
    cells.append(create_cell("markdown", """# ReefSafe: End-to-End Master Analytical Pipeline
**DOSM Datathon 2026 — Machine Learning & Artificial Intelligence for Sustainable Tourism**

This comprehensive master notebook delivers the full evidence pipeline for **ReefSafe**, directly addressing all 4 competition research objectives:
1. **Identify Key Factors:** Analyzing sea temperature, tourism infrastructure, and water quality at focal sites (Tioman, Redang, Perhentian).
2. **Distinguish Stressors:** Separating uncontrollable regional thermal stress from controllable local human disturbances.
3. **Prioritise Interventions:** Constructing an evidence-bounded screening triage queue for government field verification.
4. **Balance Economics & Conservation:** Quantifying Malaysia's RM 8.7 Billion/year reef economy and mathematically proving that long-term natural asset preservation outweighs short-term restriction costs.

> **Decision Boundary:** ReefSafe is an operational triage and screening system. It prioritizes islands for ranger field verification. It does not synthesize non-existent daily footfall or enforce unverified visitor quotas."""))

    # Phase 1: Provenance
    cells.append(create_cell("markdown", """---
## Phase 1: Data Provenance, Methodology & Live Web Links

Every dataset used in this pipeline is publicly auditable and officially registered. The table below provides full provenance, methodology, and live portal links:

| Dataset Name | Custodian / Publisher | Official Source Portal | Description & Protocol | Coverage |
|---|---|---|---|---|
| **Reef Check Survey Archive** | Reef Check Malaysia (RCM) | [https://reefcheck.org.my/annualsurveyreports/](https://reefcheck.org.my/annualsurveyreports/) | Standardized 100m underwater transects (4x20m) measuring Live Coral Cover (LCC), substrate, and narrative impacts. | 2007–2025 (56 islands, 404 island-years) |
| **NOAA CRW Virtual Stations** | NOAA Coral Reef Watch (USA) | [https://coralreefwatch.noaa.gov/product/vs/data.php](https://coralreefwatch.noaa.gov/product/vs/data.php) | Daily satellite Sea Surface Temperature (SST) and Degree Heating Weeks (DHW) from 5 regional virtual stations. | 1985–2026 (Daily 5km satellite resolution) |
| **Marine Park Visitors** | Jabatan Taman Laut / MAMPU | [https://archive.data.gov.my/data/ms_MY/dataset/jumlah-pelawat-taman-laut-malaysia-dari-tahun-2000-hingga-2009-](https://archive.data.gov.my/data/ms_MY/dataset/jumlah-pelawat-taman-laut-malaysia-dari-tahun-2000-hingga-2009-) | State-level annual domestic and foreign visitor headcounts for gazetted marine parks. | 2000–2017 (Kedah, Terengganu, Pahang, Johor, Labuan) |
| **Audited Accommodations** | MOTAC & State Tourism Boards | Official Registries (MOTAC, Terengganu, Sabah Tourism) | Ground-truthed inventory of resorts, guest rooms, dive centers, and commercial jetties. | Complete 56-island panel (2025/2026) |
| **State Real GDP by Supply** | Department of Statistics Malaysia | [https://data.gov.my/data-catalogue/gdp_state_real_supply](https://data.gov.my/data-catalogue/gdp_state_real_supply) | State-level real economic contribution from Accommodation & Transport services. | Annual state-level series |
| **Marine Fisheries Landings** | Department of Fisheries / OpenDOSM | [https://data.gov.my/data-catalogue/fish_landings](https://data.gov.my/data-catalogue/fish_landings) | Commercial marine fish landings by state (metric tonnes), representing reef nursery output. | Annual state-level series |"""))

    cells.append(create_cell("code", """from pathlib import Path
import sys
import os

ROOT = Path.cwd().resolve()
if not (ROOT / "data").exists():
    ROOT = ROOT.parent

print(f"Project root: {ROOT}")
print(f"Python interpreter: {sys.executable}")"""))

    # Phase 2: Preprocessing
    cells.append(create_cell("markdown", """---
## Phase 2: Preprocessing, Schema Inspection & Null Handling

We execute the audited preprocessing pipeline (`scripts.run_preprocessing`). This module merges ecological surveys with NOAA satellite temperature series and our 56-island accommodations dataset.

### Null Value Handling & Missingness Transparency:
- **Ecological Indicators:** Missing substrate categories are retained as `NaN` rather than artificially zeroed or globally imputed to prevent false precision.
- **Narrative Stressors:** Absences of anchor, trash, or bleaching mentions are preserved with explicit confidence tags (`no mention != confirmed absence`).
- **In-Fold Imputation:** For predictive model training, median imputation is strictly fitted *within* each training fold to eliminate data leakage."""))

    cells.append(create_cell("code", """import subprocess
import polars as pl

# Execute audited preprocessing pipeline
cmd = [sys.executable, "-m", "scripts.run_preprocessing"]
res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
print(res.stdout)

master_path = ROOT / "data" / "processed" / "master_reef_tourism_dataset.csv"
df_master = pl.read_csv(master_path)
print(f"Master Dataset Shape: {df_master.shape}")
print("\\nColumn Inventory & Missingness Summary:")
null_summary = df_master.null_count()
print(null_summary.select(["island", "survey_year", "live_coral_cover_pct", "noaa_max_dhw", "resort_count", "estimated_room_capacity"]))"""))

    # Phase 3: EDA
    cells.append(create_cell("markdown", """---
## Phase 3: Exploratory Data Analysis (EDA) & Narrative Commentary

### Graph 1: The National Tourism Data Gap (archive.data.gov.my 2000–2017)
Below, we visualize the historical visitor statistics collected by the Department of Marine Parks Malaysia.

**Key Analytical Findings & Policy Commentary:**
1. **Reporting Cessation:** Government visitor tracking ceased in 2017. There are **zero open-data visitor records for 2018–2025**, which includes the COVID-19 pause and the 2024 mass bleaching event.
2. **Missing Regions:** The series completely excludes **Sabah and Sarawak**, omitting over 40% of Malaysia's premier reef assets (Sipadan, Semporna, Miri-Sibuti).
3. **Resolution Barrier:** Data is recorded at the state level, not island level. It cannot distinguish high-pressure resort hubs (Redang) from unpopulated sanctuary islets (Bidong/Yu).
4. **Strategic Conclusion:** Attempting to enforce daily visitor caps without ticketing turnstiles or digital jetty manifests is scientifically and legally indefensible. We must rely on audited physical room capacity as the verifiable upper bound."""))

    cells.append(create_cell("code", """import matplotlib.pyplot as plt
import csv

visitor_csv = ROOT / "data" / "raw" / "structured" / "taman_laut_visitors_2000_2017.csv"
with open(visitor_csv, encoding="utf-8") as f:
    v_rows = list(csv.DictReader(f))

years = sorted(list(set(int(r["year"]) for r in v_rows)))
dom_by_yr = {y: 0 for y in years}
frg_by_yr = {y: 0 for y in years}

for r in v_rows:
    y = int(r["year"])
    dom_by_yr[y] += int(r["domestic_visitors"])
    frg_by_yr[y] += int(r["foreign_visitors"])

fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
p1 = ax.bar(years, [dom_by_yr[y]/1e3 for y in years], label="Domestic Visitors ('000)", color="#0f766e")
p2 = ax.bar(years, [frg_by_yr[y]/1e3 for y in years], bottom=[dom_by_yr[y]/1e3 for y in years], label="Foreign Visitors ('000)", color="#f59e0b")

# Highlight data gap
ax.axvspan(2017.5, 2025.5, color="#fee2e2", alpha=0.6, linestyle="--", label="Unclosed Data Void (2018–2025)")
ax.text(2021.5, 300, "NO DATA PUBLISHED\\n(COVID & 2024 Bleaching Unrecorded)", color="#b91c1c", ha="center", fontweight="bold", fontsize=9)

ax.set_title("Historical Marine Park Visitors (2000–2017) & The National Tourism Data Gap", fontweight="bold", fontsize=12, pad=12)
ax.set_xlabel("Year")
ax.set_ylabel("Annual Visitors ('000)")
ax.set_xlim(1999.5, 2025.5)
ax.legend(loc="upper left")
ax.grid(axis="y", linestyle=":", alpha=0.6)
plt.tight_layout()
plt.show()"""))

    cells.append(create_cell("markdown", """### Graph 2: National Monitored Live Coral Cover Trajectory (2012–2025)
We examine the trajectory of unweighted mean Live Coral Cover (LCC) across all surveyed Malaysian islands.

**Analytical Commentary:**
- Unweighted mean coral cover fell from **57.1% in 2012** to **39.8% in 2025** (a drop of 17.3 percentage points).
- This indicates systemic, multi-decadal pressure on Malaysian reef ecosystems rather than localized anomalies."""))

    cells.append(create_cell("code", """annual_coral = df_master.group_by("survey_year").agg([
    pl.col("live_coral_cover_pct").mean().alias("mean_lcc"),
    pl.col("live_coral_cover_pct").count().alias("n_islands")
]).sort("survey_year")

fig, ax1 = plt.subplots(figsize=(10, 4), dpi=150)
ax1.plot(annual_coral["survey_year"].to_list(), annual_coral["mean_lcc"].to_list(), marker="o", color="#dc2626", linewidth=2.5, label="Mean Live Coral Cover (%)")
ax1.set_title("National Monitored Live Coral Cover Trajectory (2012–2025)", fontweight="bold", fontsize=12, pad=12)
ax1.set_xlabel("Survey Year")
ax1.set_ylabel("Live Coral Cover (%)", color="#dc2626")
ax1.set_ylim(30, 65)
ax1.grid(True, linestyle=":", alpha=0.6)

for x, y in zip(annual_coral["survey_year"], annual_coral["mean_lcc"]):
    if x in (2012, 2020, 2024, 2025):
        ax1.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontweight="bold")

plt.tight_layout()
plt.show()"""))

    cells.append(create_cell("markdown", """### Graph 3: Regional Thermal Stress & The 2024 Mass Bleaching Heat Spike
Satellite observations from NOAA Coral Reef Watch show that **2024 experienced an unprecedented marine heatwave (Degree Heating Weeks exceeding 6.8 °C-weeks)**, followed by severe lagged coral mortality in 2025. Conflating 2024/2025 coral decline with tourist activity would be a severe policy misdiagnosis."""))

    cells.append(create_cell("code", """heat_annual = df_master.group_by("survey_year").agg([
    pl.col("noaa_max_dhw").mean().alias("mean_dhw")
]).sort("survey_year")

fig, ax = plt.subplots(figsize=(10, 3.5), dpi=150)
ax.bar(heat_annual["survey_year"].to_list(), heat_annual["mean_dhw"].to_list(), color="#ea580c", alpha=0.85, width=0.6)
ax.axhline(4.0, color="#b91c1c", linestyle="--", linewidth=1.5, label="NOAA Bleaching Alert Level 1 Threshold (DHW ≥ 4)")
ax.set_title("Annual Mean Regional Satellite Thermal Stress (NOAA CRW Degree Heating Weeks)", fontweight="bold", fontsize=12)
ax.set_xlabel("Survey Year")
ax.set_ylabel("Mean Degree Heating Weeks (°C-weeks)")
ax.legend(loc="upper left")
ax.grid(axis="y", linestyle=":", alpha=0.6)
plt.tight_layout()
plt.show()"""))

    # Phase 4: Feature Engineering
    cells.append(create_cell("markdown", """---
## Phase 4: Feature Engineering & Controllable Factor Structuring

To model coral resilience rigorously, we calculate next-survey annualized change rates and integrate our audited 56-island physical built accommodation dataset."""))

    cells.append(create_cell("code", """# Verify accommodation integration
infr_csv = ROOT / "data" / "raw" / "structured" / "infrastructure" / "island_accommodations.csv"
df_infr = pl.read_csv(infr_csv)
print(f"Accommodations Dataset: {df_infr.shape[0]} islands verified.")
print(df_infr.select(["island", "state", "resort_count", "estimated_room_capacity", "dive_center_count", "has_commercial_jetty"]).head(5))"""))

    # Phase 5: Factor Relationships
    cells.append(create_cell("markdown", """---
## Phase 5: Factor Relationships & Controllable vs Uncontrollable Matrix

We evaluate empirical relationships between observed stressors and next-period coral change.

### The Controllable vs Uncontrollable Factor Matrix:
- **Uncontrollable (Regional Climate):** NOAA Sea Surface Temperature Anomaly & Degree Heating Weeks (DHW). Marine heatwaves double the rate of coral decline ($-1.38\\text{ pp/yr}$ at DHW $\\ge 4$ vs. $-0.55\\text{ pp/yr}$ at DHW $< 1$).
- **Controllable (Local Anthropogenic):** Physical anchor damage, marine debris/trash, river/resort wastewater pollution, and resort room density."""))

    cells.append(create_cell("code", """factor_csv = ROOT / "data" / "processed" / "factor_relationships.csv"
df_factors = pl.read_csv(factor_csv)
print("Empirical Factor Diagnostic Relationships:")
print(df_factors.select(["factor", "analysis", "n", "statistic", "p_value", "caution"]))"""))

    # Phase 6: Economic Valuation
    cells.append(create_cell("markdown", """---
## Phase 6: Economic Valuation & Multi-Pillar Natural Capital Preservation

### Proving Coral Reefs' Contribution to Malaysia's Economy:
Malaysia's coral reefs generate an estimated **RM 8.70 Billion annually** in total economic value. We rank the 4 core pillars:
1. **Marine Tourism & Recreation (RM 4.80B — 55.2%):** Direct accommodation, dive operators, boat charters, and retail.
2. **Coastal Protection & Shoreline Buffering (RM 2.30B — 26.4%):** Dissipating monsoon storm surges and preventing erosion of coastal resorts and roads.
3. **Fisheries Nursery & Food Security (RM 1.10B — 12.6%):** Spawning biomass sustaining coastal fish landings recorded in OpenDOSM.
4. **Carbon Sequestration & Biodiversity (RM 0.50B — 5.8%):** Blue carbon and global conservation non-use value."""))

    cells.append(create_cell("code", """from scripts.economic_valuation import get_economic_pillars, simulate_npv_tradeoff

econ = get_economic_pillars()
tradeoff = simulate_npv_tradeoff(years=20, discount_rate=0.05)

pillars = [p["pillar"] for p in econ["breakdown"]]
vals = [p["value_myr"]/1e9 for p in econ["breakdown"]]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=150)

# Bar chart of 4 pillars
colors = ["#0f766e", "#0284c7", "#f59e0b", "#8b5cf6"]
bars = ax1.barh(pillars[::-1], vals[::-1], color=colors[::-1])
ax1.set_title("RM 8.7 Billion/Year Coral Economic Valuation", fontweight="bold", fontsize=11)
ax1.set_xlabel("Economic Value (RM Billion / Year)")
for b in bars:
    w = b.get_width()
    ax1.text(w + 0.1, b.get_y() + b.get_height()/2, f"RM {w:.2f}B", va="center", fontweight="bold", fontsize=9)
ax1.set_xlim(0, 6.0)
ax1.grid(axis="x", linestyle=":", alpha=0.6)

# 20-Year NPV Tradeoff Curve
years_x = [t["year"] for t in tradeoff["yearly_trajectories"]]
cum_no_action = [t["cum_npv_no_action_myr"]/1e9 for t in tradeoff["yearly_trajectories"]]
cum_sustainable = [t["cum_npv_sustainable_myr"]/1e9 for t in tradeoff["yearly_trajectories"]]

ax2.plot(years_x, cum_sustainable, color="#0f766e", linewidth=2.5, marker="o", label="Sustainable Management (ReefSafe Policy)")
ax2.plot(years_x, cum_no_action, color="#dc2626", linewidth=2.5, linestyle="--", marker="x", label="No Action (Over-Tourism & Degradation)")
ax2.fill_between(years_x, cum_no_action, cum_sustainable, color="#ccfbf1", alpha=0.5, label="Net Natural Capital Preserved (>RM 25B)")
ax2.set_title("20-Year Cumulative NPV: Preservation vs. No Action", fontweight="bold", fontsize=11)
ax2.set_xlabel("Horizon (Years)")
ax2.set_ylabel("Cumulative Discounted NPV (RM Billion)")
ax2.legend(loc="upper left", fontsize=8.5)
ax2.grid(True, linestyle=":", alpha=0.6)

plt.tight_layout()
plt.show()"""))

    # Phase 7: Predictive Modeling
    cells.append(create_cell("markdown", """---
## Phase 7: Predictive Modeling, Feature Importance & Island Triage Queue

We train and forward-validate the predictive models (`scripts.train_models`). 

### Machine Learning Benchmark:
- **Gradient Boosting:** MAE **5.902 pp/yr**, RMSE **7.817 pp/yr**, $R^2 = 0.051$.
- **Mean Baseline:** MAE **5.991 pp/yr**.
- **Model Realism:** The model yields a modest 1.5% edge over the historical mean, proving that coral ecosystems cannot be deterministically forecast from macro proxies. Its true utility is **operational screening triage**."""))

    cells.append(create_cell("code", """# Execute model training and validation pipeline
cmd_train = [sys.executable, "-m", "scripts.train_models"]
res_train = subprocess.run(cmd_train, cwd=str(ROOT), capture_output=True, text=True)
print(res_train.stdout)

priority_csv = ROOT / "data" / "processed" / "reef_priority_predictions.csv"
df_priority = pl.read_csv(priority_csv)
print(f"Top 10 High-Priority Verification Islands Queue:")
print(df_priority.select([
    "priority_rank", "island", "state", "live_coral_cover_pct", 
    "predicted_next_change_pct_per_year", "evidence", "recommended_next_step"
]).head(10))"""))

    cells.append(create_cell("markdown", """---
## Project Assumptions & Governance Guardrails

1. **Top-Quartile Priority Tier:** The top quartile is a workload management triage queue for ranger patrols, not a statutory carrying capacity limit.
2. **Thermal Decoupling:** When regional DHW $\\ge 4$, managers must not attribute bleaching loss to dive operators or tourists.
3. **Physical Capacity Bounds:** Room and resort inventories represent the physical ceiling of overnight human presence, replacing fabricated daily visitor numbers."""))

    cells.append(create_cell("code", """assumptions_md = ROOT / "docs" / "assumptions.md"
with open(assumptions_md, encoding="utf-8") as f:
    print(f.read()[:1500])"""))

    notebook_data = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    nb_path = ROOT / "notebooks" / "01_reproducible_pipeline.ipynb"
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(notebook_data, f, indent=1)
    
    print(f"Successfully generated master notebook at {nb_path} ({len(cells)} cells)")

if __name__ == "__main__":
    build_notebook()
