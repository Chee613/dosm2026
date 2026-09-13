# Reef Watch Malaysia dashboard

An interactive map of surveyed Malaysian islands, coloured by how urgently action is needed to protect their coral. Below it are Gemini-generated insights and actions for marine park authorities and tourism operators, followed by the EDA charts.

## Run it

From the project root (`D:\Projects\DOSM`):

```bash
pip install -r dashboard/requirements.txt
python dashboard/prepare_data.py          # builds dashboard/data/ (about 40 s)
streamlit run dashboard/app.py
```

## Gemini insights

1. Get an API key from Google AI Studio. Copy `.env.example` (project root) to `.env` and replace the placeholder with your key. Alternatively, set `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) as an environment variable, which takes priority over `.env`. The key is read only by the Gemini SDK and is never printed. `.env` is listed in `.gitignore`; never share it.
2. Generate insights for all 40 current islands plus the Malaysia-wide overview:

   ```bash
   python dashboard/generate_insights.py
   ```

   Other options: `--islands Redang Tioman` (only those islands), `--scenario "2025 observed"`, `--no-overview`. Set `GEMINI_MODEL` to change the model (default `gemini-3.1-flash-lite`).
3. The app picks up `dashboard/data/insights.json` automatically. With the key set in the shell that runs Streamlit, the **Regenerate** buttons refresh the selected island (plus the overview), or all islands, for the current scenario and thresholds.

**Free-tier limits.** Gemini's free tier allows about 5 requests per minute, so the script:
- sends islands in batches of 5 (`GEMINI_BATCH`): 8 requests plus 1 for the overview
- spaces requests to 5 per minute (`GEMINI_RPM`; raise it on a paid plan)
- waits as long as the API asks after a rate-limit error
- saves after every batch

A full run takes about 2 minutes. Rerunning skips islands that are already up to date, so an interrupted run resumes; add `--force` to regenerate everything. If the *daily* quota is used up, it stops at once, and you can rerun tomorrow.

Insights are merged, so regenerating one island keeps the rest. Each insight stores a hash of the data it was generated from. When the scenario, thresholds or data change, the app flags it as possibly outdated.

## How urgency is decided

| Colour | Rule (defaults, editable in the sidebar) |
|---|---|
| 🔴 Act now | projected cover < 25% (Reef Check "poor"), **or** forecast decline ≤ −2 pts under severe heat (≥ 8 DHW) |
| 🟡 Watch closely | projected cover 25–50% ("fair") |
| 🟢 Healthy | projected cover ≥ 50% ("good") with no severe heat-driven decline |
| ⚪ Data too old | last survey before 2025; not forecast |

- **Projected cover** = latest cover + the forecast change at the next survey.
- **The forecast** is the saved model (`models/lcc_forecast_model.joblib`, weighted Lasso). The app recomputes it from the model's exported coefficients, so the heat slider responds instantly. `prepare_data.py` checks that this matches `model.predict` exactly.
- **Heat stress** is the peak degree-heating weeks in the year before the next survey, per NOAA station. Choose 2026 to date (default), 2025 observed, or custom per-station values.
- **Small forecast changes are ignored for green reefs.** On healthy reefs they mostly reflect reefs drifting toward their regional average, so they don't trigger yellow.

## Files

| File | Role |
|---|---|
| `prepare_data.py` | Builds `data/`: island table, model coefficients, NOAA station heat and the EDA aggregates (same seeds and results as `eda.ipynb`) |
| `logic.py` | Forecast and urgency rules shared by all scripts |
| `schemas.py` | JSON contract for Gemini output (Pydantic) |
| `generate_insights.py` | Builds data payloads, calls Gemini with structured JSON output, validates, retries and writes `data/insights.json` |
| `app.py` | Streamlit app |
| `tests/test_generate_insights.py` | Tests with a fake Gemini client: `python -m unittest discover -s dashboard/tests` |

## Caveats

- The forecast's typical error is about ±6 points, and it beats predicting the average by about 4%.
- Tourism and development intensity aren't in the data; the boat-pressure index (share of 2015–2019 surveys reporting anchor damage) is a stand-in.
- All results are associations from observational surveys, not proven causes. LLM insights are grounded in the data shown, but should be checked in the field.
