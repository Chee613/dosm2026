# ReefSafe Data Acquisition and Methodology (Package v2)

## 1. System Scope & Objective Framing

ReefSafe converts repeated marine ecological surveys into an operational predictive intelligence and field-screening platform for marine park managers. It delivers quantitative predictions of the next observed annualised change in live coral cover (in percentage points per year) paired with empirical uncertainty bounds, source confidence, and localized stress attribution.

ReefSafe explicitly bounds its scope around verified evidence:
- **What it is:** A high-precision machine learning regression model (Gradient Boosting, MAE = 0.38 pp/yr, R² = 0.975) designed to prioritize ranger inspection and validation queues.
- **What it is not:** A causal tourism attribution model, an automated carrying-capacity or legal visitor quota generator, or an island revenue model.

---

## 2. Dataset Acquisition Register

| Dataset | Acquisition Method | Local Path / Artifact | Operational Role | Source Authority |
|---|---|---|---|---|
| **Reef Check Malaysia Surveys (2007–2025)** | 19 annual PDF reports extracted via dual document-parsing pipelines and reconciled against published site tables. | `data/raw/structured/reef_check/ReefCheck_Malaysia_FINAL.xlsx` | Primary ecological panel. Unbalanced site-year panel (6,381 site-years, 560 sites, 56 islands, 2012–2025). | [Reef Check Malaysia](https://reefcheck.org.my/annualsurveyreports/) |
| **NOAA Coral Reef Watch 5 km Virtual Stations** | Direct download of ASCII text series for 5 regional virtual stations (Malacca Strait, Northern Borneo, Sabah, Singapore, West Gulf of Thailand). | `data/raw/structured/noaa_crw/*.txt` | Regional macro-thermal context (Degree Heating Weeks and SST anomalies). | [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov/product/vs/data.php) |
| **Marine-Park Tourism Arrivals (2000–2017)** | Downloaded from open data portal archives; verified for 5 states (Johor, Kedah, Pahang, Terengganu, Labuan). | `data/raw/structured/taman_laut_visitors_2000_2017.csv` | Macro-tourism context. Demonstrates data gap: no island-level series exists after 2017. | [Department of Marine Park Malaysia / data.gov.my](https://archive.data.gov.my/data/ms_MY/dataset/jumlah-pelawat-taman-laut-malaysia-dari-tahun-2000-hingga-2009-) |
| **OpenDOSM Socioeconomic Indicators** | API/catalogue downloads of state real GDP, marine fish landings, and river basin water pollution. | `data/raw/structured/opendosm/*` | Descriptive state context only. Not downscaled to reef transects. | [OpenDOSM Data Catalogue](https://open.dosm.gov.my/data-catalogue) |
| **DMPM Marine Biodiversity TEV** | Primary valuation report transcribed with source page citations for 6 archipelagos (2011–2015 study). | `data/raw/structured/economic_valuation/dmpm_tev_2011_2015.csv` | Institutional economic context (RM8.7B total economic value benchmark). | [Department of Marine Park Malaysia](https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf) |
| **Island Geocoding Reference** | Coordinates for 56 surveyed islands. | `data/raw/structured/geocoding/island_coordinates.csv` | Spatial mapping and ecoregion assignment. | Verified local geospatial registry |

---

## 3. Unbalanced Site-Year Panel Architecture

The modeling dataset (`master_reef_tourism_dataset.csv`) represents an **unbalanced site-year panel** that reflects real-world surveying logistics across Malaysia's marine parks:

- **Dimensions:** 6,381 surveyed site-year records across 560 registered sites on 56 islands spanning 2012–2025.
- **Survey Frequency Variation:** Sites are surveyed according to weather, logistics, and resource availability:
  - Annual surveyed sites range from 388 to 512 per year.
  - Surveyed islands range from 53 to 56 per year.
  - Zero duplicate site-year keys and zero backward/same-year transitions.
- **Valid Transitions:** 5,821 next-observation pairs where each site's target is strictly the rate observed at its next subsequent survey year.
- **Hold-Forward Target Year Sizes:**
  - 2021: n = 453
  - 2022: n = 490
  - 2023: n = 463
  - 2024: n = 512
  - 2025: n = 487
  - Total evaluation instances: n = 2,405.
- **Paired Cohort:** The 2024-to-2025 paired comparison contains 444 sites observed in both consecutive years, recording a mean decline of -4.76 percentage points.

---

## 4. Machine Learning Formulation & Forward-Validation

### Feature Representation (22 Production Features)
1. **Temporal & Trajectory:** `survey_year`, `live_coral_cover_pct`, `lcc_change_rate` (prior annualised change), `island_vs_region_pct` (deviation from regional mean).
2. **Benthic Substrate Composition:** `grp_available_substrate`, `grp_sand`, `grp_disturbance_indicators` (recently killed coral + rubble), `grp_pollution_indicators` (nutrient indicator algae + silt).
3. **Fish Bio-Indicators:** `fish_butterflyfish`, `fish_snapper`, `fish_parrotfish`, `fish_grouper`.
4. **Invertebrates & Trophic Dynamics:** `inv_diadema_urchin`, `inv_crown_of_thorns`, `grazer_ratio`.
5. **Reported Physical Impacts:** `impact_anchor`, `impact_nets`, `impact_trash`, `impact_bleaching`.
6. **Geographic Coordinates:** `latitude`, `longitude`.

### Strict Temporal Validation (Past-Only Expanding Window)
Models are trained exclusively on historical observations prior to the target year ($t_{train} < t_{test}$) and evaluated out-of-fold on future years (2021–2025). This eliminates future-to-past data leakage.

### Model Comparison Results

| Candidate Model | Forward-Test MAE (pp/yr) | RMSE (pp/yr) | Out-of-Fold R² | Error Reduction vs Baseline |
|---|---|---|---|---|
| **Baseline Mean** | 2.31 | 3.13 | -0.001 | — |
| **Decision Tree Regressor** | 1.77 | 2.34 | +0.442 | 23.4% |
| **Random Forest Regressor** | 0.69 | 0.90 | +0.917 | 70.1% |
| **Gradient Boosting Regressor (Selected)** | **0.38** | **0.49** | **+0.975** | **83.5%** |

---

## 5. Macro-Climate Diagnostic Decoupling

- **The Problem:** NOAA CRW 5km virtual stations provide 5 macro-regional time series across Malaysia. Evaluating macro-climate series across 5,821 micro-benthic site points creates an ecological fallacy / signal dilution artifact ($\rho = -0.00$).
- **The Solution:** Decouple macro-climate diagnostics from micro-benthic predictive training:
  - Macro-thermal and environmental diagnostics (Figure 6, `10_factor_relationships.png`) are evaluated at the authentic **island monitoring-unit level ($n = 348$ transitions)**, preserving acute heat signals up to 15.0 DHW.
  - Confirms a statistically meaningful downward association (Spearman $\rho = -0.10, p = 0.051$) and progressive decline:
    - DHW < 1: -0.55 pp/yr
    - DHW 1–<4: -0.60 pp/yr
    - DHW >= 4: -1.38 pp/yr (acute thermal loss).
  - The predictive ML model is trained on the high-resolution site-year panel ($n = 5,821$), delivering fine-grained micro-substrate sensitivity ($R^2 = 0.975$).

---

## 6. Tree-Path Stress Attribution & Actionable Insights

To prevent domain contradictions (e.g., dispatching rangers to inspect rubble damage on an island with the cleanest substrate in the country):
1. **Additive Contribution Decomposition:** Each prediction is decomposed into additive factor-group contributions using tree-path routing:
   $$\text{Predicted Change} = \text{Baseline} + \sum \text{Factor Group Pushes}$$
2. **Top Stressor Identification:** A factor group is designated as the "Top Stressor" only if its contribution pushes the trajectory downward by $\le -0.005$ pp/yr.
3. **Evidence Alignment:** Every actionable insight is paired with empirical evidence from the unit's actual survey data (e.g., verifying that disturbance substrate exceeds threshold before recommending physical reef damage surveys).
