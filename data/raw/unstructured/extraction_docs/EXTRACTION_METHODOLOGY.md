# Data Extraction Methodology

**Dataset:** Reef Check Malaysia coral reef survey panel, 2012–2025
**Output:** `ReefCheck_Malaysia_FINAL.xlsx` — 404 island-year records, 56 islands, 9 states
**Prepared for:** DOSM Datathon 2026

---

## 1. Source data

All data comes from the **Reef Check Malaysia Annual Survey Reports**, published at
`https://reefcheck.org.my/annualsurveyreports/`. Nineteen reports were obtained, covering
2007 to 2025.

Reef Check Malaysia is a Malaysian non-profit. Surveys are carried out by trained volunteers
using the international Reef Check protocol, in partnership with the Department of Fisheries
Malaysia and Sabah Parks. The data therefore originates entirely within Malaysia, as the
competition rules require.

No data was purchased, simulated, imputed or generated. Every value in the final dataset was
read out of a published report.

### Why extraction was necessary

Reef Check Malaysia publishes **PDF reports, not datasets**. The figures exist only inside
prose, bar-chart data rows, pie charts and, in recent years, images. There is no CSV, no API
and no open-data listing. Building a usable panel meant extracting the numbers from the
documents.

---

## 2. The core problem: the report format changed four times

The single biggest obstacle was that Reef Check Malaysia redesigned the report repeatedly.
A parser that works on one era fails silently on another. The eras are:

| Years | Per-island pages | Substrate | Fish and invertebrates |
|---|---|---|---|
| 2007–2012 | None | National narrative only | National narrative only |
| 2013–2019 | Yes | Full 10 categories (HC, SC, RKC, NIA, SP, RC, RB, SD, SI, OT) | Labelled data rows (BF…GR, BCS…GC) |
| 2020–2022 | Yes | Aggregated to 6 groups, drawn as a pie chart | Labelled data rows |
| 2023–2025 | Yes | 6-group pie | **Species labels removed** — values sit beside icons |

Two consequences follow, and both are limitations of the source, not of the method:

- **Nutrient Indicator Algae (NIA) exists only for 2013–2019.** From 2020 it is merged with
  silt into a single "Pollution Indicators" group and cannot be recovered.
- **2007–2012 contain no per-island tables at all**, so those years cannot enter an
  island-level panel.

---

## 3. Extraction strategy: two independent pipelines

Because a single automated pass can fail silently, the reports were extracted **twice, by
unrelated methods**, and the two results compared. Disagreements were then resolved against
the source document.

```
                    ┌─────────────────────────┐
   19 PDF reports ──┤                         │
                    │  Pipeline A (PDF)       │──┐
                    │  pdfplumber + geometry  │  │
                    └─────────────────────────┘  │    ┌──────────────┐
                                                 ├────┤ Reconcile    │── FINAL
                    ┌─────────────────────────┐  │    │ + validate   │
   19 PDF reports ──┤  Pipeline B (Markdown)  │──┘    └──────────────┘
                    │  Open Data Loader       │
                    └─────────────────────────┘
```

### Tools

| Tool | Version | Used for |
|---|---|---|
| Python | 3.11 | All processing |
| pdfplumber | 0.11.9 | Pipeline A — text, word coordinates, vector paths, embedded images |
| Open Data Loader | — | Pipeline B — PDF to Markdown and structured JSON |
| pandas | 3.0.2 | Assembly, joins, validation |
| openpyxl | 3.1.5 | Workbook output |
| poppler-utils, tesseract | — | Evaluated for the 2024 font problem, not used in the final pipeline |

---

## 4. Pipeline A — direct PDF parsing

### 4.1 Word-level line reconstruction

`page.extract_text()` was **not** used. On two-column layouts it interleaves the chart data
row with body prose, which corrupts values.

Instead, `page.extract_words()` returns each word with x/y coordinates. Words were clustered
into visual lines by rounding the `top` coordinate, then sorted left to right within each
line. This reconstructs the table rows as they appear on the page.

### 4.2 Substrate tables (2013–2019)

Locate the header line containing `HC … OT`, then find the value row beneath it. Several
layout variants had to be handled:

