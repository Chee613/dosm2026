# ReefSafe data acquisition and methodology

## Scope

This document records how every dataset in the ReefSafe repository was obtained, extracted, transformed and used. It distinguishes downloadable source data from one-off document extraction and from local files whose acquisition trail is incomplete.

ReefSafe predicts the next observed annualised change in live coral cover. It is a field-verification screening tool, not a causal tourism model, legal carrying-capacity model or island financial model.

## Dataset acquisition register

| Dataset | How the data was obtained | Local evidence | Use in ReefSafe | Source |
|---|---|---|---|---|
| Reef Check Malaysia annual surveys, 2007–2025 | Nineteen annual PDF reports were downloaded from the publisher. The PDFs were not scraped as web tables because the observations are embedded in prose, tables, vector charts and images. Two document-extraction pipelines were used and reconciled. | `data/raw/unstructured/reef_check_reports/`; `data/raw/structured/reef_check/ReefCheck_Malaysia_FINAL.xlsx` | Primary ecological input. The model-ready panel contains 404 monitoring-unit/year rows; per-island coverage begins in 2012 because earlier reports do not contain usable island tables. | [Reef Check Malaysia annual reports](https://reefcheck.org.my/annualsurveyreports/) |
| NOAA Coral Reef Watch 5 km virtual stations | Five regional station time-series files were directly downloaded as NOAA text files. This was file retrieval, not HTML scraping. Daily rows were parsed into annual maximum Degree Heating Weeks and annual mean sea-surface-temperature anomaly. | `data/raw/structured/noaa_crw/*.txt` | Descriptive heat context only. Excluded from production-model features while written DOSM eligibility confirmation is unavailable. | [NOAA Coral Reef Watch virtual stations](https://coralreefwatch.noaa.gov/product/vs/data.php) |
| Marine-park visitors, 2000–2009 | A published portal dataset was downloaded and retained locally as CSV. No page scraping was used. Only the years covered by the cited source are admitted. | `data/raw/structured/taman_laut_visitors_2000_2017.csv` | Historical aggregated tourism context only; never allocated to individual islands. | [Jabatan Taman Laut Malaysia / data.gov.my archive](https://archive.data.gov.my/data/ms_MY/dataset/jumlah-pelawat-taman-laut-malaysia-dari-tahun-2000-hingga-2009-) |
| Marine-park visitor extension, 2010–2017 | Present in the same local CSV, but no traceable publisher link or retrieval record verifies these rows. | `data/raw/structured/taman_laut_visitors_2000_2017.csv` | Excluded from analysis, charts, model features and claims. | No verified source link in the repository. |
| OpenDOSM state GDP | Previously downloaded from the data catalogue and stored locally as JSON. The exact historical retrieval command and date were not retained. | `data/raw/structured/opendosm/gdp_state_real_supply.json` | State-level descriptive context only; not downscaled to reefs. | [Annual real GDP by state and sector](https://data.gov.my/data-catalogue/gdp_state_real_supply) |
| OpenDOSM marine fish landings | Direct catalogue CSV download retained locally. No custom scraper is required because data.gov.my provides downloadable files and API access. | `data/raw/structured/opendosm/fish_landings.csv` | Descriptive context only; landings are not reef-specific catches. | [Monthly marine fish landings by state](https://data.gov.my/data-catalogue/fish_landings) |
| OpenDOSM river-basin pollution | Direct catalogue CSV download retained locally. No custom scraper is required. | `data/raw/structured/opendosm/water_pollution_basin.csv` | Descriptive context only; mainland basin observations are not island wastewater measurements. | [River-basin pollution monitoring](https://data.gov.my/data-catalogue/water_pollution_basin) |
| DMPM marine-biodiversity economic valuation | The primary PDF was downloaded directly from the archived source. Seven published annual value components were transcribed with their page numbers and checked against the reported rounded total. | `data/raw/unstructured/economic_valuation/TOTAL_ECONOMIC_VALUE_OF_MARINE_BIODIVERSITY.pdf`; `data/raw/structured/economic_valuation/dmpm_tev_2011_2015.csv` | Historical economic context for six evaluated archipelagos. No island allocation, avoided-loss estimate or NPV is calculated. | [Department of Marine Park Malaysia valuation PDF](https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf) |
| Island coordinates and marine-park mapping | A 56-island local reference table was manually assembled before the current reproducible pipeline. The repository does not retain a retrieval script or independently verifiable source URL. | `data/raw/structured/geocoding/island_coordinates.csv` | Used for joins, mapping and geographic model fields. This acquisition gap must be disclosed and the coordinates should be independently checked before regulatory use. | No verified external source link in the repository. |
| Island accommodation inventory | Local manual compilation. The repository has no reproducible scrape, registry query, retrieval date or source-by-row audit trail. | `data/raw/structured/infrastructure/island_accommodations.csv` | Excluded from model features, charts, ranking and policy claims. | No verified source link in the repository. |

## Reef Check PDF extraction

### Pipeline A: direct PDF parsing

`pdfplumber` extracted words with page coordinates. Words were rebuilt into visual lines instead of relying on ordinary PDF text order, which can mix two-column charts with prose.

- For 2013–2019 tables, headers and nearby value rows were matched while handling missing percent signs, glued labels and fractional values.
- For 2020–2025 pie charts, vector-path angles and fill colours were converted into the six substrate groups and rejected when the groups did not sum to approximately 100%.
- For 2023–2025 icon-labelled fish and invertebrate charts, values were matched to icons by position and canonical species order.

### Pipeline B: Markdown extraction

The same PDFs were converted with Open Data Loader to Markdown and structured page elements. Tables were flattened, chart titles and data rows were collected separately, and each row was assigned to the nearest title of the same chart type.

### Reconciliation and confidence

The two pipelines matched 343 island-years and compared 5,872 values. They agreed exactly on 5,746 values, or 97.9%. All 126 disagreements were checked against the published PDFs. Markdown values took precedence where available; PDF extraction filled structural gaps. Every final row retains a confidence label identifying whether it was cross-checked.

The original one-off PDF-extraction utilities are not retained. Therefore, acquisition from raw Reef Check PDFs is documented and auditable but not fully rerunnable. The analysis from the structured workbook onward is reproducible.

## Preprocessing

`scripts/run_preprocessing.py` performs the reproducible preparation stage:

1. Reads the Reef Check `model_ready` worksheet without replacing missing observations.
2. Normalises island and state labels, including `W.P. Labuan`.
3. Joins the 56-island coordinate reference by island name.
4. Parses NOAA daily text rows and calculates station-year maximum DHW and mean anomaly.
5. Assigns a regional NOAA station using state/ecoregion rules.
6. Retains OpenDOSM files as context without inferring island-level tourism or economic values.
7. Writes `data/processed/master_reef_tourism_dataset.csv`.

The accommodation inventory is read for audit compatibility but its fields are excluded from the production feature list and judged claims.

## Target construction and validation

- Observations are ordered by island and survey year.
- Each row is linked only to the same island's next observed survey.
- The target is the next observation's annualised live-coral-cover change; it is not an interpolated annual observation.
- Model evaluation uses expanding-year validation over target years 2021–2025. Every test year is trained only on earlier target years.
- Missing feature values are median-imputed inside each training fold to prevent leakage.
- Mean prediction is the benchmark. Ridge regression, Gradient Boosting and Random Forest are compared using the same folds.
- Gradient Boosting has the lowest forward-test MAE: 5.859 percentage points/year versus 5.991 for the mean baseline, a 2.2% improvement. R² is 0.070, so the model remains screening-only.
- Prediction bands use pooled empirical 2.5th and 97.5th percentiles of forward-validation residuals rather than a normal-error assumption.

## Factor analysis

Current-observation variables are compared with the next observed coral change. The all-factor table (`data/processed/all_factor_relationships.csv`) applies Spearman rank correlation consistently to all 22 production features and the two NOAA context variables so they can be viewed on one scale. `island_vs_region_pct` is live coral cover minus Reef Check's published eco-region average for that survey year, in percentage points; it is a relative baseline-condition feature, not an external pressure. The focused diagnostic table additionally presents narrative flags as differences in mean next change between mentioned and not-mentioned groups. These are descriptive, unadjusted lagged associations, not causal effects. Repeated islands, irregular survey intervals, multiple comparisons, regional heat proxies, mean reversion and reporting intensity limit interpretation.

## Economic valuation method

The seven DMPM components are loaded from the page-referenced transcription. Their unrounded sum is RM8.68699 billion and the publication reports the rounded headline as RM8.7 billion annually for six evaluated archipelagos from studies conducted during 2011–2015. ReefSafe preserves that scope and does not update the value to current prices or assign it to individual islands.

## Reproducible commands

```powershell
python -m scripts.run_preprocessing
python -m scripts.train_models
python scripts/build_master_notebook.py
python -m jupyter nbconvert --to notebook --execute notebooks/01_reproducible_pipeline.ipynb --output 01_reproducible_pipeline.ipynb --output-dir notebooks --ExecutePreprocessor.timeout=600
python -m unittest discover -s tests -v
```

## Evidence boundaries

- NOAA and OpenDOSM are context, not production-model predictors.
- Visitor rows after 2009 and the accommodation inventory are excluded because their source trail is incomplete.
- Association does not establish tourism causality.
- Priority tiers schedule field verification; they do not prescribe quotas or closures.
- The economic benchmark is historical source context, not ReefSafe revenue or intervention benefit.
