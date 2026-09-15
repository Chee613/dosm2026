# ReefSafe data provenance

`provenance_manifest.csv` is the machine-readable source register. Its status field determines how each dataset may be used.

## Evidence admitted to the scored model

- Reef Check Malaysia annual survey material supplies ecological measurements and documented impact mentions. The processed panel contains 404 monitoring-unit/year rows from 2007-2025. Annual reports are available from [Reef Check Malaysia](https://reefcheck.org.my/annualsurveyreports/).
- Geographic coordinates support location and regional grouping. Labuan is recorded as W.P. Labuan.

## Context kept outside the scored model

- NOAA Coral Reef Watch virtual stations provide regional heat context. Because written DOSM confirmation of external-data eligibility is not on file, NOAA variables are excluded from model features. They remain useful for descriptive associations and field-verification questions. Source: [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov/product/vs/data.php).
- State marine-park visitor totals for 2000-2017 come from five Department of Marine Park datasets on the data.gov.my archive (Creative Commons Attribution): [Johor](https://archive.data.gov.my/data/ms_MY/dataset/senarai-pelancong-ke-taman-laut-johor-dari-2000-2017), [Kedah](https://archive.data.gov.my/data/ms_MY/dataset/statistik-pelancong-ke-taman-laut-kedah-dari-2000-2017), [Pahang](https://archive.data.gov.my/data/ms_MY/dataset/statistik-pelancong-ke-taman-laut-pahang-dari-2000-2017), [Terengganu](https://archive.data.gov.my/data/en_US/dataset/statistik-pelancong-ke-taman-laut-terengganu-dari-2000-2017) and [Labuan](https://archive.data.gov.my/data/en_US/dataset/statistik-pelancong-ke-taman-laut-labuan-dari-2000-2017). All 90 rows of `taman_laut_visitors_2000_2017.csv` were checked against the published CSVs on 2026-09-15 with no mismatches. State totals are not allocated to islands.
- Island arrivals for 11 monitoring units in 2024 (`data/raw/structured/tourism/island_arrivals.csv`): Sabah Parks' [public visitor statistics](https://dashboard.sabahparks.org.my) for Tunku Abdul Rahman Park, Tun Sakaran Marine Park, Sipadan, Turtle Islands and Pulau Tiga (full year, Malaysian/international split); and the Terengganu State Tourism Department's January-August 2024 figures for Redang, Perhentian, Kapas, Lang Tengah, Tenggol and Bidong, as [reported by Malay Mail](https://malaysia.news.yahoo.com/tourist-arrivals-rise-terengganu-islands-050917502.html). Used only for the economic-context cards, never as model features.
- 2024 bleaching: `data/raw/structured/reef_check/bleaching_2024.csv` reproduces Table 1 (p.14) of Szereday et al. (2025), [*The 4th Global Coral Bleaching Event in Malaysia*](https://reefcheck.org.my/wp-content/uploads/2025/07/2024CoralBleachingImpactReportMalaysia.pdf) (Coralku and Reef Check Malaysia). The dashboard cites the report's own headline figures (p.4): 50.7% of corals bleached and 34.1% average mortality, transcribed in `bleaching_2024_headline.csv`.
- OpenDOSM state series are descriptive context only and are not proxies for individual-reef tourism exposure.

## Economic context

The Department of Marine Park Malaysia booklet *Total Economic Value of Marine Biodiversity: Malaysia Marine Parks* reports a rounded annual Total Economic Value of **RM8.7 billion** from studies of six evaluated archipelagos during 2011-2015: Pulau Payar, Pulau Perhentian, Pulau Redang, Pulau Tioman, Pulau Tinggi, and Pulau Labuan. The local primary PDF and page-level transcription are stored at:

- `data/raw/unstructured/economic_valuation/TOTAL_ECONOMIC_VALUE_OF_MARINE_BIODIVERSITY.pdf`
- `data/raw/structured/economic_valuation/dmpm_tev_2011_2015.csv`

The component values sum to RM8.68699 billion before rounding. ReefSafe does not reinterpret the benchmark as current revenue, an island allocation, avoided loss, or net present value. Archived primary PDF: [Protected Planet country information](https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf).

## Excluded pending verification

- The accommodation inventory has no reproducible audit trail supporting its claimed completeness. It remains in `data/raw` for traceability but is excluded from charts, model features, rankings, economic figures and policy claims.

## Supporting methods from foreign sources

- Spalding et al. (2017), *Marine Policy* 82:104-113, supplies the 10% share of island tourism spending attributed to reef presence. It is a method coefficient applied to Malaysian inputs, used to support a statement, not raw data.
- James Cook University (2019) supplies the 10-15 year recovery window used in the season-rest comparison.

## Interpretation boundary

Associations are not causal effects. The available data cannot estimate the percentage of reef change caused by tourism, legal visitor capacity, island revenue, or guaranteed intervention benefits.