- values on the same line as the label — `2018 (n=18) 58.68% 3.92% …`
- the year alone on one line, values on the next — 2013
- the label mangled by a glued axis character — `2I017`, `S2018 (n=6)43.23%1.35%`
- values with no separating space — `0.0332.320.00` is 0.03, 32.32, 0.00
- **percentages written without a `%` sign** — the 2013 charts print
  `|2013|54.8|3.63|0.63|…|`, so a parser that requires `%` silently drops the whole year
- **percentages written as fractions** — one 2013 chart is plotted 0–1 and sums to 1.00,
  not 100; detected by the sum and rescaled ×100

### 4.3 Pie charts (2020–2025) — vector geometry

The pie slices are vector paths. Rather than read the printed labels, each slice's
**angular extent** was measured directly from its path coordinates and divided by 360°.

1. Find the pie centre as the point shared by the most slice paths.
2. For each slice, take the arc endpoints and compute the angle swept, clockwise from north.
3. Identify each slice by its **fill colour**, matched to the legend palette. Colour keying
   means slice order does not matter.
4. Reject the page if the six values do not sum to ~100.

**Validation.** On 2025 Seri Buat, where the printed values are readable, the measured angles
reproduced them to within 0.02 percentage points:

| Group | Printed | Measured |
|---|---|---|
| Live Coral Cover | 54.22 | 54.20 |
| Other | 1.09 | 1.09 |
| Available Substrate | 23.75 | 23.75 |
| Sand | 4.22 | 4.22 |
| Disturbance Indicators | 14.38 | 14.38 |
| Pollution Indicators | 2.34 | 2.35 |

A label-reading fallback handles pies where two groups are 0% and the geometry degenerates
(e.g. Payar 2021). It assigns printed percentages to groups by angle, anchored on which
legend colours were actually drawn — a group with no slice is a zero.

### 4.4 Icon-labelled charts (2023–2025) — position matching

From 2023 the fish and invertebrate species names are images, not text. The numbers remain as
text. Species identity was recovered from layout:

- Within each trade-category block, species appear in Reef Check's canonical order.
  Fish: aquarium = butterflyfish; food = sweetlips, snapper, barramundi cod, parrotfish,
  moray eel, grouper; live-food = humphead wrasse, bumphead parrotfish.
- Each species icon (45–115 px wide) is matched to the nearest value by y-coordinate within
  its column.
- A **red ✗ is a 33×33 px image** occupying the position a number would take. It means the
  species was not recorded and is written as 0.0, consistent with how earlier labelled
  reports record absences.
- A species icon with neither a number nor a ✗ beside it is decoration, not data, and is
  discarded — this removes the crown-of-thorns picture that sits in a callout box.

**Validation.** 2025 national fish page reproduced exactly: BF 4.99, SL 0.30, SN 4.58,
BC 0.00 (✗), PF 3.27, ME 0.03, GR 0.70, HW 0.03, BP 0.07.

---

## 5. Pipeline B — Markdown extraction

The same PDFs were converted with **Open Data Loader**, producing Markdown plus a structured
JSON with page numbers, bounding boxes and fonts for every text element.

### 5.1 Flattening

Markdown tables were exploded — pipes stripped, `<br>` and `<br><br>` split into separate
logical lines, image references removed — producing an ordered list of text fragments.

### 5.2 Two-pass anchor matching

**This is the step that caught the most serious error.** In the 2013–2019 layout the chart
title appears *after* the data row inside the same table cell:

```
| |HC|SC|RKC|NIA|SP|RC|RB|SD|SI|OT|
|2018 (n=10)|42.31%|1.38%|0.50%|8.19%|…|
… Substrate Cover at Perhentian Island, 2018|
```

A parser that attributes each data row to the most recent title shifts **every island by
one**. The fix is a two-pass design:

1. Collect every chart title with its line index and type (substrate / fish / invertebrate).
2. Collect every data row with its line index and type.
3. Assign each data row to the **nearest title of the same type, in either direction**,
   rejecting matches more than 40 lines away.

### 5.3 Pie charts

In the 2022–2025 markdown, each pie occupies one table cell holding the six values, then the
chart title, then the six legend labels — in order. Values are paired to labels positionally
and checked to sum to ~100. This required no geometry.

For 2020–2021 the pie is loose text whose visual order does not follow the legend, so those
years fall back to Pipeline A.

---

## 6. Reconciliation

The two pipelines were compared on every island-year and field they both covered.

