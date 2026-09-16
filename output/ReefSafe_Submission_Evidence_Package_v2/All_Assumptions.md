# ReefSafe Operational Assumptions & Governance Register (Package v2)

This register defines the empirical and methodological boundaries of ReefSafe. ReefSafe is an evidence-bounded predictive screening system designed for ranger verification and conservation resource scheduling, not a causal carrying-capacity or financial model.

---

## 1. Working Assumptions & Guardrails

| Domain | Working Assumption | Potential Risk | Operational Mitigation / Guardrail |
|---|---|---|---|
| **Monitoring Unit Continuity** | Island labels are comparable across survey years. | Site composition and survey teams change over time. | Model on site-year pairs (`site_id`); retain annual survey sample sizes; report paired comparisons. |
| **Change Rate Annualisation** | Change rates between successive surveys can be annualised ($pp/\text{year}$). | Intermediate acute events between survey years remain unobserved. | Store both survey years explicitly; never interpolate missing intermediate years as synthetic observations. |
| **Past-Only Temporal Transfer** | Past relationships provide actionable signals for future seasons. | Unprecedented marine heatwaves can alter historical response functions. | Strictly evaluate models on future years ($t_{train} < t_{test}$); report empirical forward residual intervals. |
| **Macro-Thermal Context** | NOAA CRW 5 km virtual stations provide regional atmospheric-oceanic heat exposure. | In-water temperatures vary by depth, shading, and local currents. | Keep NOAA outside the production feature set; use as descriptive screening context; recommend in-water loggers. |
| **Narrative Impact Mentions** | A reported mention (anchor, trash, bleaching) reflects an observed physical impact. | Absence of mention does not prove absence of damage (reporting bias). | Treat binary mentions as descriptive group indicators; do not extrapolate to continuous impact densities. |
| **Missing Value Imputation** | Fold-local median imputation prevents data leakage during training. | Missingness could be non-random. | Impute strictly within training folds; preserve raw nulls in published processed datasets. |
| **Empirical Prediction Bounds** | Empirical 2.5th and 97.5th percentiles of out-of-fold residuals represent uncertainty. | Residual distributions may vary across ecoregions. | Label ranges clearly as empirical screening bounds, not parametric confidence intervals. |
| **Geospatial Mapping** | The 56-island coordinate registry provides accurate regional grouping. | Exact reef transects span up to several kilometers around island perimeters. | Use coordinates for spatial grouping and interactive mapping only; verify exact GPS transects in the field. |
| **Priority Queue Tiering** | Top 25% predicted decline designates High screening priority. | Arbitrary thresholds could be misinterpreted as regulatory cutoff points. | Explicitly define priority as "verify sooner" (schedule ranger visits); strictly forbid automated closures. |
| **Tourism Data Gap** | Official marine-park visitor series covers 2000–2017 state aggregates. | Allocating state visitor totals to individual reefs would fabricate precision. | Exclude visitor numbers from ML training; explicitly present the data gap in evidence visualizations. |
| **Economic Valuation** | DMPM's RM8.7B Total Economic Value is an institutional benchmark (2011–2015 study). | Misrepresenting TEV as current revenue or avoided losses would mislead stakeholders. | Present published components (RM8.0B aesthetic scenery vs RM4.6M tourism income) as conservation context only. |

---

## 2. Explicitly Rejected Assumptions

The following common assumptions are **explicitly rejected** by ReefSafe to prevent misleading decision-making:

1. **Rejected:** "State or island visitor totals represent local diver or boat pressure on specific coral patches."
2. **Rejected:** "The absence of a reported anchor or trash mention proves the reef is free from human disturbance."
3. **Rejected:** "Satellite Degree Heating Weeks measure exact in-water water temperature at depth."
4. **Rejected:** "High machine-learning predictive accuracy ($R^2 = 0.975$) proves causal mechanisms."
5. **Rejected:** "A high screening priority justifies automatic reef closure, tourist caps, or penalty enforcement without field verification."
6. **Rejected:** "The historical DMPM RM8.7 billion TEV benchmark represents direct annual revenue earned by marine parks or monetized savings."

---

## 3. Decision Boundary & Governance Framework

```
[Raw Ecological & Thermal Data]
             │
             ▼
[Gradient Boosting Predictive Engine (R² = 0.975, MAE = 0.38 pp/yr)]
             │
             ▼
[Tree-Path Stress Attribution & Evidence Matching]
             │
             ▼
[Field-Verification Priority Matrix (Graph 12)]
             │
             ▼
[High Screening Priority Queue (Top 25%)]
             │
             ▼
[MANDATORY GOVERNANCE GATEWAY: Ranger Physical Inspection & In-Water Verification]
   ┌─────────┴─────────┐
   ▼                   ▼
[Evidence Confirmed]  [Evidence Not Confirmed]
   │                   │
   ▼                   ▼
[Deploy Targeted      [Update Evidence Register &
 Management Action]    Recalibrate Screening Signals]
```

ReefSafe functions strictly as an **operational field-triage radar**: it tells marine park authorities **where to look first and what evidence to look for**, ensuring that management actions are guided by in-water evidence rather than speculative models.
