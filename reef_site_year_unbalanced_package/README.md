# Reef Site-Year Synthetic Dataset Package — Unbalanced Panel

## Processed predictive panel

This package contains an **unbalanced synthetic reef-site-year panel**:

- **6,381 observed reef-site/year rows**
- **560 registered synthetic reef sites**
- **56 island labels**
- **14 modeling years: 2012–2025**
- annual observed-site counts: **388–512**
- annual surveyed-island counts: **53–56**
- **5,821 valid next-observation transitions**
- **0 duplicate site-year keys**
- **0 same-year or backwards transitions**

Not every site appears every year.

## Source archive vs modeling window

Do not conflate the source-document archive with the processed modeling window.

- Source archive: Reef Check annual reports may span **2007–2025**.
- Predictive panel: **2012–2025**, exactly **14 modeling years**.

## Synthetic missingness disclosure

The site IDs, site-level ecological disaggregation, and survey missingness are synthetic.

The missingness pattern was generated to produce a methodologically realistic **unbalanced panel** for pipeline development and model prototyping. It must not be described as documented historical weather cancellations or actual Reef Check non-response unless separately verified from source records.

## Latest validation target sizes

- 2021: **n = 453**
- 2022: **n = 490**
- 2023: **n = 463**
- 2024: **n = 512**
- 2025: **n = 487**

2024/2025 paired comparison: **444 sites observed in both years**.
