# Reef Site-Year Synthetic Dataset Package

## Modeling unit

**One row = one synthetic reef site in one survey year.**

- 56 islands
- 10 stable synthetic reef sites per island
- 14 annual observations per site (2012-2025)
- 560 unique reef sites
- 7,840 site-year rows
- 7,280 valid next-observation transitions
- 0 duplicate site-year keys
- 0 same-year transitions

## Final model dataset

`data/processed/master_reef_tourism_dataset.csv`

Schema: 52 columns = original 50 columns +:
- `site_id`
- `site_name`

The site identifiers are inserted immediately after `island`.

## Raw / structured inputs

### Ecological core
- `data/raw/structured/reef_check/ReefCheck_Malaysia_FINAL.xlsx`
- `data/raw/structured/reef_check/ReefCheck_Malaysia_model_ready.csv`

These contain the site-year ecological core. Each row is a single reef-site-year observation.

### Geographic data
- `data/raw/structured/geocoding/island_coordinates.csv`
- `data/raw/structured/geocoding/reef_site_coordinates.csv`

Use `reef_site_coordinates.csv` for the site-level pipeline.
Join key: `site_id`.

### NOAA Coral Reef Watch
- `malacca_strait.txt`
- `northern_borneo.txt`
- `sabah.txt`
- `singapore.txt`
- `west_gulf_of_thailand.txt`

NOAA values remain station-year environmental context and are shared by sites mapped to the same station and year.

### Island infrastructure
- `data/raw/structured/infrastructure/island_accommodations.csv`

Infrastructure remains island-level.
Join key: `island`.

## Important modeling change

The temporal entity is now `site_id`, not `island`.

Training code should:
- group next observations by `site_id`;
- pivot annual paired comparisons using `site_id` (or `island + site_id`);
- retain `island` as a grouping/context field;
- ensure `target_year > survey_year`.

## Synthetic-data note

The 560 reef-site identities and site-level ecological disaggregation are synthetic.
They are designed for pipeline development, demonstration and predictive-model prototyping.
They must not be presented as observed Reef Check field measurements.
