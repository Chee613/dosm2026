# Data Provenance, Sources, and Acquisition Registry

This registry provides complete provenance, official source links, licensing, and methodological documentation for all raw datasets utilized in the **DOSM Datathon 2026** project (*ReefSafe AI: Leveraging Machine Learning for Sustainable Marine Tourism & Coral Resilience in Malaysia*).

---

## 1. Directory Structure

```text
dosm2026/
└── data/
    ├── raw/
    │   ├── structured/
    │   │   ├── reef_check/
    │   │   │   ├── ReefCheck_Malaysia_FINAL.xlsx  # 404 island-years, 56 islands, 2007-2025
    │   │   │   └── bleaching_2024.csv             # 2024 Mass Bleaching Event survey records
    │   │   ├── opendosm/
    │   │   │   ├── gdp_state_real_supply.json     # Official state GDP & tourism supply proxy
    │   │   │   ├── fish_landings.csv              # Annual marine fisheries landings by state
    │   │   │   └── water_pollution_basin.csv      # River basin water quality & pollution index
    │   │   ├── noaa_crw/
    │   │   │   ├── malacca_strait.txt             # Daily 5km SST & DHW (1985–2026)
    │   │   │   ├── sabah.txt                      # Daily 5km SST & DHW (1985–2026)
    │   │   │   ├── northern_borneo.txt            # Daily 5km SST & DHW (1985–2026)
    │   │   │   ├── singapore.txt                  # Daily 5km SST & DHW (1985–2026)
    │   │   │   └── west_gulf_of_thailand.txt      # Daily 5km SST & DHW (1985–2026)
    │   │   └── geocoding/
    │   │       └── island_coordinates.csv         # 56 islands JUPEM/WGS84 geocoded coordinates
    │   └── unstructured/
    │       ├── reef_check_reports/                # 19 Annual Survey Reports (2007–2025 PDFs)
    │       │   ├── 2007AnnualSurveyReport.pdf
    │       │   ├── ...
    │       │   └── 2025AnnualSurveyReport.pdf
    │       ├── extraction_docs/
    │       │   └── EXTRACTION_METHODOLOGY.md      # Methodological audit for data extraction
    │       └── competition_guidelines/
    │           └── DOSM-Datathon-2026-Booklet.pdf # Official DOSM Datathon 2026 Competition Guidelines
    └── processed/
        └── master_reef_tourism_dataset.csv        # Merged, feature-engineered, audited master dataset
```

---

## 2. Detailed Data Source Registry & Web Links

