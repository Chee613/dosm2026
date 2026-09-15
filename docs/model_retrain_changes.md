# Model retrain: what changed

Branch `onn-v2`, 15 Sep 2026. **Old** = the teammate's committed outputs (commit `6401c97`). **New** = the retrain on this machine.

## Why and what

- **Why:** the stress factor breakdown on the Monitoring Unit tab is traced from the fitted model's trees. The pipeline does not save the fitted model, so it was retrained, and the predictions and breakdowns were written from the same run.
- **Same model:** code, data, 22 features, settings (Gradient Boosting, 100 trees, depth 2, learning rate 0.04) and seed (`random_state=42`) are unchanged. Re-running gives byte-identical outputs on this machine.
- **What differs:** 2 of 40 final predictions (Bidong & Yu, Mabul) and 2 of 183 validation predictions (Tioman 2022, Rawa 2022). Everything else matches to within 1e-14.
- **Likely cause:** a near-tied tree split resolved differently under different library versions (this machine: scikit-learn 1.7.2, numpy 2.3.5; the teammate's versions are unknown). Not confirmed.

## 1. Numbers to update in the report

| Item | Old | New | Note |
|---|---|---|---|
| Gradient boosting MAE (3 dp) | 5.859 | **5.862** | At 2 dp it stays 5.86 |
| Gradient boosting RMSE (3 dp) | 7.739 | **7.741** | At 2 dp it stays 7.74 |
| Gradient boosting R² | 0.070 | **0.069** | |
| MAE improvement over baseline | 2.2% (2.20%) | **2.1%** (2.15%) | Baseline MAE unchanged at 5.991 |
| Random forest RMSE | 8.017 | **8.016** | MAE 6.074 and R² 0.002 unchanged at 3 dp |
| 2022 validation MAE | 6.94 | **6.96** | |
| 2022 validation bias | −0.03 | **−0.04** | RMSE 9.96 and R² 0.12 unchanged at 2 dp |
| Units predicted to decline | 36 of 40 (90%) | **38 of 40 (95%)** | |
| Units predicted to gain | 4 | **2** | Now Kapalai and Malacca only |
| Urgency High / Medium / Low | 10 / 26 / 4 | **10 / 28 / 2** | Medium = Monitor with predicted decline; Low = Monitor with predicted gain (dashboard map colours) |
| Mean predicted change, 40 units | −2.69 pp/yr | **−2.75 pp/yr** | Median unchanged at −2.54 |
| Bidong & Yu: predicted change | +0.59 pp/yr | **−0.61 pp/yr** | Rank 37 → 36; range −16.9 to +13.0 (was −15.7 to +14.3) |
| Mabul: predicted change | +1.18 pp/yr | **−0.03 pp/yr** | Rank 39 → 38; range −16.3 to +13.6 (was −15.1 to +14.8) |
| Mantanani: rank | 36 | **37** | Prediction unchanged (−0.15 pp/yr) |
| Kapalai: rank | 38 | **39** | Prediction unchanged (+0.77 pp/yr) |

## 2. Unchanged (keep as is)

- Baseline mean MAE 5.991. Ridge regression: MAE 5.990, RMSE 7.939, R² 0.021.
- Training transitions 348; forward evaluation observations 183; test years 2021–2025.
- Uncertainty range (pooled 95% forward residuals): −16.25 to +13.66 pp/yr.
- Top 10: same islands, same order, same predictions (Labuan, Kapas, Seri Buat, Mertang, Mensirip, Tenggol, Tinggi, Lima, Sibu, Lankayan).
- High screening priority: 10 units; cutoff at rank 10 (Lankayan) −4.07 pp/yr. No unit changed tier.
- Validation results for 2021, 2023, 2024 and 2025.
- Not model outputs, so unchanged: factor diagnostics (Spearman correlations and p-values), descriptive statistics (coral cover, paired 2024–2025 change, heat summaries), and all tourism and economics figures.

## 3. Model comparison (forward test)

| Model | MAE old | MAE new | RMSE old | RMSE new | R² old | R² new |
|---|---|---|---|---|---|---|
| Baseline mean | 5.9910 | 5.9910 | 8.1001 | 8.1001 | −0.0191 | −0.0191 |
| Ridge regression | 5.9899 | 5.9899 | 7.9390 | 7.9390 | 0.0210 | 0.0210 |
| Gradient boosting | 5.8594 | 5.8623 | 7.7388 | 7.7407 | 0.0698 | 0.0693 |
| Random forest | 6.0736 | 6.0736 | 8.0166 | 8.0160 | 0.0018 | 0.0019 |

## 4. Validation by target year (Gradient boosting)

| Target year | n | MAE old | MAE new | RMSE old | RMSE new | R² old | R² new | Bias old | Bias new |
|---|---|---|---|---|---|---|---|---|---|
| 2021 | 24 | 5.700 | 5.700 | 7.580 | 7.580 | 0.107 | 0.107 | −2.403 | −2.403 |
| **2022** | 35 | 6.944 | **6.959** | 9.955 | 9.962 | 0.117 | 0.115 | −0.026 | **−0.036** |
| 2023 | 43 | 5.756 | 5.756 | 7.239 | 7.239 | 0.178 | 0.178 | +0.875 | +0.875 |
| 2024 | 41 | 5.601 | 5.601 | 7.061 | 7.061 | −0.286 | −0.286 | +2.261 | +2.261 |
| 2025 | 40 | 5.383 | 5.383 | 6.735 | 6.735 | −0.654 | −0.654 | +4.452 | +4.452 |

## 5. Forward-test predictions that changed

| Island | Survey → target year | Actual (pp/yr) | Old prediction | New prediction |
|---|---|---|---|---|
| Tioman | 2021 → 2022 | +2.78 | −1.762 | −2.200 |
| Rawa | 2019 → 2022 | −4.09 | +1.876 | +1.960 |

2 of 183 forward-test predictions changed; the rest are identical. These two rows are why the 2022 year and the overall MAE, RMSE and R² moved.

## 6. Full priority ranking (40 units)

Changed ranks and predictions in bold. Predicted change and range in pp/yr.

| New rank | Island | State | Old rank | Old predicted | New predicted | New range | Tier | Urgency |
|---|---|---|---|---|---|---|---|---|
| 1 | Labuan | W.P. Labuan | 1 | −14.42 | −14.42 | −30.7 to −0.8 | High Priority | High |
| 2 | Kapas | Terengganu | 2 | −5.75 | −5.75 | −22.0 to +7.9 | High Priority | High |
| 3 | Seri Buat | Pahang | 3 | −5.15 | −5.15 | −21.4 to +8.5 | High Priority | High |
| 4 | Mertang | Johor | 4 | −5.03 | −5.03 | −21.3 to +8.6 | High Priority | High |
| 5 | Mensirip | Johor | 5 | −4.85 | −4.85 | −21.1 to +8.8 | High Priority | High |
| 6 | Tenggol | Terengganu | 6 | −4.64 | −4.64 | −20.9 to +9.0 | High Priority | High |
| 7 | Tinggi | Johor | 7 | −4.63 | −4.63 | −20.9 to +9.0 | High Priority | High |
| 8 | Lima | Johor | 8 | −4.37 | −4.37 | −20.6 to +9.3 | High Priority | High |
| 9 | Sibu | Johor | 9 | −4.34 | −4.34 | −20.6 to +9.3 | High Priority | High |
| 10 | Lankayan | Sabah | 10 | −4.07 | −4.07 | −20.3 to +9.6 | High Priority | High |
| 11 | Sipadan | Sabah | 11 | −4.06 | −4.06 | −20.3 to +9.6 | Monitor | Medium |
| 12 | Tun Sakaran Marine Park | Sabah | 12 | −3.97 | −3.97 | −20.2 to +9.7 | Monitor | Medium |
| 13 | Larapan | Sabah | 13 | −3.44 | −3.44 | −19.7 to +10.2 | Monitor | Medium |
| 14 | Harimau | Johor | 14 | −3.15 | −3.15 | −19.4 to +10.5 | Monitor | Medium |
| 15 | Tengah | Johor | 15 | −3.03 | −3.03 | −19.3 to +10.6 | Monitor | Medium |
| 16 | Rawa | Johor | 16 | −2.91 | −2.91 | −19.2 to +10.8 | Monitor | Medium |
| 17 | Gual | Johor | 17 | −2.84 | −2.84 | −19.1 to +10.8 | Monitor | Medium |
| 18 | Penyu | Sabah | 18 | −2.76 | −2.76 | −19.0 to +10.9 | Monitor | Medium |
| 19 | Payar | Kedah | 19 | −2.75 | −2.75 | −19.0 to +10.9 | Monitor | Medium |
| 20 | Lahad Datu | Sabah | 20 | −2.68 | −2.68 | −18.9 to +11.0 | Monitor | Medium |
| 21 | Tun Mustapha Park | Sabah | 21 | −2.40 | −2.40 | −18.7 to +11.3 | Monitor | Medium |
| 22 | Hujung | Johor | 22 | −2.31 | −2.31 | −18.6 to +11.4 | Monitor | Medium |
| 23 | Pemanggil | Johor | 23 | −2.27 | −2.27 | −18.5 to +11.4 | Monitor | Medium |
| 24 | Besar | Johor | 24 | −2.21 | −2.21 | −18.5 to +11.5 | Monitor | Medium |
| 25 | Usukan Cove | Sabah | 25 | −2.18 | −2.18 | −18.4 to +11.5 | Monitor | Medium |
| 26 | Port Dickson | Negeri Sembilan | 26 | −2.03 | −2.03 | −18.3 to +11.6 | Monitor | Medium |
| 27 | Aur & Dayang | Johor | 27 | −1.92 | −1.92 | −18.2 to +11.7 | Monitor | Medium |
| 28 | Tioman | Pahang | 28 | −1.63 | −1.63 | −17.9 to +12.0 | Monitor | Medium |
| 29 | Tiga | Sabah | 29 | −1.57 | −1.57 | −17.8 to +12.1 | Monitor | Medium |
| 30 | Rhu | Terengganu | 30 | −1.19 | −1.19 | −17.4 to +12.5 | Monitor | Medium |
| 31 | Redang | Terengganu | 31 | −1.11 | −1.11 | −17.4 to +12.6 | Monitor | Medium |
| 32 | Perhentian | Terengganu | 32 | −1.08 | −1.08 | −17.3 to +12.6 | Monitor | Medium |
| 33 | Tunku Abdul Rahman Park | Sabah | 33 | −1.06 | −1.06 | −17.3 to +12.6 | Monitor | Medium |
| 34 | Mataking | Sabah | 34 | −1.03 | −1.03 | −17.3 to +12.6 | Monitor | Medium |
| 35 | Lang Tengah | Terengganu | 35 | −0.78 | −0.78 | −17.0 to +12.9 | Monitor | Medium |
| **36** | **Bidong & Yu** | Terengganu | 37 | +0.59 | **−0.61** | −16.9 to +13.0 | Monitor | Medium |
| **37** | **Mantanani** | Sabah | 36 | −0.15 | −0.15 | −16.4 to +13.5 | Monitor | Medium |
| **38** | **Mabul** | Sabah | 39 | +1.18 | **−0.03** | −16.3 to +13.6 | Monitor | Medium |
| **39** | **Kapalai** | Sabah | 38 | +0.77 | +0.77 | −15.5 to +14.4 | Monitor | Low |
| 40 | Malacca | Malacca | 40 | +3.48 | +3.48 | −12.8 to +17.1 | Monitor | Low |

## 7. Permutation importance (feature importance figure)

Mean MAE increase when a feature is shuffled (8 repeats). Higher means more important; negative means no useful signal.

| New rank | Feature | Old | New | Old rank |
|---|---|---|---|---|
| 1 | `island_vs_region_pct` | 0.2784 | 0.2823 | 1 |
| 2 | `lcc_change_rate` | 0.1416 | 0.1410 | 2 |
| 3 | `longitude` | 0.0596 | 0.0601 | 3 |
| 4 | `fish_parrotfish` | 0.0564 | 0.0564 | 4 |
| 5 | `fish_snapper` | 0.0309 | 0.0313 | 5 |
| 6 | `grp_sand` | 0.0268 | 0.0250 | 6 |
| 7 | `fish_grouper` | 0.0227 | 0.0227 | 7 |
| 8 | `impact_bleaching` | 0.0005 | 0.0005 | 8 |
| 9 | `impact_anchor` | 0.0000 | 0.0000 | 9 |
| 10 | `fish_butterflyfish` | −0.0006 | −0.0006 | 10 |
| 11 | `survey_year` | −0.0007 | −0.0007 | 11 |
| 12 | `impact_nets` | −0.0023 | −0.0023 | 12 |
| **13** | `impact_cot` | −0.0042 | −0.0039 | 14 |
| **14** | `inv_crown_of_thorns` | −0.0027 | −0.0056 | 13 |
| 15 | `grp_pollution_indicators` | −0.0053 | −0.0061 | 15 |
| **16** | `grp_disturbance_indicators` | −0.0065 | −0.0065 | 17 |
| **17** | `impact_trash` | −0.0071 | −0.0071 | 18 |
| **18** | `inv_diadema_urchin` | −0.0095 | −0.0072 | 19 |
| **19** | `grazer_ratio` | −0.0063 | −0.0093 | 16 |
| 20 | `latitude` | −0.0102 | −0.0102 | 20 |
| 21 | `live_coral_cover_pct` | −0.0203 | −0.0215 | 21 |
| 22 | `grp_available_substrate` | −0.0745 | −0.0745 | 22 |

The top 12 features keep their order. 6 lower-ranked features swap places (bold); all 6 have negative importance (no useful signal) before and after.

## 8. Figures to replace

Redrawn from the new outputs. The same image is saved in several folders:

| Figure | Files |
|---|---|
| Model comparison (MAE by model) | `reports/figures/09_model_performance.png`, `output/fig1_model_performance_cv.png`, `figures/model_performance.png`, `dashboard/figures/model_performance.png` |
| Actual vs predicted (forward test) | `reports/figures/07_actual_vs_predicted_oof.png`, `output/fig2_actual_vs_predicted.png`, `figures/actual_vs_predicted_oof.png`, `dashboard/figures/actual_vs_predicted_oof.png` |
| Feature importance | `reports/figures/08_feature_importance.png`, `output/fig3_feature_importance.png`, `figures/feature_importance.png`, `dashboard/figures/feature_importance.png` |

The visible difference is small: two 2022 points move in the actual-vs-predicted plot, and some bars shift slightly.

## 9. New output from this run (not a change)

`data/processed/stress_contributions.csv` splits each unit's prediction into 8 factor groups by tree path decomposition (Saabas 2014). The model baseline is −0.90 pp/yr for every unit, and baseline + groups = the prediction exactly.

- 15 of 40 units have a named top stressor (a stressor group pushing at least 0.25 pp/yr towards decline); 25 have none.
- Example, Labuan: baseline −0.90 + Pollution & waste −13.64 + other groups +0.12 = prediction −14.42 pp/yr.
- This is model attribution, not proven cause. NOAA heat is not in the model.

## 10. Files regenerated

- `data/processed/`: `reef_priority_predictions.csv`, `model_evaluation_metrics.csv`, `model_validation_by_year.csv`, `model_validation_predictions.csv`, `stress_contributions.csv` (new)
- `output/model_evaluation_metrics.json`, the figures in section 8, `dashboard/data.js`
- Notebook re-executed; Excel workbook cells updated
- Text updated (MAE, RMSE, R², improvement): `README.md`, `dist/dashboard_package/README.txt`, the evidence package `Methodology.md`, `README.md` and `images/README.md`, and `output/VIDEO_PRESENTATION_SCRIPT.md`
