# Reef-adjacent economy and season-rest cards: method and sources

This note explains the two economic cards on the ReefSafe dashboard's Overview tab: what they show, how every number is calculated, and where the input data comes from. All figures below match `data/processed/park_economics.csv` and `data/processed/tourism_economics.json`, which the dashboard reads.

## What the cards show

| Card | Headline | Meaning |
|---|---|---|
| Reef-adjacent economy | **RM60.09 million a year** | Tourist spending attributable to reefs, summed across 10 marine parks with published visitor counts. A national estimate and a floor, not a total for every reef. |
| Season rest vs long-term reef revenue | **RM23.72M vs RM284.66M–RM426.99M** | The spending lost by resting the parks that hold high-priority reefs for one month, against the reef-attributable revenue those parks earn over a 10–15 year recovery period. |

Neither card is a forecast. Both are arithmetic on published inputs, and both are kept outside the prediction model.

## Source data

### Visitor numbers

**Peninsular Malaysia and Labuan** — Department of Marine Park Malaysia, state marine-park visitor statistics 2000–2017, published on the data.gov.my archive under a Creative Commons Attribution licence:

| State | Dataset |
|---|---|
| Johor | [Senarai Pelancong Ke Taman Laut Johor dari 2000-2017](https://archive.data.gov.my/data/ms_MY/dataset/senarai-pelancong-ke-taman-laut-johor-dari-2000-2017) |
| Kedah | [Statistik Pelancong Ke Taman Laut Kedah dari 2000-2017](https://archive.data.gov.my/data/ms_MY/dataset/statistik-pelancong-ke-taman-laut-kedah-dari-2000-2017) |
| Labuan | [Statistik Pelancong Ke Taman Laut Labuan dari 2000-2017](https://archive.data.gov.my/data/ms_MY/dataset/statistik-pelancong-ke-taman-laut-labuan-dari-2000-2017) |
| Pahang | [Statistik Pelancong Ke Taman Laut Pahang dari 2000-2017](https://archive.data.gov.my/data/ms_MY/dataset/statistik-pelancong-ke-taman-laut-pahang-dari-2000-2017) |
| Terengganu | [Statistik Pelancong Ke Taman Laut Terengganu dari 2000-2017](https://archive.data.gov.my/data/ms_MY/dataset/statistik-pelancong-ke-taman-laut-terengganu-dari-2000-2017) |

Local copy: `data/raw/structured/taman_laut_visitors_2000_2017.csv` (5 states × 18 years = 90 rows). All 90 rows were checked against the published CSVs on 15 September 2026 with no mismatches.

**Sabah** — Sabah Parks public visitor statistics, full-year 2024 totals with a Malaysian/international split (read 15 September 2026):

| Park | Dashboard page |
|---|---|
| Tunku Abdul Rahman Park | [dashboard.sabahparks.org.my/dashboard/tunku-abdul-rahman-park](https://dashboard.sabahparks.org.my/dashboard/tunku-abdul-rahman-park) |
| Tun Sakaran Marine Park | [dashboard.sabahparks.org.my/dashboard/tun-sakaran-marine-park](https://dashboard.sabahparks.org.my/dashboard/tun-sakaran-marine-park) |
| Sipadan Island Park | [dashboard.sabahparks.org.my/dashboard/sipadan-island-park](https://dashboard.sabahparks.org.my/dashboard/sipadan-island-park) |
| Turtle Islands Park | [dashboard.sabahparks.org.my/dashboard/turtle-islands-park](https://dashboard.sabahparks.org.my/dashboard/turtle-islands-park) |
| Pulau Tiga Park | [dashboard.sabahparks.org.my/dashboard/pulau-tiga-park](https://dashboard.sabahparks.org.my/dashboard/pulau-tiga-park) |

Local copy: the Sabah Parks rows of `data/raw/structured/tourism/island_arrivals.csv`.

### Other inputs

| Input | Value | Source |
|---|---|---|
| Spending per visitor | RM410.23 | DOSM, [Domestic Tourism Survey 2024](https://www.dosm.gov.my/portal-main/release-content/domestic-tourism-survey-2024): RM106.7 billion total domestic tourism expenditure ÷ 260.1 million domestic visitors |
| Share of spending attributable to reefs | 10% | Spalding, M. et al. (2017), [*Mapping the global value and distribution of coral reef tourism*](https://www.nature.org/content/dam/tnc/nature/en/documents/paper_coralreeftourism_spalding_2017.pdf), *Marine Policy* 82: 104–113 |
| Reef recovery period | 10–15 years | James Cook University (2019), [*How long does it take coral reefs to recover from bleaching?*](https://www.jcu.edu.au/news/releases/2019/february/how-long-does-it-take-coral-reefs-to-recover-from-bleaching) |
| High-priority units | 10 of 40 | ReefSafe model ranking, `data/processed/reef_priority_predictions.csv` (top quarter by predicted coral-cover decline) |

Spalding et al. and James Cook University are foreign sources. They supply a method coefficient and a recovery period that support a statement; every number they are applied to is Malaysian.

## Card 1: Reef-adjacent economy

### Step 1 — Visitors per park

**Department of Marine Park parks:** the average of 2013–2017, the last five published years, using only years with a recorded total.

| Park (state) | 2013 | 2014 | 2015 | 2016 | 2017 | Visitors a year |
|---|---|---|---|---|---|---|
| Terengganu Marine Parks (Terengganu) | 235,876 | 262,094 | 244,762 | 270,947 | 362,794 | **275,295** |
| Mersing Marine Parks (Johor) | 185,541 | 235,510 | 234,748 | 215,921 | 171,950 | **208,734** |
| Tioman Marine Parks (Pahang) | 232,102 | 240,657 | 231,238 | 249,300 | 90,180 | **208,695** |
| Pulau Payar Marine Park (Kedah) | 139,840 | 122,875 | 111,750 | 125,432 | 110,723 | **122,124** |
| Labuan Marine Park (Labuan) | 0 | 0 | 0 | 1,191 | 1,192 | **1,192** |

Labuan's zeros for 2013–2015 are treated as unrecorded years, so its figure is the 2016–2017 average.

**Sabah Parks parks:** the 2024 full-year total, Malaysian plus international visitors.

| Park | Malaysian | International | Visitors a year |
|---|---|---|---|
| Tunku Abdul Rahman Park | 371,069 | 126,130 | **497,199** |
| Tun Sakaran Marine Park | 74,467 | 25,902 | **100,369** |
| Sipadan Island Park | 32,349 | 4,370 | **36,719** |
| Turtle Islands Park | 9,205 | 1,128 | **10,333** |
| Pulau Tiga Park | 3,369 | 741 | **4,110** |

### Step 2 — Spending

```
spending per visitor = RM106,700,000,000 ÷ 260,100,000 = RM410.23
park spending        = visitors a year × RM410.23
```

### Step 3 — Reef-adjacent value

```
reef-adjacent value = park spending × 10%
```

### Step 4 — National estimate

The sum of the 10 parks.

| Park | Visitors a year | Spending | Reef-adjacent |
|---|---|---|---|
| Tunku Abdul Rahman Park | 497,199 | RM203.96M | RM20.40M |
| Terengganu Marine Parks | 275,295 | RM112.93M | RM11.29M |
| Mersing Marine Parks | 208,734 | RM85.63M | RM8.56M |
| Tioman Marine Parks | 208,695 | RM85.61M | RM8.56M |
| Pulau Payar Marine Park | 122,124 | RM50.10M | RM5.01M |
| Tun Sakaran Marine Park | 100,369 | RM41.17M | RM4.12M |
| Sipadan Island Park | 36,719 | RM15.06M | RM1.51M |
| Turtle Islands Park | 10,333 | RM4.24M | RM0.42M |
| Pulau Tiga Park | 4,110 | RM1.69M | RM0.17M |
| Labuan Marine Park | 1,192 | RM0.49M | RM0.05M |
| **Total** | **1,464,770** | **RM600.89M** | **RM60.09M** |

### Coverage

The 10 parks contain **30 of the 40** ranked monitoring units. The other 10 have no published park-level visitor count and are left out rather than estimated: **Malacca**, Port Dickson, Lahad Datu, Mantanani, Mataking, Kapalai, Mabul, Lankayan, Tun Mustapha Park and Usukan Cove.

## Card 2: Season rest vs long-term reef revenue

### Which parks

The parks that contain at least one high-priority unit:

| Park | High-priority units inside it |
|---|---|
| Terengganu Marine Parks | Kapas, Tenggol |
| Mersing Marine Parks | Lima, Mensirip, Mertang, Sibu, Tinggi |
| Tioman Marine Parks | Seri Buat |
| Labuan Marine Park | Labuan |

Together they hold **9 of the 10** high-priority units. Lankayan is not covered: its conservation area (SIMCA) has no published visitor count.

### Short term: one month of rest

```
combined park spending = RM112.93M + RM85.63M + RM85.61M + RM0.49M = RM284.66M a year
one month of rest      = RM284.66M ÷ 12 = RM23.72M
```

### Long term: reef revenue over the recovery period

```
reef-adjacent value of the four parks = RM284.66M × 10% = RM28.47M a year
over 10 years = RM284.66M
over 15 years = RM426.99M
```

### Chart

Three figures sit above three horizontal bars on one axis (RM millions, gridlines every 50): one month of rest (RM23.72M, red), reef revenue over 10 years (RM284.66M, green) and over 15 years (RM426.99M, green). The long-term figures are undiscounted.

### Important: the ratio is fixed by the assumptions

Both sides are built from the same spending, so the ratio between them does not depend on the data:

```
long term ÷ short term = 10% × 12 months × recovery years = 12× (10 years) to 18× (15 years)
```

The visitor numbers only set the ringgit scale. The card says so, and the ratio is not presented as a finding.

## Card 3: Reef-Adjacent Economy Potential

A donut of the Department of Marine Park Malaysia's published Total Economic Value for six marine-park archipelagos (studies 2011–2015), headline RM8.7 billion a year.

| Component | RM a year | Share of component sum | Source page |
|---|---|---|---|
| Aesthetic value | 8,000,000,000 | 92.09% | 9 |
| Fisheries | 580,400,000 | 6.68% | 6 |
| Coastal protection | 56,250,000 | 0.65% | 11 |
| Carbon sequestration | 30,240,000 | 0.35% | 12 |
| Bequest value | 14,500,000 | 0.17% | 13 |
| Tourism | 4,600,000 | 0.05% | 7 |
| Biological support | 1,000,000 | 0.01% | 10 |
| **Sum** | **8,686,990,000** | 100% | (published total rounded to RM8.7 billion) |

**Display rule:** components under 1.5% are drawn as 1.5% slices so all seven stay visible; aesthetic value and fisheries share the rest of the ring in proportion. The legend and hover text show the true values and shares.

**Limit:** a 2011–2015 valuation, largely willingness-to-pay; not current revenue or visitor spending, and not the Spalding 10% reef-adjacent estimate used in Card 1.

**Source:** Department of Marine Park Malaysia, [Total Economic Value of Marine Biodiversity](https://wdpa.s3.amazonaws.com/Country_informations/MYS/TOTAL%20ECONOMIC%20VALUE%20OF%20MARINE%20BIODIVERSITY.pdf).

## Assumptions and limitations

| Assumption | Limitation |
|---|---|
| 2013–2017 visitor levels stand in for today in peninsular parks | The Department of Marine Park series ends in 2017. Pahang's 2017 figure (90,180, down from 249,300 in 2016) may be a partial year. |
| Every visitor spends the national domestic average (RM410.23) | It is a per-trip average across all domestic trips, including day trips. Overnight island visitors and foreign visitors usually spend more, so spending is a floor. |
| 10% of spending is attributable to reefs | A single global coefficient from Spalding et al., not estimated for Malaysia. |
| Official park counts capture reef tourism | Non-park reefs (Mabul, Kapalai, Semporna, Port Dickson and others) and Malacca are excluded, so the national figure is a floor. |
| A park's visitors stand in for its high-priority units | Resting a whole park because one unit is flagged is a simplification; e.g. all of Tioman's visitors count because Seri Buat is flagged. |
| Rested-month visitors are lost | Visitors may return later or go elsewhere. The card does not model how coral responds to a rest. |
| Reef-adjacent value is an annual flow | It is not an asset value and not a forecast of losses from coral decline. |

## What we changed along the way

1. **Replaced unsourced figures.** The earlier dashboard showed RM842.5M "assets at risk", a 78/22 "reef-adjacent vs dive fees" split and a RM350,000 trust-fund allocation with no source. All were removed.
2. **Dropped the accommodation-based estimates.** An early version filled missing islands with a capacity ceiling from room counts. The room counts have no verifiable source, so they are no longer used anywhere.
3. **Recovered the 2010–2017 visitor data.** These rows had been marked unverified. They match the five Department of Marine Park datasets exactly and are now registered as verified.
4. **Moved from island level to park level.** Visitor counts are published per park, not per island, so both cards now work at park level. This also removed an annualisation error: Terengganu's January–August figures had been scaled up by 12/8, even though resorts close from October to February.
5. **Excluded Malacca.** There is no published visitor count for its islands (its marine park was only gazetted in 2023).
6. **Averaged only recorded years for Labuan,** instead of counting 2013–2015 as zero visitors.
7. **Stated the ratio honestly.** The earlier "12–18× larger" badge was removed after we found the ratio is fixed by the assumptions.
8. **Standardised park names** to official names in Title Case.

## Reproduce

```bash
python -m scripts.tourism_economics
python -m scripts.build_web_dashboard_data
python -m unittest tests.test_tourism_economics
```

| File | Role |
|---|---|
| `scripts/tourism_economics.py` | All calculations above, with the inputs as named constants |
| `data/processed/park_economics.csv` | One row per park: visitors, spending, reef-adjacent value, year basis, units inside |
| `data/processed/tourism_economics.json` | National totals, coverage, and the season-rest figures |
| `data/provenance_manifest.csv` | Source register, including every dataset above |
| `tests/test_tourism_economics.py` | Checks the 10% relationship, the 2013–2017 averages, Malacca's exclusion and the season-rest coverage |
