REEFSAFE — DOSM DATATHON 2026 DASHBOARD PACKAGE

PURPOSE
ReefSafe ranks monitored islands for field verification using observed Reef Check condition
and reported local stressors. NOAA heat remains descriptive context. It does not calculate a legal carrying
capacity, prescribe closures, prove tourism causality, or estimate island-level revenue.

FILES
- Dashboard.xlsx: Interactive Excel workbook with an island dropdown, formula-linked
  indicators, native charts, priority table, historical data, and model diagnostics.
- Dashboard.pdf: Static one-page view of the dashboard.
- Data.csv: Corrected 404-row processed island-year dataset. It contains no fabricated
  tourism-pressure or GDP-intensity columns.
- ReefSafe_Reproducible_Pipeline.ipynb: Concise notebook that runs the tested scripts.
- README.txt: This guide.

HOW TO USE THE WORKBOOK
1. Open Dashboard.xlsx in Microsoft Excel.
2. On the Dashboard tab, change the yellow Selected island cell.
3. Read the observed condition, model screening result, uncertainty band, evidence, and
   recommended next step together.
4. Use High screening priority only to schedule verification. Check Source confidence on
   Priority_Data before acting.

MODEL CHECK
- Target: next observed annualized live-coral-cover change.
- Validation: expanding-year, past-only evaluation on the latest five target years.
- Forward evaluation observations: 183.
- Gradient Boosting MAE: 5.862 percentage points/year.
- Mean baseline MAE: 5.991 percentage points/year.
- Improvement over baseline: 2.1%.
- Forward-test R²: 0.069.

Because performance is weak, rankings must not be treated as forecasts or enforcement
decisions. The workbook keeps these diagnostics visible.

FACTOR RELATIONSHIPS AND ASSUMPTIONS
- Factor relationships use current-observation evidence against the next observed coral
  change. They are descriptive associations, not causal effects.
- NOAA maximum DHW has a weak negative Spearman relationship with the next change; heat
  bands and sample sizes are shown in the notebook. NOAA is excluded from the production
  model while written eligibility confirmation remains pending.
- Regional NOAA matching, survey comparability, irregular intervals, narrative reporting,
  missing-value imputation, temporal transfer, and the top-quartile workload threshold are
  explicit assumptions. See the notebook and repository docs/assumptions.md.

DATA PROVENANCE
- Reef Check Malaysia annual survey reports: ecological observations and narrative flags.
- NOAA Coral Reef Watch: regional temperature anomaly and Degree Heating Weeks.
- OpenDOSM tourism/GDP series: descriptive context only; not downscaled to islands.
- Department of Marine Park Malaysia: source for the rounded RM8.7 billion annual
  total-economic-value benchmark across six evaluated marine-park archipelagos.
- DOSM Datathon 2026 booklet: submission and evidence requirements.

SOFTWARE
Dashboard.xlsx uses Excel-compatible VLOOKUP, IFERROR, and TEXT formulas and native charts.
No macros, add-ins, external links, or Power BI installation are required.
