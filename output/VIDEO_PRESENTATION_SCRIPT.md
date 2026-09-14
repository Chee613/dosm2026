# ReefSafe presentation script (target: 9 minutes 30 seconds)

Replace the bracketed team details before recording. Keep the final video below 10 minutes.

## 0:00-0:40 — Introduction

**Visual:** Title, team members, DOSM Datathon 2026 theme.

> We are [TEAM NAME] from [INSTITUTION]. ReefSafe is an evidence-led screening tool that helps marine-park teams decide which monitored islands should receive earlier field verification. It uses long-running reef observations for prediction and keeps NOAA thermal-stress evidence as context. It does not calculate legal visitor limits or claim that tourism caused reef decline.

## 0:40-1:50 — The decision problem

**Visual:** Observed national mean live coral cover by survey year.

> Marine managers have limited survey, enforcement and conservation resources. The practical question is not simply which reef has low coral cover. It is which island should be checked first, what evidence supports that priority, and how uncertain the result is.
>
> Our processed evidence contains 404 island-year observations across 56 islands from 2012 to 2025. The unweighted mean among surveyed islands fell from 57.1 percent in 2012 to 39.8 percent in 2025. Survey composition changes over time, so we present this as descriptive context rather than a fixed-panel national estimate.

## 1:50-3:05 — Data and integrity

**Visual:** Reef Check, NOAA, OpenDOSM and provenance flow.

> Reef Check Malaysia reports provide coral, substrate, fish, invertebrate and narrative stressor evidence. NOAA Coral Reef Watch provides regional sea-surface temperature anomaly and Degree Heating Weeks. Because written eligibility confirmation is still pending, NOAA variables are excluded from the scored production model and used only for descriptive diagnostics. OpenDOSM tourism and GDP series are retained only as national or state context; we do not fabricate island-level tourism pressure from those totals.
>
> During validation we corrected the NOAA DHW column, removed two generated tourism proxy fields, retained missing values, and preserved source-confidence labels. These controls matter because a polished dashboard cannot rescue unreliable evidence.

## 3:05-4:40 — Prediction design and performance

**Visual:** Next-observation timeline and model comparison chart.

> Each example uses conditions at one island survey to predict the annualized coral-cover change recorded at that island's next survey. Evaluation uses the latest five target years, and every test year is trained only on earlier target years. This prevents future information from leaking into training.
>
> We compared a mean baseline, Ridge regression, Gradient Boosting and Random Forest. Gradient Boosting achieved the best forward-test MAE at 5.859 percentage points per year, versus 5.991 for the baseline. That is only a 2.2 percent improvement, with R-squared of 0.070. We therefore use the model only to rank field checks, never as an automated forecast or enforcement rule. XGBoost is not presented as the answer because the limiting issue is evidence quality and temporal transfer, not algorithm complexity.

## 4:40-5:55 — Factor relationships and assumptions

**Visual:** Factor-relationship figure and assumption register.

> We also examine factors measured at the current observation against the next observed coral change. Maximum NOAA DHW has a weak negative Spearman relationship: rho minus 0.105, with 348 observations and p equal to 0.051. Mean next change is minus 0.55 percentage points per year below DHW 1, compared with minus 1.38 at DHW 4 or higher.
>
> This is directionally consistent with heat stress, but it is not causal proof. NOAA stations are regional proxies, surveys are irregular, islands repeat in the sample, and local events are incompletely measured. Narrative anchor, trash and bleaching mentions also depend on reporting intensity; no mention is not confirmed absence.

## 5:55-7:45 — Dashboard demonstration

**Visual:** Open the web dashboard, switch between its three views, and select an island. Keep Dashboard.xlsx available as an offline companion.

> The dashboard opens on a national overview. I select an island in the monitoring view. The live coral cover, observed change, predicted next change, empirical prediction band and priority tier update together.
>
> The evidence section is deliberately separate from the prediction. If regional DHW reaches 4, the next step is a coordinated bleaching survey, with an explicit warning not to attribute thermal loss to visitors. An anchor mention prompts a mooring and anchoring inspection. Elevated waste or pollution indicators prompt wastewater checks. Where no stressor dominates, the system recommends field validation before restrictions.
>
> The top quartile is labelled High screening priority. This is a workload queue, not an ecological threshold. The evidence view also exposes the visitor-series gap, factor relationships, model comparison and year-by-year validation. The Excel workbook preserves the selector and full supporting tables for offline review.

## 7:45-8:25 — Economic context

**Visual:** Department of Marine Park Malaysia total-economic-value components.

> Reef conservation also has a documented economic basis. Department of Marine Park Malaysia studies conducted from 2011 to 2015 reported a rounded annual total economic value of 8.7 billion ringgit across six evaluated marine-park archipelagos. We reproduce the seven published components, led by aesthetic value, without converting that national benchmark into island revenue or a net-present-value simulation.

## 8:25-9:10 — Operational use and next data

**Visual:** Four-step operating cycle.

> The operating cycle is simple: refresh after new survey reports, review confidence and uncertainty, verify conditions in the field, and record the outcome for the next cycle.
>
> The highest-value next enhancement is better island-level operational evidence: daily visitors, vessel trips, mooring use, wastewater discharge, closures, consistent survey-site identifiers and in-water temperature. Those data would let us test pressure-response relationships instead of relying on broad proxies.

## 9:10-9:30 — Closing

**Visual:** Final dashboard and project guardrail.

> ReefSafe's value is transparency and restraint. It shows what was observed, what was predicted, how uncertain the prediction is, what assumption is being made, and what the data cannot support. It turns heterogeneous public evidence into a defensible queue for faster field verification and more sustainable tourism management.
