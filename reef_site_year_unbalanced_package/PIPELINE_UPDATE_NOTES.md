# Pipeline Update Notes

## Observation key

Use:

```python
(site_id, survey_year)
```

It must be unique.

## Temporal sequencing

Group transitions by `site_id`, not `island`.

Missing years are allowed. For example:

```text
2019 -> 2021
```

is a valid next-observation transition with `years_since_prev = 2`.

## 2024/2025 paired comparison

Pivot on:

```python
index=["island", "site_id"]
```

and drop sites not observed in both years.

Current paired n: **444**.

## Validation sizes

Do not hard-code 560. Derive n from the actual transition table.

Current latest target-year n:

```text
2021: 453
2022: 490
2023: 463
2024: 512
2025: 487
```