| | |
|---|---|
| Island-years matched | 343 |
| Values compared | 5,872 |
| **Agreed exactly** | **5,746 (97.9%)** |
| Disagreed | 126 |

Two blocks agreed on **100%** of comparable rows: the 6-group substrate values and the
survey-site counts (`n_sites`).

### Resolution

Every one of the 126 disagreements was checked against the source document. **In every case
the Markdown extraction was correct**, and Pipeline A had picked up a neighbouring island's
chart on a two-column page.

Worked example — Pangkor Laut 2017, verbatim from the report:

```
|2017 (n=1)|66.25%|0.00%|0.63%|0.00%|0.00%|10.00%|18.75%|3.13%|0.00%|1.25%|
"…with 66.25% live coral cover, above the average (35.67%) for the Malacca Strait region"
|BF SL SN BC HW BP PF ME GR  2017 (n=1) 10.50 0.00 0.25 0.00 0.00 0.00 0.00 0.00 0.75|
```

Markdown returned HC 66.25, RB 18.75, RC 10.00, butterflyfish 10.50 — correct.
Pipeline A returned HC 28.75, RB 2.50, RC 61.25, butterflyfish 2.50 — wrong.

Eight island-years were affected: Tinggi 2015, Kapas 2016, Mantanani 2013 and 2018,
Usukan Cove 2018, Pangkor Laut 2017, Sipadan 2016, Lahad Datu 2015. All are listed in the
`disagreements_resolved` sheet with both values side by side.

### Precedence rule

**Markdown is authoritative wherever it reached.** Pipeline A fills only what Markdown
structurally cannot carry — and those are precisely the blocks that agreed 100% in testing:

| Block | From Markdown | From PDF |
|---|---|---|
| Substrate, 10 categories | 156 | 32 |
| Substrate, 6 groups | 117 | 277 |
| Fish | 274 | 148 |
| Invertebrates | 248 | 168 |

Every record carries a `confidence` label:

| Label | Rows |
|---|---|
| mixed — markdown primary, PDF filled gaps | 307 |
| PDF geometry only — not cross-checked | 46 |
| markdown only | 43 |
| verified — markdown corrected an error in the PDF pass | 8 |

---

## 7. Validation rules

Applied throughout; rows failing them were rejected rather than stored.

1. **Composition sums.** The 10 substrate categories must sum to 100 ± tolerance, as must the
   6 groups. Every retained row passes.
2. **Pie cross-check.** Geometric measurement was validated against printed labels where both
   were available (agreement within 0.02 pp).
3. **Regional benchmarks.** A region's average is one number per year. Within each
   year × eco-region group the modal value is taken and values differing by more than
   2 points are discarded. This removed contaminated values — chart axis gridlines such as
   0.83%, 1.00% and 7.29% had been captured by an earlier regex.
4. **Axis-label guard.** Narrative live-coral-cover values falling exactly on an axis tick
   (0, 20, 40, 60, 80, 100) and disagreeing with the chart by more than 5 points are
   discarded. This caught a spurious 80.0% reading.
5. **Cross-pipeline agreement**, as in section 6.

---

## 8. Post-processing

**Island name normalisation.** Variants were merged — "Bidong & Yu" / "Bidong and Yu",
"Pulau Aur and Dayang" / "Aur & Dayang", "TSMP" / "Tun Sakaran Marine Park",
"TARP" / "Tunku Abdul Rahman Park". Left unmerged, an island's time series splits in two.

**State assignment.** The reports print the state only from 2020. For earlier years the state
was recovered by searching all 19 reports for the island name and a state name **in the same
sentence**, then reading the quotation:

> "Pulau Rawa is under Mersing District, Johor." (2017)
> "Balambangan Island is an island in Kudat Division, Sabah." (2015)
> "Sembilan Islands (off Lumut, Perak)." (2012)

Word boundaries were required — an early attempt matched "Rawa" inside "Sa**rawa**k" and
assigned Pulau Rawa to Sarawak.

**Eco-region.** Some reports head island pages with the eco-region rather than the state
("Sunda Shelf – Tioman"). These were separated into their own field and back-filled per island.

**Derived variables.**

