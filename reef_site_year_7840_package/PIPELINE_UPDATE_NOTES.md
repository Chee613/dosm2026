# Required pipeline changes for reef-site-year data

## 1. `make_next_observation_rows`

Group by `site_id` instead of `island`.

The uniqueness invariant should be:

```python
(site_id, survey_year)
```

and every generated transition must satisfy:

```python
target_year > survey_year
```

## 2. Annual paired comparison

Change the pivot from an island key to a site key:

```python
paired = (
    master.filter(pl.col("survey_year").is_in([2024, 2025]))
    .select(["island", "site_id", "survey_year", "live_coral_cover_pct"])
    .pivot(
        on="survey_year",
        index=["island", "site_id"],
        values="live_coral_cover_pct",
    )
    .drop_nulls()
)
```

This produces one value per reef site per year.

## 3. Latest predictions

The latest-year table contains 560 site rows.
Include `site_id` and `site_name` in prediction / stress-contribution outputs so sites on the same island remain distinguishable.

## 4. Uniqueness guard

Before training:

```python
duplicates = (
    master.group_by(["site_id", "survey_year"])
    .len()
    .filter(pl.col("len") > 1)
)

if duplicates.height:
    raise ValueError("Duplicate site-year observations detected")
```
