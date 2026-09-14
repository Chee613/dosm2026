# ReefSafe data provenance

`provenance_manifest.csv` is the machine-readable source register. Its status field determines how each dataset may be used.

## Evidence admitted to the scored model

- Reef Check Malaysia annual survey material supplies ecological measurements and documented impact mentions. The processed panel contains 404 monitoring-unit/year rows from 2007-2025. Annual reports are available from [Reef Check Malaysia](https://reefcheck.org.my/annualsurveyreports/).
- Geographic coordinates support location and regional grouping. Labuan is recorded as W.P. Labuan.

## Context kept outside the scored model

- NOAA Coral Reef Watch virtual stations provide regional heat context. Because written DOSM confirmation of external-data eligibility is not on file, NOAA variables are excluded from model features. They remain useful for descriptive associations and field-verification questions. Source: [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov/product/vs/data.php).
- The verified marine-park visitor source covers 2000-2009 aggregates for Johor, Kedah, Labuan, Pahang, and Terengganu. It is not allocated to islands. Source: [data.gov.my archive](https://archive.data.gov.my/data/ms_MY/dataset/jumlah-pelawat-taman-laut-malaysia-dari-tahun-2000-hingga-2009-).
- OpenDOSM state series are descriptive context only and are not proxies for individual-reef tourism exposure.

## Economic context

The Department of Marine Park Malaysia booklet *Total Economic Value of Marine Biodiversity: Malaysia Marine Parks* reports a rounded annual Total Economic Value of **RM8.7 billion** from studies of six evaluated archipelagos during 2011-2015: Pulau Payar, Pulau Perhentian, Pulau Redang, Pulau Tioman, Pulau Tinggi, and Pulau Labuan. The local primary PDF and page-level transcription are stored at:

- `data/raw/unstructured/economic_valuation/TOTAL_ECONOMIC_VALUE_OF_MARINE_BIODIVERSITY.pdf`
- `data/raw/structured/economic_valuation/dmpm_tev_2011_2015.csv`

The component values sum to RM8.68699 billion before rounding. ReefSafe does not reinterpret the benchmark as current revenue, an island allocation, avoided loss, or net present value. Archived primary PDF: [Protected Planet country information](https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf).

## Excluded pending verification

- The local 2010-2017 visitor extension has no traceable source beyond the verified 2000-2009 portal coverage.
- The accommodation inventory has no reproducible audit trail supporting its claimed completeness.

Both files remain in `data/raw` for traceability but are excluded from charts, model features, rankings, and policy claims.

## Interpretation boundary

Associations are not causal effects. The available data cannot estimate the percentage of reef change caused by tourism, legal visitor capacity, island revenue, or guaranteed intervention benefits.
