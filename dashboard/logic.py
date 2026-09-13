"""Forecast and urgency rules shared by prepare_data.py, generate_insights.py and app.py."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / 'data'
STATIONS = ['sabah', 'singapore', 'malacca_strait', 'northern_borneo']
STATION_LABEL = {'sabah': 'Sabah', 'singapore': 'Singapore Strait', 'malacca_strait': 'Malacca Strait',
                 'northern_borneo': 'Northern Borneo'}
# Reef Check health bands (live coral cover) and the severe-heat trigger
DEFAULT_THRESHOLDS = {'poor': 25.0, 'good': 50.0, 'severe_dhw': 8.0, 'severe_decline': -2.0}
SCENARIOS = ['2026 to date', '2025 observed', 'Custom']


def load_model_spec(path=DATA_DIR / 'model_spec.json'):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def forecast(islands: pd.DataFrame, spec: dict, heat: pd.Series) -> pd.Series:
    """Forecast next-survey change: the saved Lasso, recomputed from its exported coefficients.

    `heat` is the previous-year peak DHW per island (the scenario). Missing inputs take the
    training median, exactly as the model's imputer does.
    """
    pred = pd.Series(spec['intercept'], index=islands.index, dtype=float)
    for f in spec['features']:
        x = heat if f['name'] == 'dhw_peak_prev_year' else islands[f['input_column']]
        x = x.astype(float).fillna(f['impute_median'])
        pred += f['coef_per_sd'] * (x - f['mean']) / f['scale']
    return pred


def scenario_heat(islands: pd.DataFrame, scenario: str, custom: dict | None = None) -> pd.Series:
    if scenario == '2025 observed':
        by_station = islands['dhw_2025']
    elif scenario == 'Custom':
        by_station = islands['noaa_station_id'].map(custom)
    else:
        by_station = islands['dhw_2026']
    return by_station.astype(float)


def urgency(cover: float, change: float, dhw: float, th: dict = DEFAULT_THRESHOLDS) -> tuple[str, str]:
    """Return (level, reason) for one island; level is red / yellow / green."""
    projected = cover + change
    if projected < th['poor']:
        return 'red', f'projected cover {projected:.0f}% is in the poor band (< {th["poor"]:.0f}%)'
    if change <= th['severe_decline'] and dhw >= th['severe_dhw']:
        return 'red', f'forecast decline {change:+.1f} pts under severe heat ({dhw:.1f} DHW ≥ {th["severe_dhw"]:.0f})'
    if projected < th['good']:
        return 'yellow', f'projected cover {projected:.0f}% is in the fair band ({th["poor"]:.0f}–{th["good"]:.0f}%)'
    # Small forecast declines on healthy reefs are mostly the model's pull toward the regional average,
    # not a threat signal, so they don't trigger yellow; heat-driven declines are handled by the red rule.
    return 'green', f'projected cover {projected:.0f}% is in the good band (≥ {th["good"]:.0f}%), no severe heat-driven decline'


def score_islands(islands: pd.DataFrame, spec: dict, scenario: str = '2026 to date',
                  custom: dict | None = None, th: dict = DEFAULT_THRESHOLDS) -> pd.DataFrame:
    """Add heat, forecast, projected cover and urgency columns; stale islands are grey."""
    out = islands.copy()
    out['heat_dhw'] = scenario_heat(out, scenario, custom)
    out['forecast_change'] = forecast(out, spec, out['heat_dhw'])
    out['projected_cover'] = out['cover'] + out['forecast_change']
    levels = [urgency(r.cover, r.forecast_change, r.heat_dhw, th) if not r.stale
              else ('grey', f'last surveyed {r.last_survey_year}: data too old to forecast')
              for r in out.itertuples()]
    out['urgency'] = [lvl for lvl, _ in levels]
    out['urgency_reason'] = [why for _, why in levels]
    out.loc[out['stale'], ['forecast_change', 'projected_cover']] = np.nan
    return out
