# ReefSafe submission evidence package

This package is the judge-facing evidence bundle for ReefSafe. Start with the notebook for the reproducible story, the report for the concise submission narrative, and the dashboard workbook for exploration. `Methodology.md` documents acquisition and processing for every dataset; `All_Assumptions.md` records the project's limits; `images/README.md` explains what every graph shows and what it cannot prove.

## What changed

| Area | Change | Why it improves the submission |
|---|---|---|
| Objectives | Reframed unsupported causal, quota and financial promises as evidence-bounded screening objectives. | Every objective is now answerable with the available data. |
| Target and validation | Predicts the next observed annualised coral-cover change with past-only expanding-year validation. | Prevents future information leaking into earlier tests. |
| Stressor evidence | Keeps NOAA as regional context and explicitly exposes the tourism data gap. | Avoids presenting proxy data as island-level causes. |
| Associations | Adds one common-scale chart for all 22 production features and two NOAA context variables. | Judges can see immediately that most single-factor relationships are weak or very weak. |
| Model claims | Compares every model with a mean baseline and uses empirical forward residual ranges. | Makes the modest predictive value and uncertainty visible. |
| Economics | Replaces invented revenue/NPV scenarios with DMPM's sourced RM8.7 billion historical TEV benchmark. | Preserves policy relevance without fabricating island-level values. |
| Governance | Corrects W.P. Labuan handling and discloses incomplete coordinate and accommodation provenance. | Makes acquisition and eligibility risks auditable. |

## The four objectives remain

1. **Identify Associated Factors:** examine lagged relationships between measured reef condition, ecology, reported impacts and next observed coral-cover change.
2. **Compare Available Stressor Evidence:** compare regional heat and recorded local-pressure signals while stating that tourism's share cannot be estimated from current data.
3. **Prioritise Field Verification:** use a modest predictive signal, observed condition and uncertainty to order ranger follow-up—not to automate closures or quotas.
4. **Frame Conservation with Economic Context:** cite the published DMPM RM8.7 billion annual benchmark for six evaluated archipelagos during 2011–2015 without treating it as current ReefSafe revenue.

## Findings and insights

- The same 39 monitoring units surveyed in 2024 and 2025 declined by 4.76 percentage points on average.
- The strongest negative all-factor association is coral cover versus the regional average (rho = -0.320, n = 346, p < 0.001), followed by current coral cover (rho = -0.295) and current change rate (rho = -0.218). The first equals island coral cover minus Reef Check's published eco-region average for that survey year. These are condition signals, not identified causes, and may partly reflect mean reversion.
- Most measured factors have weak or very weak individual associations. NOAA maximum DHW is weakly negative (rho = -0.105, n = 348, p = 0.051) and remains context only.
- Gradient Boosting has forward-test MAE 5.859 percentage points/year versus 5.991 for the mean baseline: a 2.2% improvement, with R² 0.070. This supports prioritisation only, not precise forecasting.
- The verified visitor source covers 2000–2009 aggregates. No recent island-level visitor exposure series is available, so tourism causality is not estimable.
- DMPM reports a rounded RM8.7 billion annual Total Economic Value for six evaluated marine-park archipelagos in studies conducted during 2011–2015. This is historical context, not a ReefSafe calculation.

## Recommended actions

| Evidence observed | Appropriate action now |
|---|---|
| High screening priority | Schedule field verification and review the prediction range before any intervention. |
| Elevated regional heat | Coordinate an in-water bleaching survey; do not attribute the loss to visitors. |
| Recorded anchor impact | Inspect mooring availability and anchoring controls. |
| Waste or pollution indicator | Audit waste and wastewater controls at the monitoring unit. |
| No dominant measured stressor | Collect local temperature, vessel, visitor and wastewater data before choosing a policy response. |
| Coordinate or external-data eligibility gap | Independently verify the source and obtain written DOSM confirmation before regulatory use. |

## Which graph answers the factor question?

Use `images/11_all_factor_associations.png` as the main graph showing every measured factor against subsequent coral-cover change. Use `images/10_factor_relationships.png` for a closer view of heat bands and selected recorded impacts, and `images/08_feature_importance.png` only for predictive contribution inside the validated model. Correlation and predictive importance answer different questions; neither proves causality.

## Decision boundary

ReefSafe is a field-verification queue. It does not prove why coral changed, calculate legal carrying capacity, estimate island revenue, or guarantee that an intervention will work.
