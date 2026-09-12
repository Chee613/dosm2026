# ReefSafe — DOSM Datathon 2026

ReefSafe is an evidence-led screening tool for deciding which monitored Malaysian islands should receive earlier reef field checks. It combines Reef Check observations with NOAA thermal-stress records and keeps OpenDOSM tourism/GDP data as descriptive context only.

## Decision boundary

- The model predicts the next observed annualized live-coral-cover change.
- Evaluation is past-only: every test year is trained only on earlier target years.
- The output is a field-verification priority, not a visitor quota, closure order, causal attribution, or island-level economic estimate.
- No fabricated tourism-pressure or GDP-intensity variables are used.

## Current evidence

- 404 island-year observations, 56 islands, 2012–2025.
- 348 next-observation transitions; 183 observations in the five forward-test years.
- Best model: Gradient Boosting, MAE 5.902 pp/year, RMSE 7.817 pp/year, R² 0.051.
- Mean baseline MAE: 5.991 pp/year. Improvement: 1.5%, so the model is screening-only.

## Reproduce

```powershell
python -m scripts.run_preprocessing
python -m scripts.train_models
python -m unittest
```

The concise notebook at `notebooks/01_reproducible_pipeline.ipynb` runs the same tested scripts. The interactive workbook source is `src/build_dashboard.mjs`; the report source is `src/generate_report.py`.

## Deliverables

- `output/TeamName_Datathon2026_Report.pdf` — verified 12-page report with factor diagnostics and assumptions.
- `dist/TeamName_Datathon2026_Dashboard.zip` — dashboard workbook, static PDF, corrected CSV, notebook, and README.
- `data/processed/model_evaluation_metrics.csv` — benchmark evidence.
- `data/processed/reef_priority_predictions.csv` — latest screening queue with prediction bands, evidence, and next steps.
- `data/processed/factor_relationships.csv` and `heat_category_summary.csv` — lagged descriptive associations with the next observation.
- `docs/assumptions.md` — explicit assumption, risk, and mitigation register.

## Source evidence

Raw files are retained under `data/raw/`: Reef Check Malaysia annual survey reports, NOAA Coral Reef Watch station series, OpenDOSM structured datasets, island coordinate mappings, and the DOSM Datathon 2026 booklet.
