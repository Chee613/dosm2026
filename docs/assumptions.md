# ReefSafe assumption register

These assumptions define what the current evidence can support. They are not hidden model facts; each one should be revisited when better data arrives.

| Area | Working assumption | Risk if wrong | Current mitigation |
|---|---|---|---|
| Island identity | An island name refers to a sufficiently comparable monitoring unit across years. | Boundary or site-composition changes can look like ecological change. | Retain island, park, coordinates, year and extraction confidence; verify large movements against source reports. |
| Survey comparability | Reported live coral cover is comparable enough across survey years for directional screening. | Method, site or observer changes can create artificial differences. | Treat results as screening only and retain source confidence. |
| Irregular intervals | Annualized change is approximated as linear between two survey observations. | Short disturbances and recoveries between surveys are unobserved. | Store survey and target years; never describe intermediate annual values as observed. |
| Thermal exposure | A NOAA regional station is an adequate proxy for broad heat exposure near its matched islands. | Local reefs can experience different temperature and current conditions. | Describe DHW as regional evidence and request in-water logger confirmation. |
| Timing | Conditions recorded at the current survey can help screen the island's next observed change. | A stressor occurring after the current survey may drive the later outcome. | Use lagged wording and avoid causal attribution. |
| Narrative flags | A reported anchor, trash or bleaching mention is evidence of presence; no mention is not proof of absence. | Reporting intensity varies by island and year. | Use group comparisons as descriptive only and show the limitation beside results. |
| Missing values | Median imputation within each training fold is adequate for model comparison. | Missingness may be systematic rather than random. | Fit imputation inside each fold; retain missingness in the processed dataset. |
| Temporal transfer | Earlier island-year patterns contain limited information relevant to later target years. | Regime shifts can make historical relationships unstable. | Use expanding-year validation and show the baseline comparison. |
| Residual dependence | Repeated island observations are not fully independent. | Conventional uncertainty can be too narrow. | Do not present formal causal confidence intervals; use empirical screening bands. |
| Priority threshold | The top quartile is a practical workload queue, not an ecological or legal threshold. | Users may mistake rank 10 versus 11 for a scientific boundary. | Label the tier “High screening priority” and require field verification. |
| Economic context | State or national tourism totals cannot represent individual-island pressure without allocation data. | Downscaling would fabricate precision. | Keep OpenDOSM tourism/GDP series descriptive and outside the island prediction features. |

## Assumptions that would change with new data

Island-level visitor counts, vessel trips, mooring use, wastewater discharge, closure records, site identifiers and in-water temperature would allow several assumptions above to be tested or removed. Until then, ReefSafe remains a transparent triage tool rather than a carrying-capacity or causal-impact model.
