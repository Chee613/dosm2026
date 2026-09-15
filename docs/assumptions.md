# ReefSafe assumption register

These assumptions define what the evidence can support. ReefSafe is a screening tool, not a causal, carrying-capacity, or financial model.

| Area | Working assumption | Risk | Mitigation |
|---|---|---|---|
| Monitoring unit | The same island label is comparable across survey years. | Site composition or methods may change. | Retain year and source confidence; verify large movements against the source reports. |
| Change rate | Change between observations can be annualised for comparison. | Events between surveys are unobserved. | Store both observation years and never label interpolated years as observations. |
| Temporal transfer | Earlier patterns contain limited information about later observations. | Regime shifts can weaken transfer. | Use past-only expanding-year validation and compare against a mean baseline. |
| Regional heat | NOAA virtual stations describe broad regional thermal context. | Local reef conditions can differ. | Keep NOAA out of the scored model until DOSM confirms eligibility; request in-water logger verification. |
| Narrative flags | An anchor, trash, or bleaching mention indicates a recorded observation. | No mention does not prove absence and reporting intensity varies. | Present descriptive group differences only. |
| Missing values | Fold-local median imputation is acceptable for model comparison. | Missingness may be systematic. | Fit imputation within each training fold and retain missing values in processed data. |
| Repeated observations | Island observations are not fully independent. | Ordinary uncertainty estimates can be too narrow. | Use empirical forward-validation residual bands and label them screening uncertainty. |
| Priority tier | The top quartile is a field-work queue. | Rank boundaries can be mistaken for ecological thresholds. | Require ranger verification and do not prescribe closures or quotas. |
| Tourism data gap | State marine-park totals are verified for 2000-2017, and 2024 arrivals exist for only 11 monitoring units; no series links visitor exposure to reef change over time. | Allocating state totals to islands would fabricate precision. | Keep visitor and OpenDOSM context outside the model; show island arrivals only where they are published. |
| Tourism spending rate | Each island visitor spends the national domestic average of RM410 (DOSM Domestic Tourism Survey 2024). | Foreign visitors and divers spend more; day-trippers spend less. | Present island spending as a floor and cite DMPM's RM450 marine-park estimate as a cross-check. |
| Reef-attributable share | 10% of island tourism spending is attributable to reef presence (Spalding et al. 2017). | The coefficient is global, not fitted to Malaysia. | Use it as supporting context on Malaysian inputs only; never as an asset value or loss forecast. |
| Season-rest arithmetic | A one-month rest forgoes one twelfth of an island's annual spending, while reef-attributable revenue continues through a 10-15 year recovery. | Visitors may come later or elsewhere; the reef's response to a rest is not modelled. The ratio of the two figures is fixed by these assumptions. | Show both ringgit amounts and state that their ratio follows from the assumptions, not the data. |
| Economic valuation | DMPM's RM8.7 billion is a rounded annual Total Economic Value for six evaluated archipelagos during 2011-2015. | Treating it as current ReefSafe revenue, avoided loss, or a national reef total would be incorrect. | Show the published components and scope only; do not calculate NPV or island allocations. |

## What new data would change

Island-level visitor counts, vessel trips, mooring use, wastewater discharge, closure records, stable site identifiers, and in-water temperature would allow these assumptions to be tested. Until then, ReefSafe prioritises field verification rather than prescribing regulation.
