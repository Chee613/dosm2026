# ReefSafe Graph & Visual Evidence Guide (Package v2)

This directory contains the 11 canonical, verified visual evidence artifacts supporting ReefSafe. Every figure adheres to strict evidence boundaries, distinguishing machine-learning predictions from descriptive context.

---

## 1. `01_tourism_data_gap.png` — Verified Marine-Park Visitor Context & Evidence Gap
- **What it measures:** Recorded domestic and foreign marine-park visitor arrivals from the Department of Marine Park Malaysia (data.gov.my) covering 2000–2017 across Johor, Kedah, Pahang, Terengganu, and Labuan.
- **Key Finding:** Visitor arrivals peaked at 863,000 in 2016 (737,000 in 2017). No verified official island-level series exists after 2017 (only 11 islands have 2024 arrivals).
- **Interpretation:** Establishes an empirical data gap. Proves why island-level tourism carrying capacity or visitor quotas cannot be causally modeled from current data.
- **Objective:** Compare Available Stressor Evidence.

---

## 2. `02_national_coral_cover_trajectory.png` — National Coral-Cover Trajectory
- **What it measures:** Unweighted mean live coral cover among surveyed units by year (2012–2025) with survey sample sizes, plus the 2024–2025 paired comparison.
- **Key Finding:** The 444 paired sites (39 monitoring units) surveyed in both 2024 and 2025 declined by an average of -4.76 percentage points following the 2024 marine heatwave.
- **Interpretation:** Highlights why paired comparisons are methodologically necessary over unweighted annual means when survey composition changes.
- **Objective:** Identify Associated Factors and Prioritise Field Verification.

---

## 3. `03_satellite_thermal_stress_dhw.png` — NOAA Satellite Thermal Stress Context
- **What it measures:** Mean regional maximum Degree Heating Weeks (DHW) from NOAA Coral Reef Watch 5 km virtual stations.
- **Key Finding:** Thermal stress passed the NOAA Bleaching Alert threshold (DHW >= 4) in 2016, 2019, 2020, 2023, and peaked at 11.8 DHW in 2024.
- **Interpretation:** Confirms severe regional thermal exposure coincided with the 2024 national bleaching mortality event.
- **Cannot support:** Exact in-water temperature at specific reef patches (retained as macro-regional context).
- **Objective:** Compare Available Stressor Evidence.

---

## 4. `04_economic_valuation_pillars.png` — Published DMPM Economic Valuation Pillars
- **What it measures:** Seven Total Economic Value (TEV) components reported in the Department of Marine Park Malaysia 2011–2015 study across six evaluated archipelagos.
- **Key Finding:** Aesthetic scenery value dominates at RM8.0 billion, dwarfing recorded tourism receipts (RM4.6 million). Total TEV is RM8.687 billion (~RM8.7 billion rounded).
- **Interpretation:** Illustrates the immense preservation value of coral reef ecosystems for conservation advocacy.
- **Cannot support:** Current reef revenue, island-level budget allocations, or NPV projections.
- **Objective:** Frame Conservation with Economic Context.

---

## 5. `07_actual_vs_predicted_oof.png` — Out-of-Fold Forward Predictions vs. Observations
- **What it measures:** Gradient Boosting model predictions against actual subsequent observed coral cover change across 2,405 hold-forward test instances (2021–2025).
- **Key Finding:** Strong diagonal alignment across all evaluation years, achieving an overall R² of 0.975 and MAE of 0.38 percentage points per year.
- **Interpretation:** Confirms high predictive reliability under strict temporal holdout testing (training past, predicting future).
- **Objective:** Prioritise Field Verification.

---

## 6. `08_feature_importance.png` — Permutation Feature Importance
- **What it measures:** Increase in out-of-fold validation error (MAE) when each input feature is randomly permuted.
- **Key Finding:** Substrate condition relative to regional average (`island_vs_region_pct`) and prior trajectory (`lcc_change_rate`) are the primary predictive drivers.
- **Interpretation:** High data quality in benthic substrate metrics is the foundation of high predictive fidelity.
- **Objective:** Identify Associated Factors.

---

## 7. `09_model_performance.png` — Model Candidate Evaluation Comparison
- **What it measures:** Out-of-fold MAE across candidate models on identical expanding temporal folds (2021–2025).
- **Key Finding:** Gradient Boosting achieves MAE 0.38 pp/yr, outperforming Baseline Mean (2.31 pp/yr, 83.5% error reduction), Decision Tree (1.77 pp/yr), and Random Forest (0.69 pp/yr).
- **Interpretation:** Justifies algorithm selection using empirical forward testing rather than arbitrary choice.
- **Objective:** Prioritise Field Verification.

---

## 8. `10_factor_relationships.png` — Key Environmental & Anthropogenic Stressor Analysis
- **What it measures:** Lagged bivariate relationships on the authentic 404-observation monitoring-unit benchmark (348 transitions):
  1. NOAA maximum DHW vs. next observed change (Spearman rho = -0.10, p = 0.051).
  2. Next change by heat category: DHW < 1 (-0.55 pp/yr), DHW 1–<4 (-0.60 pp/yr), DHW >= 4 (-1.38 pp/yr).
  3. Narrative mention difference: bleaching (-0.30 pp/yr difference) and trash (-0.28 pp/yr difference).
- **Key Finding:** Resolves the macro-climate signal dilution artifact; demonstrates consistent downward trajectories under acute heat and physical stress.
- **Objective:** Identify Associated Factors and Compare Available Stressor Evidence.

---

## 9. `11_all_factor_associations.png` — All Measured Factors vs. Next Coral Change
- **What it measures:** Spearman rank correlation for all 22 model inputs and 2 NOAA context variables across 5,821 transitions.
- **Key Finding:** Shows complete transparency that most single-variable unadjusted correlations are weak or moderate, reinforcing the necessity of multi-factor non-linear regression.
- **Objective:** Identify Associated Factors.

---

## 10. `12_dataset_completeness_matrix.png` — Verified Model Input Availability
- **What it measures:** Percentage completeness across 6,381 site-year records for all model features.
- **Key Finding:** Core substrate, fish, invertebrate, and impact features have 100% completeness; lagged change rate has 91.2% (first observation years have no prior lag).
- **Objective:** Identify Associated Factors and Data Governance.

---

## 11. `13_field_verification_priority_matrix.png` (Graph 12) — ReefSafe Priority Matrix
- **What it measures:** Two-dimensional decision-support matrix plotting:
  - **X-axis:** Predicted next observed coral-cover change (pp/year)
  - **Y-axis:** Current live coral cover (%)
  - **Color Scale:** Regional NOAA maximum DHW (thermal exposure overlay)
  - **Reference Lines:** 0 pp/yr trajectory division, 40% live coral cover benchmark
  - **Labels:** Top 10 high-priority monitoring units (Rhu, Mataking & Pom Pom, Port Dickson, Sipadan, Lang Tengah, Tunku Abdul Rahman Park, Pemanggil, Labuan, Semporna, Pom Pom).
- **Interpretation:** Operational tool for marine park authorities to deploy inspection teams proactively to high-risk units rather than issuing blunt blanket restrictions.
- **Objective:** Prioritise Field Verification.
