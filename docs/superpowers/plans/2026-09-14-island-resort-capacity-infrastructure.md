# Implementation Plan: Island Resort & Accommodation Capacity Infrastructure (Alternative 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish an audited, publicly verifiable island accommodation and built-infrastructure dataset across all 56 monitored islands to serve as an empirical proxy for physical tourist carrying capacity, integrating it into the data pipeline, tests, and interactive dashboard without fabricating non-existent visitor counts.

**Architecture:** Create an audited static infrastructure CSV (`data/raw/structured/infrastructure/island_accommodations.csv`) referencing MOTAC and OSM registries. Integrate this into the preprocessing pipeline (`scripts/run_preprocessing.py`), bundle it into `dashboard/data.js`, and display island-level capacity metrics and policy levers in Tab 2 (Diagnostics) and Tab 3 (Policy Simulator).

**Tech Stack:** Python 3.11, Polars, Vanilla HTML5/CSS3/JS, unittest.

**Spec Reference:** Alternative 1 (Built-environment capacity proxy from MOTAC/OSM/Tourism Registries).

---

## Global Constraints

- **No Fictional Daily Numbers:** Never multiply room counts by arbitrary multipliers to claim "observed daily visitors". Room and resort counts must be labeled as *physical capacity ceilings*.
- **Full 56-Island Coverage:** Every island in `island_coordinates.csv` must have an explicit accommodation entry (even if 0, like Pulau Sipadan or uninhabited marine sanctuaries).
- **Test Integrity:** Every pipeline change must pass `python -m unittest discover tests`.
- **Minimalist Institutional Design:** Maintain OpenDOSM design standards (no consumer emojis, high data-to-ink ratio).

---

## User Review Required

> [!IMPORTANT]
> **Data Methodology:** This feature uses *physical room and resort counts* as the upper bound of human overnight capacity on each island. Uninhabited or restricted islands (e.g. Sipadan, Pulau Lima, Pulau Yu) will explicitly be recorded as 0 rooms / 0 resorts, which accurately reflects their conservation status.

---

## Proposed Changes

### Component 1: Ground-Truth Infrastructure Dataset

#### [NEW] [island_accommodations.csv](file:///c:/Users/Chee/Documents/dosm2026/data/raw/structured/infrastructure/island_accommodations.csv)
- Create structured CSV with 56 rows matching monitored islands in `island_coordinates.csv`.
- Columns:
  - `island`: Normalized island name matching Reef Check panel.
  - `state`: Malaysian state.
  - `resort_count`: Verified count of operating resorts, hotels, and chalets.
  - `estimated_room_capacity`: Total guest room inventory.
  - `dive_center_count`: Number of registered dive operators on island.
  - `has_commercial_jetty`: Binary flag (1 = dedicated concrete jetty; 0 = beach landing/boat only).
  - `data_source`: Audit reference (e.g., MOTAC Tourism Registry, State Parks, OpenStreetMap).

---

### Component 2: Pipeline Integration & Verification

#### [MODIFY] [run_preprocessing.py](file:///c:/Users/Chee/Documents/dosm2026/scripts/run_preprocessing.py)
- Load `island_accommodations.csv`.
- Join accommodation fields with `df_rc` and `df_geo`.
- Ensure zero nulls across all 56 islands (default 0 for uninhabited nature reserves).
- Export updated `master_reef_tourism_dataset.csv`.

#### [MODIFY] [build_web_dashboard_data.py](file:///c:/Users/Chee/Documents/dosm2026/scripts/build_web_dashboard_data.py)
- Include `resort_count`, `room_capacity`, `dive_centers`, and `has_jetty` in the priority island dictionary export inside `dashboard/data.js`.

#### [NEW] [test_infrastructure_data.py](file:///c:/Users/Chee/Documents/dosm2026/tests/test_infrastructure_data.py)
- Unit tests verifying:
  - All 56 monitored islands exist in `island_accommodations.csv`.
  - Room counts and resort counts are non-negative integers.
  - Known reference islands have verified ground truth (e.g. Sipadan = 0 rooms, Redang > 500 rooms).

---

### Component 3: Dashboard UI & Policy Simulator Integration

#### [MODIFY] [dashboard/index.html](file:///c:/Users/Chee/Documents/dosm2026/dashboard/index.html)
- **Tab 2 (Island Diagnostics):** Add a compact "Physical Carrying Capacity & Built Infrastructure" card beside the Ecological Diagnostic card.
- **Tab 3 (Policy Simulator):** Add an "Accommodations & Development Cap" interactive slider (e.g. freezing new resort approvals or setting room occupancy limits) that modifies simulated human disturbance pressure.

#### [MODIFY] [dashboard/app.js](file:///c:/Users/Chee/Documents/dosm2026/dashboard/app.js)
- Wire island selection in Tab 2 to dynamically populate the accommodation metrics (`resort_count`, `estimated_room_capacity`, `dive_center_count`, `has_commercial_jetty`).
- Update Policy Simulator calculations to include the accommodation constraint factor.

#### [MODIFY] [docs/assumptions.md](file:///c:/Users/Chee/Documents/dosm2026/docs/assumptions.md)
- Add a new row to the assumption register detailing the role of static room capacity as a verifiable proxy for overnight tourist pressure ceiling.

---

## Verification Plan

### Automated Tests
1. Run newly created unit test:
   ```powershell
   python -m unittest tests.test_infrastructure_data
   ```
2. Run full regression test suite:
   ```powershell
   python -m unittest discover tests
   ```

### Manual Verification
1. Re-generate data bundle:
   ```powershell
   python -m scripts.run_preprocessing
   python -m scripts.build_web_dashboard_data
   ```
2. Open browser test via `browser_subagent` at `http://localhost:8088/`:
   - Verify Tab 2 (Island Diagnostics) displays accurate room and resort metrics when selecting Pulau Redang, Pulau Tioman, and Pulau Sipadan.
   - Verify Tab 3 (Policy Simulator) adjusts simulated outcome when sliding the accommodation cap.
   - Verify 0 console errors in browser.
