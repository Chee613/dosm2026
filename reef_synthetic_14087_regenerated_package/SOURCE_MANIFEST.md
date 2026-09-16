# Regenerated Reef + Tourism Synthetic Dataset Package

Aligned to `reef_synthetic_14087.csv`.

## Final master
- `master_reef_tourism_dataset.csv`: 14,087 rows x 50 columns.

## Structured raw inputs
- `data/raw/structured/reef_check/ReefCheck_Malaysia_FINAL.xlsx`: `model_ready` contains 14,087 rows x 40 ecological/provenance columns.
- `data/raw/structured/geocoding/island_coordinates.csv`: 56 unique islands; fixed coordinates and marine-park lookup keyed by `island`.
- `data/raw/structured/infrastructure/island_accommodations.csv`: 56 unique islands; fixed infrastructure lookup keyed by `island`.
- `data/raw/structured/noaa_crw/malacca_strait.txt`
- `data/raw/structured/noaa_crw/northern_borneo.txt`
- `data/raw/structured/noaa_crw/sabah.txt`
- `data/raw/structured/noaa_crw/singapore.txt`
- `data/raw/structured/noaa_crw/west_gulf_of_thailand.txt`

Each NOAA TXT contains synthetic daily records for 2012-2025. Annual `max(DHW)` and `mean(SSTA)` exactly reproduce the station-year values in the final master.

## Join normalization applied
The previous synthetic master varied some fields row-by-row even though the stated preprocessing pipeline joins them from lookup tables. To make this package reproducible:
- `latitude`, `longitude`, `marine_park` are fixed per island.
- infrastructure fields are fixed per island.
- `noaa_max_dhw`, `noaa_mean_ssta` are fixed per `noaa_station_id + survey_year`.
- the 40 ecological/provenance fields remain row-level.

## Validation
- coordinate mismatches: 0
- infrastructure mismatches: 0
- NOAA join mismatches: 0
- NOAA raw annual aggregate mismatches: 0

## Original 19 PDF reports
The 2007-2025 Reef Check annual PDFs are source documents, so they were not fabricated. Their expected filenames are listed in `data/raw/unstructured/reef_check_reports/README.md`.
