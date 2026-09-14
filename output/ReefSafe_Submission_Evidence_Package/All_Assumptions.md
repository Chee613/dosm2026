# ReefSafe assumption register

These assumptions define what the evidence can support. ReefSafe is a screening tool, not a causal, carrying-capacity or financial model.

| Area | Working assumption | Risk | Mitigation |
|---|---|---|---|
| Monitoring unit | The same island label is comparable across survey years. | Site composition or methods may change. | Retain year and source confidence; verify large movements against the source reports. |
| Change rate | Change between observations can be annualised for comparison. | Events between surveys are unobserved. | Store both observation years and never label interpolated years as observations. |
| Temporal transfer | Earlier patterns contain limited information about later observations. | Regime shifts can weaken transfer. | Use past-only expanding-year validation and compare against a mean baseline. |
| Regional heat | NOAA virtual stations describe broad regional thermal context. | Local reef conditions can differ. | Keep NOAA out of the scored model until DOSM confirms eligibility; request in-water logger verification. |
| Narrative flags | An anchor, trash or bleaching mention indicates a recorded observation. | No mention does not prove absence and reporting intensity varies. | Present descriptive group differences only. |
| Missing values | Fold-local median imputation is acceptable for model comparison. | Missingness may be systematic. | Fit imputation within each training fold and retain missing values in processed data. |
| Repeated observations | Island observations are not fully independent. | Ordinary uncertainty estimates can be too narrow. | Use empirical forward-validation residual bands and label them screening uncertainty. |
| Coordinate mapping | The local island coordinate table is sufficiently accurate for broad geographic grouping. | Its original retrieval script and verifiable external source URL are not retained. | Independently verify coordinates before regulatory use and do not treat longitude/latitude importance as causal. |
| Priority tier | The top quartile is a field-work queue. | Rank boundaries can be mistaken for ecological thresholds. | Require ranger verification and do not prescribe closures or quotas. |
| Tourism data gap | The cited visitor source verifies 2000–2009 aggregates only; no verified island-level exposure series is available. | Allocating totals to islands would fabricate precision. | Keep visitor and OpenDOSM context outside the model. |
| Economic valuation | DMPM's RM8.7 billion is a rounded annual Total Economic Value for six evaluated archipelagos during 2011–2015. | Treating it as current ReefSafe revenue, avoided loss or a national reef total would be incorrect. | Show the published components and scope only; do not calculate NPV or island allocations. |

## Assumptions explicitly rejected

- State tourism totals represent visitor pressure at individual reefs.
- Missing narrative mentions mean an impact was absent.
- Regional NOAA stations measure exact in-water temperature at each island.
- A model prediction proves why coral cover changed.
- The priority threshold is an ecological carrying-capacity threshold.
- The DMPM valuation is current island revenue or a guaranteed conservation benefit.

## What new data would change

Island-level visitor counts, vessel trips, mooring use, wastewater discharge, closure records, stable survey-site identifiers and in-water temperature would allow these assumptions to be tested. Until then, ReefSafe prioritises field verification rather than prescribing regulation.