| Variable | Definition |
|---|---|
| `live_coral_cover_pct` | Chart value, else narrative value, else HC + SC |
| `lcc_change`, `lcc_change_rate` | Change since the island's previous survey, and per year |
| `island_vs_region_pct` | Island cover minus its regional average — removes the regional climate trend |
| `cot_outbreak` | 1 if crown-of-thorns > 0.3 per 100 m², Reef Check's stated healthy ceiling |
| `grazer_ratio` | Parrotfish ÷ Diadema urchins — low values indicate fish grazers were removed |
| `n_highvalue_fish_absent` | Count of barramundi cod, humphead wrasse, bumphead parrotfish recorded as zero |

**Column reduction.** 74 columns were reduced to 39. Removed: exact duplicates
(`live_coral_cover_pct` and `grp_live_coral_cover` differed by 0.0 across all rows;
`sub_RC` equals `grp_available_substrate` exactly), constants, validation artifacts, and
linear combinations of other columns. Species present in fewer than a third of surveys were
folded into absence counts rather than deleted, preserving the overfishing signal.

**National rows excluded.** Six rows were Malaysia-wide averages rather than islands. They are
retained in `full_data` and excluded from `model_ready`, since training on an aggregate of the
training set is a leak.

---

## 9. Known limitations

**The 2024 report has a broken font.** Its embedded Calibri subset maps several glyphs to
blank: "Substrate Composition" extracts as "Substrate Composi on", island names lose their
first letter ("at **apas**" for Kapas), and digits drop out of chart labels. This affects
**every text-based tool**, including Open Data Loader — it is a property of the PDF, not of
the extractor. Those pages were measured geometrically from the chart vectors instead.

**NIA is unavailable after 2019.** From 2020 it is published only as part of "Pollution
Indicators" (nutrient algae + silt). The split cannot be reconstructed: tested across 26
islands in 2018, NIA is a median 98% of the combined figure, but the 10th–90th percentile
range runs 0.13 to 1.00, and several mainland-adjacent sites (Pulau Rawa, Pangkor Laut,
Pulau Penyu) record 0% NIA with silt dominating. Nutrient analysis is therefore restricted to
2013–2019 (183 rows) and uses measured values only.

**No fish or invertebrate data for 2009 national figures.** The 2011 report tabulates
substrate for 2009–2011 but publishes no fish or invertebrate figures for those years.

**`n_sites` missing from 2020.** The reports stopped printing the survey-site count, so the
panel cannot be weighted by survey effort throughout.

**Impact flags measure mention, not severity.** `impact_anchor` and similar are keyword
presence flags: they record that an impact was named on that island's page. A longer or more
detailed page scores higher. They should not be read as intensity measures.

**Forty-six rows are single-sourced.** Rows labelled "PDF geometry only" have no independent
confirmation. Any finding that rests on one of them should be checked by hand.

**One source error observed.** In the 2017 report, the fish chart on the Payar page is labelled
`2016 (n=3)` while the substrate chart on the same page is labelled `2017 (n=5)`. This appears
to be a typographical error in the publication.

---

## 10. Reproducibility

The extraction narrative above documents how the structured Reef Check workbook was
created and audited. The original one-off extraction utilities are not retained in this
repository, so PDF-to-workbook extraction is provenance documentation rather than a fully
rerunnable stage. The 19 source PDFs and the resulting structured workbook are both retained
for verification.

The submitted analysis is reproducible from the structured workbook onward:

| Script | Purpose |
|---|---|
| `scripts/run_preprocessing.py` | Normalize the Reef Check panel, join coordinates and correctly parse NOAA fields |
| `scripts/pipeline.py` | Shared NOAA parsing, next-observation target alignment and expanding-year splits |
| `scripts/train_models.py` | Forward-test model comparison, factor diagnostics and priority output |
| `src/build_dashboard.mjs` | Build the interactive Excel dashboard from processed outputs |
| `src/generate_report.py` | Build the formal report from the same metrics and figures |

**Archived extraction input:** `data/raw/structured/reef_check/ReefCheck_Malaysia_FINAL.xlsx`.

**Reproducible analysis output:** `data/processed/master_reef_tourism_dataset.csv`, model
evaluation files, factor diagnostics, the executed notebook, dashboard and report.

---

## Citation

Reef Check Malaysia. *Annual Survey Reports, 2007–2025.* Kuala Lumpur.
Available at https://reefcheck.org.my/annualsurveyreports/

Supporting statistics: Department of Environment Malaysia (marine water quality monitoring);
Department of Statistics Malaysia (Domestic Tourism Survey); Department of Fisheries Malaysia
(marine park administration).
