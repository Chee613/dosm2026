# ReefSafe graph guide

The folder contains ten unique, canonical figures. Four unnumbered files elsewhere in the repository are byte-identical copies of figures 07–10 and are intentionally omitted. Figures 05 and 06 remain retired because the earlier versions depended on unsupported policy simulations or claims; number 11 is now used for an evidence-supported all-factor association view.

## `01_tourism_data_gap.png` — verified visitor context and evidence gap

- **Measures:** Recorded domestic and foreign marine-park visitors in the cited 2000–2017 source.
- **Finding:** Historical aggregate visitor counts exist, but there is no verified recent island-level exposure series suitable for joining to reef observations.
- **Interpretation:** This graph establishes a data limitation, not a relationship between tourism and reef condition.
- **Cannot support:** Island visitor estimates, carrying-capacity quotas or tourism-causality claims.
- **Objective:** Compare Available Stressor Evidence.

## `02_national_coral_cover_trajectory.png` — survey-aware coral-cover trend

- **Measures:** Unweighted mean live coral cover among units surveyed each year, with annual sample sizes. It also reports the paired 2024–2025 comparison.
- **Finding:** The 39 units observed in both 2024 and 2025 declined by 4.76 percentage points on average. The 2025 surveyed-unit mean is 39.8%.
- **Interpretation:** The paired comparison is more comparable than treating the full annual means as a fixed national panel.
- **Cannot support:** A census-quality national trend, because the surveyed islands and sites change by year and 2012 has only two units.
- **Objective:** Identify Associated Factors and Prioritise Field Verification.

## `03_satellite_thermal_stress_dhw.png` — regional NOAA heat context

- **Measures:** Mean regional maximum Degree Heating Weeks associated with survey years; the dashed line marks DHW 4.
- **Finding:** Regional heat context exceeded DHW 4 in several years and was highest in 2024.
- **Interpretation:** Heat exposure is a plausible field-verification question when coral losses are observed.
- **Cannot support:** Exact island-level in-water temperature, causal attribution or a production-model feature while DOSM eligibility is unconfirmed.
- **Objective:** Compare Available Stressor Evidence.

## `04_economic_valuation_pillars.png` — published DMPM value components

- **Measures:** Seven annual Total Economic Value components reported by DMPM for six evaluated archipelagos in studies conducted during 2011–2015.
- **Finding:** Aesthetic value dominates the published RM8.7 billion rounded total, followed by fisheries; the other components are substantially smaller.
- **Interpretation:** Reef conservation has documented economic value beyond tourism receipts alone.
- **Cannot support:** Current prices, national reef value, individual-island revenue, avoided losses or NPV.
- **Objective:** Frame Conservation with Economic Context.

## `07_actual_vs_predicted_oof.png` — forward predictions versus observations

- **Measures:** Gradient Boosting predictions against observations from past-only forward validation. The diagonal is perfect prediction.
- **Finding:** Predictions cluster near the centre and compress large positive and negative changes, showing limited ability to predict extremes.
- **Interpretation:** The model provides a weak screening signal suitable for ordering field checks.
- **Cannot support:** Precise forecasts, automated regulation or causal explanations.
- **Objective:** Prioritise Field Verification.

## `08_feature_importance.png` — held-forward permutation importance

- **Measures:** Increase in validation MAE when each production feature is permuted.
- **Finding:** Island-versus-region coral cover and the current coral-change rate provide the strongest predictive signal in the held-forward sample.
- **Interpretation:** These features help prediction under the current validation design.
- **Cannot support:** Causal importance. Longitude may encode geography, survey practice or unmeasured regional differences.
- **Objective:** Identify Associated Factors.

## `09_model_performance.png` — model comparison

- **Measures:** Forward-test MAE for the mean baseline, Ridge regression, Gradient Boosting and Random Forest using identical expanding-year folds.
- **Finding:** Gradient Boosting has the lowest MAE at 5.862 percentage points/year versus 5.991 for the baseline, only a 2.1% improvement.
- **Interpretation:** The model marginally improves ranking information, but evidence quality is the main limitation.
- **Cannot support:** A claim of high predictive accuracy or the assumption that a more complex algorithm such as XGBoost would solve the data limitations.
- **Objective:** Prioritise Field Verification.

## `10_factor_relationships.png` — descriptive lagged associations

- **Measures:** NOAA DHW versus next coral change, distributions by heat band, and mean differences for narrative anchor, trash and bleaching mentions.
- **Finding:** Maximum DHW has a weak negative Spearman association with next change (rho = -0.105, n = 348, p = 0.051). The DHW ≥ 4 group has a more negative mean next change, but observations remain widely dispersed.
- **Interpretation:** Heat and reported local impacts are useful hypotheses for field verification.
- **Cannot support:** Tourism causality, independent-observation assumptions or effect-size claims from narrative mentions.
- **Objective:** Identify Associated Factors and Compare Available Stressor Evidence.

## `11_all_factor_associations.png` — all measured factors on one scale

- **Measures:** Spearman correlation between each of the 22 production features, plus two NOAA context variables, and the next observed annualised coral-cover change. Negative values align with a more negative next change. The chart shows sample size and unadjusted p-value for every factor.
- **Finding:** The strongest negative associations are coral cover versus the regional average (rho = -0.320), current live coral cover (rho = -0.295) and the current coral-change rate (rho = -0.218). The first is calculated as island coral cover minus Reef Check's published eco-region average for that survey year, in percentage points. Most other relationships are weak or very weak. NOAA maximum DHW is weak (rho = -0.105, p = 0.051).
- **Interpretation:** The measured data contain limited single-factor signal. The leading variables describe existing coral condition and relative position, so mean reversion and survey structure are plausible explanations alongside ecological processes.
- **Cannot support:** A causal ranking, an estimate of each factor's contribution, or the claim that all factors are weak. One relationship reaches the chart's moderate band, and multiple testing means isolated p-values should be treated cautiously.
- **Objective:** Identify Associated Factors and Compare Available Stressor Evidence.

## `12_dataset_completeness_matrix.png` — production-feature availability

- **Measures:** Percentage of training transitions with each verified production feature available before fold-local imputation.
- **Finding:** Most features exceed 97% availability; current change rate is lowest at 86.1% and grazer ratio is 94.3%.
- **Interpretation:** The production table has broad feature coverage, and remaining missing values are handled inside each training fold.
- **Cannot support:** Measurement accuracy, source comparability or absence of missing-not-at-random bias.
- **Objective:** Identify Associated Factors and Prioritise Field Verification.