### A. Reef Check Malaysia (RCM) Ecological Survey Archive
* **Publisher:** Reef Check Malaysia (Non-Governmental Organization / Marine Conservation Partner)
* **Official Website:** [https://reefcheck.org.my](https://reefcheck.org.my)
* **Official Reports Portal:** [Reef Check Annual Survey Reports](https://reefcheck.org.my/annualsurveyreports/)
* **Survey Standard:** Global Reef Check Protocol (Standardized underwater transect survey: 4 segments x 20m per transect; substrate categories: Live Coral Cover [LCC], Dead Coral [DC], Soft Coral [SC], Algae, Rubble, Sand).
* **Coverage:** 2007 – 2025 (19 consecutive years, 56 distinct islands across 9 Malaysian states).
* **Direct Google Drive Archive Links:**
  * **19 Raw Annual Survey Report PDFs (2007–2025):** [Google Drive Folder (Subfolder: RC Annual Reports)](https://drive.google.com/drive/folders/1MxnPnzA5MNtvPdssqMfWQ2kqweeuqPfG)
  * **Consolidated Structured Panel (`ReefCheck_Malaysia_FINAL.xlsx`):** [Direct Download Link](https://drive.google.com/uc?export=download&id=1lwX6FiMeoo5FIq8cW7dwNqg_p26vZTEc)
  * **2024 Mass Bleaching Event Dataset (`bleaching_2024.csv`):** [Direct Download Link](https://drive.google.com/uc?export=download&id=1_gxTkwLHb240rbd15U5VMMdKNJ0KEvcs)
  * **Extraction & Harmonization Protocol (`EXTRACTION_METHODOLOGY.md`):** [Direct Download Link](https://drive.google.com/uc?export=download&id=1AX1QMpFJO_xoAyTaEVSthO6sH4gSORoO)

---

### B. OpenDOSM & data.gov.my Official Government Statistics
* **Publisher:** Department of Statistics Malaysia (DOSM) & Ministry of Economy / MAMPU
* **Official Portals:** 
  * OpenDOSM: [https://open.dosm.gov.my](https://open.dosm.gov.my)
  * data.gov.my Data Catalogue: [https://data.gov.my](https://data.gov.my)
* **Terms of Use:** Malaysian Government Open Data License (CC BY 4.0 equivalent).
* **Specific Endpoints:**
  1. **State GDP by Economic Activity (Real Supply & Tourism Proxies):**
     * *Catalogue ID:* `gdp_state_real_supply`
     * *Live API Query URL:* [https://api.data.gov.my/data-catalogue?id=gdp_state_real_supply](https://api.data.gov.my/data-catalogue?id=gdp_state_real_supply)
     * *Catalogue Page:* [https://data.gov.my/data-catalogue/gdp_state_real_supply](https://data.gov.my/data-catalogue/gdp_state_real_supply)
     * *Fields utilized:* State-level real GDP contribution from Accommodation & Food Services, Transportation, and Marine Park Support Services.
  2. **Marine Fish Landings by State:**
     * *Direct CSV URL:* [https://storage.data.gov.my/agriculture/fish_landings.csv](https://storage.data.gov.my/agriculture/fish_landings.csv)
     * *Catalogue Page:* [https://data.gov.my/data-catalogue/fish_landings](https://data.gov.my/data-catalogue/fish_landings)
     * *Fields utilized:* Annual marine fisheries landings (metric tonnes) by state, acting as an indicator of coastal resource extraction pressure.
  3. **River Basin Water Quality & Pollution:**
     * *Direct CSV URL:* [https://storage.data.gov.my/environment/water_pollution_basin.csv](https://storage.data.gov.my/environment/water_pollution_basin.csv)
     * *Catalogue Page:* [https://data.gov.my/data-catalogue/water_pollution_basin](https://data.gov.my/data-catalogue/water_pollution_basin)
     * *Fields utilized:* Biochemical Oxygen Demand (BOD), Ammoniacal Nitrogen (NH3-N), Suspended Solids (SS) runoff.
  4. **Domestic Tourism Survey (DTS) & Tourism Satellite Account (TSA):**
     * *Catalogue Page:* [https://open.dosm.gov.my/data-catalogue/dts_annual](https://open.dosm.gov.my/data-catalogue/dts_annual)
     * *Metrics:* State-level tourist arrivals, average stay duration, expenditure per visitor, and Marine Park Conservation Fee receipts.

---

### C. NOAA Coral Reef Watch (CRW) Satellite Bleaching Alert System
* **Publisher:** National Oceanic and Atmospheric Administration (NOAA), U.S. Department of Commerce (NESDIS / STAR)
* **Official Portal:** [NOAA Coral Reef Watch 5km Virtual Stations](https://coralreefwatch.noaa.gov/product/vs/data.php)
* **Product Version:** Operational Daily Global 5km Satellite Coral Bleaching Heat Stress Monitoring (Version 3.1)
* **Metrics Provided:** Daily Sea Surface Temperature (SST, °C), SST Anomaly (°C), Degree Heating Weeks (DHW, °C-weeks), Bleaching Alert Level (0: None, 1: Watch, 2: Warning, 3: Alert Level 1, 4: Alert Level 2).
* **Virtual Station Data URLs:**
  1. **Malacca Strait (West Coast Peninsular: Pulau Pangkor, Pulau Payar, Pulau Perak):**
     [https://coralreefwatch.noaa.gov/product/vs/data/malacca_strait.txt](https://coralreefwatch.noaa.gov/product/vs/data/malacca_strait.txt)
  2. **Sabah (East Malaysia: Sipadan, Mabul, Tunku Abdul Rahman Park, Kudat, Semporna):**
     [https://coralreefwatch.noaa.gov/product/vs/data/sabah.txt](https://coralreefwatch.noaa.gov/product/vs/data/sabah.txt)
  3. **Northern Borneo (Sarawak & Northern Sabah: Talang-Satang, Miri-Sibuti):**
     [https://coralreefwatch.noaa.gov/product/vs/data/northern_borneo.txt](https://coralreefwatch.noaa.gov/product/vs/data/northern_borneo.txt)
  4. **Singapore / Southern Sunda Shelf (Southern East Coast: Pulau Tioman, Pulau Aur, Pulau Pemanggil, Pulau Tinggi, Pulau Sibu):**
     [https://coralreefwatch.noaa.gov/product/vs/data/singapore.txt](https://coralreefwatch.noaa.gov/product/vs/data/singapore.txt)
  5. **West Gulf of Thailand / Northern Sunda Shelf (Northern East Coast: Pulau Redang, Pulau Perhentian, Pulau Lang Tengah, Pulau Bidong, Pulau Yu):**
     [https://coralreefwatch.noaa.gov/product/vs/data/west_gulf_of_thailand.txt](https://coralreefwatch.noaa.gov/product/vs/data/west_gulf_of_thailand.txt)

---

### D. Geographic Information & Marine Park Geocoding
* **Authorities:** Department of Survey and Mapping Malaysia (JUPEM) & Marine Park Section, Department of Fisheries Malaysia (DOFM)
* **Reference System:** WGS84 Geodetic Datum (EPSG:4326)
* **Local Dataset File:** `data/raw/structured/geocoding/island_coordinates.csv`
* **Contents:** Exact centroid coordinates (latitude, longitude) for all 56 survey islands, official administrative state, marine park gazettement year, and mapped NOAA CRW station ID.

---

### E. Marine Park Visitor Statistics & The National Tourism Data Gap
* **Publisher:** Jabatan Taman Laut Malaysia (JTLM) / Ministry of Natural Resources and Environment & MAMPU
* **Official Portal:** [data.gov.my Open Data Archive: Jumlah Pelawat Taman Laut Malaysia (2000–2009)](https://archive.data.gov.my/data/ms_MY/dataset/jumlah-pelawat-taman-laut-malaysia-dari-tahun-2000-hingga-2009-)
* **Local Files:**
  * `data/raw/structured/taman_laut_visitors_2000_2017.csv` (Extended 2000–2017 series by state)
  * `data/raw/structured/marine_park_visitors_tidy (1).csv` (2000–2009 tidy series)
* **Coverage & Structure:** Annual domestic and foreign visitor headcounts for gazetted marine parks across 5 states: Kedah, Terengganu, Pahang, Johor, and Federal Territory of Labuan.
* **The Tourism Data Gap Audit:**
  1. *Temporal Cessation:* Official open-data reporting abruptly ended in 2017. There is zero publicly published government visitor data for 2018–2025 (covering the crucial COVID-19 tourism pause and the 2024 mass bleaching event).
  2. *Spatial Exclusion:* Excludes Sabah and Sarawak completely (which contain over 40% of monitored reefs, governed separately by Sabah Parks and Sarawak Forestry Corporation).
  3. *Resolution Mismatch:* Aggregated at state marine park level rather than island-by-island, preventing direct site-level carrying capacity calculation without ground ticketing manifests.

---

### F. Audited Island Accommodations & Physical Carrying Capacity Ceiling
* **Publishers:** Ministry of Tourism, Arts and Culture (MOTAC), State Tourism Boards (Terengganu, Sabah, Johor), Tioman Development Authority (TDA), Municipal Councils, and OpenStreetMap.
* **Local Dataset File:** `data/raw/structured/infrastructure/island_accommodations.csv`
* **Coverage:** Complete, ground-truthed 56-island panel matching all surveyed Reef Check locations.
* **Metrics:** Operating resort count, total guest room capacity, registered dive center count, commercial jetty existence, and audit source trail.
* **Methodological Role:** Serves as the verifiable, physical upper-bound ceiling for human presence on each island, replacing non-existent daily footfall numbers.

---

### G. Multi-Pillar Economic Valuation & Natural Capital Accounting
* **Literature Sources:** UNEP Coral Reef Unit, World Bank Marine Protected Area Valuation, Reef Check Malaysia Economic Reports, and Department of Statistics Malaysia (DOSM) Tourism Satellite Accounts.
* **Engine Script:** `scripts/economic_valuation.py`
* **Benchmark Total:** **RM 8.70 Billion / Year** across 4 pillars:
  1. *Marine Tourism & Recreation:* RM 4.80 Billion (55.2%) — Accommodation, dive concessions, rentals, boat charters.
  2. *Coastal Protection & Shoreline Buffering:* RM 2.30 Billion (26.4%) — Wave attenuation and erosion prevention.
  3. *Fisheries Nursery & Commercial Landings:* RM 1.10 Billion (12.6%) — Spawning biomass export supporting coastal food security.
  4. *Carbon Sequestration & Non-Use Biodiversity:* RM 0.50 Billion (5.8%) — Blue carbon and conservation option value.
* **NPV Simulation:** 20-year net present value simulation proving that temporary seasonal capacity controls preserve >RM 25 Billion in natural capital asset value over business-as-usual degradation.
