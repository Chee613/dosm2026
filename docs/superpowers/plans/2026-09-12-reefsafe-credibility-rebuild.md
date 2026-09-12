# ReefSafe Credibility Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a consistent, authentic, interactive ReefSafe AI competition submission.

**Architecture:** Preprocessing writes one audited panel; modelling writes one set of metrics, predictions, and figures; dashboard and report only consume those outputs. Unsupported precision is removed.

**Tech Stack:** Python, standard library, Polars, scikit-learn, Matplotlib, python-docx, `@oai/artifact-tool`.

**Spec:** `docs/superpowers/specs/2026-09-12-reefsafe-credibility-rebuild-design.md`

## Global Constraints

- No fabricated, simulated, or fictional source data.
- Use past-only predictors for forward evaluation.
- Use association language unless a causal design exists.
- Keep the dashboard usable in ordinary Excel without macros.
- Do not report unsupported visitor caps or monetary impact.

---

### Task 1: Data integrity

**Files:**
- Modify: `scripts/run_preprocessing.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `parse_noaa_row(parts) -> dict`, `build_tourism_features(...)`, and `data/processed/master_reef_tourism_dataset.csv`.

- [ ] Write a test asserting DHW comes from the `DHW_from_90th_HS>1` column and generated tourism proxies are absent.
- [ ] Run `python -m unittest tests.test_pipeline.PipelineTests` and verify the assertion fails.
- [ ] Extract the NOAA parser, correct the index, and remove the multiplier-based tourism fields.
- [ ] Rerun the test and preprocessing.

### Task 2: Past-only model

**Files:**
- Modify: `scripts/train_models.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `master_reef_tourism_dataset.csv`.
- Produces: `model_evaluation_metrics.csv`, `model_evaluation_metrics.json`, `reef_priority_predictions.csv`, and three figures.

- [ ] Add a failing test showing each feature row precedes its target observation.
- [ ] Implement `make_next_observation_dataset(rows)` and expanding-year validation with an imputation pipeline.
- [ ] Save baseline and candidate metrics together and generate honest association/error figures.
- [ ] Run the tests and training command.

### Task 3: Interactive dashboard

**Files:**
- Replace: `src/build_dashboard.py`
- Create: `src/build_dashboard.mjs`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: processed panel, predictions, and metrics.
- Produces: `dist/dashboard_package/Dashboard.xlsx`, `Dashboard.pdf`, `Data.csv`, `README.txt`, and the submission ZIP.

- [ ] Add a failing structural test requiring formulas, validation, and charts in the workbook.
- [ ] Build an Excel dashboard with an island selector, linked KPIs, coral history, risk evidence, and an intervention lookup.
- [ ] Export, recalculate, inspect formulas/errors, render both sheets, and rerun the structural test.

### Task 4: Submission consistency

**Files:**
- Modify: `src/generate_report.py`
- Modify: `output/VIDEO_PRESENTATION_SCRIPT.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the same metrics, predictions, figures, and dashboard generated above.
- Produces: final DOCX/PDF report and an evidence-matched presentation script.

- [ ] Replace hardcoded findings and policy claims with generated values and explicit limitations.
- [ ] Correct the contents page and submission filenames.
- [ ] Regenerate the DOCX/PDF and inspect every rendered page.
- [ ] Execute the packaged notebook and run the complete test suite.
