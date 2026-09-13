"""Build everything the dashboard reads into dashboard/data/.

Run from the project root:  python dashboard/prepare_data.py

Outputs
  model_spec.json        the saved Lasso's active coefficients + scaling (lets the app recompute forecasts)
  islands.csv            one row per island: latest survey, heat, pressures, EDA site type, forecast inputs
  station_heat.csv       annual peak DHW per NOAA station, 2010-2026
  eda_*.csv              aggregates behind the EDA charts (ported from eda.ipynb, same seeds and results)
  meta.json              data dates, defaults and chart takeaways
"""
import json
import sys
from datetime import datetime
from itertools import combinations
from math import factorial
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from logic import DATA_DIR, DEFAULT_THRESHOLDS, STATIONS, score_islands  # noqa: E402

SEED, N_BOOT, HEAT_DHW = 42, 1000, 4.0
YEARS = (2015, 2025)
CURRENT_YEAR = 2025          # islands whose latest survey is older are "stale"
REGION = {'Johor': 'Peninsular east', 'Pahang': 'Peninsular east', 'Terengganu': 'Peninsular east',
          'Kedah': 'Peninsular west', 'Perak': 'Peninsular west', 'Malacca': 'Peninsular west',
          'Negeri Sembilan': 'Peninsular west', 'Sabah': 'Sabah', 'Sarawak': 'Sarawak'}
GRP = ['grp_other', 'grp_available_substrate', 'grp_sand', 'grp_disturbance_indicators', 'grp_pollution_indicators']
# model input  <-  column of the island's latest survey (that survey is the "previous survey" for the forecast)
FORECAST_INPUTS = {'lcc_prev': 'cover', 'prev_island_vs_region_pct': 'vs_region', 'prev_lcc_change': 'last_change',
                   'prev_n_curio_inverts_absent': 'curio_absent', 'n_sites': 'n_sites',
                   'prev_fish_sweetlips': 'sweetlips', 'dhw_peak_prev_year': None}


# ----------------------------------------------------------------------------- helpers
def read_station(station):
    path = ROOT / 'data' / 'raw' / 'structured' / 'noaa_crw' / f'{station}.txt'
    lines = path.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith('YYYY'))
    cols = ['y', 'm', 'd', 'sst_min', 'sst_max', 'sst90', 'ssta90', 'hs90', 'dhw', 'baa']
    return pd.read_csv(path, sep=r'\s+', skiprows=start + 1, names=cols)


def boot_mean(g, col, n_boot=N_BOOT, seed=SEED):
    """Island-bootstrap 95% interval of a mean (same draws as eda.ipynb's island_boot)."""
    agg = g.groupby('island')[col].agg(['sum', 'count'])
    names = agg.index.to_numpy()
    rng = np.random.default_rng(seed)
    pos = {n: i for i, n in enumerate(names)}
    sums, counts = agg['sum'].to_numpy(), agg['count'].to_numpy()
    vals = []
    for _ in range(n_boot):
        idx = [pos[n] for n in rng.choice(names, len(names))]
        c = counts[idx].sum()
        vals.append(sums[idx].sum() / c if c else np.nan)
    return np.nanpercentile(vals, [2.5, 97.5])


def mean_ci(df, col, by):
    rows = []
    for key, g in df.groupby(by, observed=True):
        lo, hi = boot_mean(g, col)
        rows.append({'group': key, 'n': len(g), 'islands': g['island'].nunique(),
                     'mean': g[col].mean(), 'ci_low': lo, 'ci_high': hi})
    return pd.DataFrame(rows)


def island_boot(df, stat, n_boot=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    groups = {i: g for i, g in df.groupby('island')}
    names = list(groups)
    vals = [stat(pd.concat([groups[i] for i in rng.choice(names, len(names))], ignore_index=True))
            for _ in range(n_boot)]
    return np.nanpercentile(vals, [2.5, 97.5])


def r2(X, y):
    if X.shape[1] == 0:
        return 0.0
    X1 = np.column_stack([np.ones(len(y)), X])
    res = y - X1 @ np.linalg.lstsq(X1, y, rcond=None)[0]
    return 1 - res @ res / ((y - y.mean()) @ (y - y.mean()))


def shapley(blocks, y):
    names, B, cache = list(blocks), len(blocks), {}

    def R(S):
        key = frozenset(S)
        if key not in cache:
            cache[key] = r2(np.column_stack([blocks[n] for n in S]) if S else np.empty((len(y), 0)), y)
        return cache[key]

    out = {j: sum(factorial(k) * factorial(B - k - 1) / factorial(B) * (R(S + (j,)) - R(S))
                  for k in range(B) for S in combinations([n for n in names if n != j], k))
           for j in names}
    return out, R(tuple(names))


def decompose(df, blocks, target):
    cols = [c for cs in blocks.values() for c in cs]
    d = df.dropna(subset=cols + [target]).reset_index(drop=True)
    y = d[target].to_numpy(float)
    arrays = {n: d[cs].to_numpy(float) for n, cs in blocks.items()}
    shares, total = shapley(arrays, y)
    rng = np.random.default_rng(SEED)
    rows_of = {i: np.flatnonzero(d['island'].to_numpy() == i) for i in d['island'].unique()}
    boot = pd.DataFrame([shapley({n: a[idx] for n, a in arrays.items()}, y[idx])[0] for idx in
                         (np.concatenate([rows_of[i] for i in rng.choice(list(rows_of), len(rows_of))]) for _ in range(N_BOOT))])
    null = [shapley({**arrays, 'Local pressures': arrays['Local pressures'][rng.permutation(len(y))]}, y)[0]['Local pressures']
            for _ in range(500)]
    table = pd.DataFrame({'share': shares, 'ci_low': boot.quantile(0.025), 'ci_high': boot.quantile(0.975)})
    return table, total, float(np.percentile(null, 95)), float(np.mean(np.array(null) >= shares['Local pressures'])), d


def coefs(d, blocks, target):
    cols = [c for cs in blocks.values() for c in cs]
    X, y = d[cols].to_numpy(float), d[target].to_numpy(float)
    fit = lambda X, y: np.linalg.lstsq(np.column_stack([np.ones(len(y)), X]), y, rcond=None)[0][1:]
    b = fit(X, y)
    rng = np.random.default_rng(SEED)
    rows_of = {i: np.flatnonzero(d['island'].to_numpy() == i) for i in d['island'].unique()}
    boot = np.array([fit(X[idx], y[idx]) for idx in
                     (np.concatenate([rows_of[i] for i in rng.choice(list(rows_of), len(rows_of))]) for _ in range(N_BOOT))])
    return pd.DataFrame({'coef': b, 'ci_low': np.percentile(boot, 2.5, axis=0),
                         'ci_high': np.percentile(boot, 97.5, axis=0)}, index=cols)


# ----------------------------------------------------------------------------- main
def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(ROOT / 'master_reef_tourism_dataset.csv').sort_values(['island', 'survey_year']).reset_index(drop=True)
    raw['region'] = raw['state'].map(REGION)
    raw['pollution_share'] = raw['grp_pollution_indicators'] / raw[GRP].sum(axis=1, min_count=len(GRP)) * 100
    by_island = raw.groupby('island')
    for col in ['impact_anchor', 'impact_trash', 'pollution_share', 'inv_crown_of_thorns', 'cot_outbreak',
                'island_vs_region_pct']:
        raw[f'prev_{col}'] = by_island[col].shift(1)
    raw['heat_exposed'] = raw['dhw_peak_prev_year'] >= HEAT_DHW
    pre = raw[raw['survey_year'].between(2015, 2019)].groupby('island')['impact_anchor'].agg(['size', 'mean'])
    pre = pre[pre['size'] >= 3]['mean']
    boat_median = pre.median()
    raw['boat_pressure'] = raw['island'].map(pre)
    raw['boat_group'] = (pd.Series(np.where(raw['boat_pressure'] > boat_median, 'High boat pressure', 'Low boat pressure'),
                                   index=raw.index).where(raw['boat_pressure'].notna()))
    lv = raw[raw['survey_year'].between(*YEARS)].copy()
    ch = lv.dropna(subset=['lcc_change']).copy()

    # --- NOAA station heat -------------------------------------------------------------------
    station_data = {s: read_station(s) for s in STATIONS}
    heat = pd.DataFrame({s: d.groupby('y')['dhw'].max() for s, d in station_data.items()}).loc[2010:]
    last = station_data['sabah'].iloc[-1]
    noaa_last_date = f'{int(last.y)}-{int(last.m):02d}-{int(last.d):02d}'
    heat.rename_axis('year').reset_index().melt(id_vars='year', var_name='station', value_name='peak_dhw') \
        .to_csv(DATA_DIR / 'station_heat.csv', index=False)
    # the dataset's own heat column must agree with these files
    check = raw.groupby(['survey_year', 'noaa_station_id'])['noaa_max_dhw'].first()
    assert all(abs(check[(y, s)] - heat.loc[y, s]) < 0.01 for (y, s) in check.index if s in STATIONS), 'station heat mismatch'

    # --- model spec --------------------------------------------------------------------------
    model = joblib.load(ROOT / 'models' / 'lcc_forecast_model.joblib')
    pre_t, lasso = model[0], model[-1]
    names = list(model[:-1].get_feature_names_out())
    num = pre_t.named_transformers_['num']
    cont = list(pre_t.transformers_[0][2])
    active = [(n, c) for n, c in zip(names, lasso.coef_) if c != 0]
    assert all(n in cont for n, _ in active), 'active features must be continuous'
    spec = {'intercept': float(lasso.intercept_), 'alpha': float(lasso.alpha), 'features': []}
    for n, c in active:
        i = cont.index(n)
        spec['features'].append({'name': n, 'input_column': FORECAST_INPUTS[n], 'coef_per_sd': float(c),
                                 'mean': float(num.named_steps['scale'].mean_[i]),
                                 'scale': float(num.named_steps['scale'].scale_[i]),
                                 'impute_median': float(num.named_steps['impute'].statistics_[i])})
    (DATA_DIR / 'model_spec.json').write_text(json.dumps(spec, indent=2), encoding='utf-8')

    # --- island table ------------------------------------------------------------------------
    latest = raw.groupby('island').tail(1).set_index('island')
    isl = pd.DataFrame({
        'state': latest['state'], 'region': latest['region'], 'latitude': latest['latitude'],
        'longitude': latest['longitude'], 'marine_park': latest['marine_park'],
        'noaa_station_id': latest['noaa_station_id'], 'last_survey_year': latest['survey_year'].astype(int),
        'cover': latest['live_coral_cover_pct'], 'last_change': latest['lcc_change'],
        'vs_region': latest['island_vs_region_pct'], 'curio_absent': latest['n_curio_inverts_absent'],
        'sweetlips': latest['fish_sweetlips'], 'n_sites': latest['n_sites'],
        'surveys_total': raw.groupby('island').size(),
    })
    isl['stale'] = isl['last_survey_year'] < CURRENT_YEAR
    isl['dhw_2025'] = isl['noaa_station_id'].map(heat.loc[2025])
    isl['dhw_2026'] = isl['noaa_station_id'].map(heat.loc[2026])
    pressures = lv.groupby('island').agg(anchor_share=('impact_anchor', 'mean'), trash_share=('impact_trash', 'mean'),
                                         pollution_share=('pollution_share', 'mean'),
                                         cot_outbreak_share=('cot_outbreak', 'mean'))
    isl = isl.join(pressures)
    isl['boat_pressure'] = pre.reindex(isl.index)

    # forecasts: exported formula must reproduce the saved pipeline
    X = pd.DataFrame(np.nan, index=isl.index, columns=list(model.feature_names_in_))
    for model_col, isl_col in FORECAST_INPUTS.items():
        X[model_col] = isl['dhw_2026'] if isl_col is None else isl[isl_col]
    scored = score_islands(isl, spec)
    exact = pd.Series(model.predict(X), index=isl.index)
    assert np.allclose(scored.loc[~isl['stale'], 'forecast_change'], exact[~isl['stale']], atol=1e-9), 'spec != model'

    # --- EDA 1: trends -----------------------------------------------------------------------
    cover = lv.groupby(['survey_year', 'region'])['live_coral_cover_pct'].mean().reset_index()
    cover = pd.concat([cover, lv.groupby('survey_year')['live_coral_cover_pct'].mean().reset_index().assign(region='All sites')])
    cover.rename(columns={'survey_year': 'year', 'live_coral_cover_pct': 'mean_cover'}).to_csv(DATA_DIR / 'eda_cover_trend.csv', index=False)

    # --- EDA 2: variation explained + local-pressure coefficients -------------------------------
    level_blocks = {'Thermal stress': ['noaa_max_dhw', 'dhw_peak_prev_year'],
                    'Crown-of-thorns': ['inv_crown_of_thorns', 'cot_outbreak'],
                    'Local pressures': ['impact_anchor', 'pollution_share', 'boat_pressure']}
    change_blocks = {'Starting cover': ['lcc_prev'],
                     'Thermal stress': ['dhw_peak_prev_year', 'noaa_max_dhw'],
                     'Crown-of-thorns': ['prev_inv_crown_of_thorns', 'prev_cot_outbreak'],
                     'Local pressures': ['prev_impact_anchor', 'prev_pollution_share', 'boat_pressure']}
    var_rows, coef_rows, var_meta = [], [], {}
    scale = {'impact_anchor': 1, 'prev_impact_anchor': 1, 'pollution_share': 10, 'prev_pollution_share': 10, 'boat_pressure': 0.5}
    label = {'impact_anchor': 'Anchor damage reported', 'prev_impact_anchor': 'Anchor damage reported',
             'pollution_share': 'Pollution indicators +10 pts', 'prev_pollution_share': 'Pollution indicators +10 pts',
             'boat_pressure': 'Boat-pressure index +0.5'}
    for target_label, df, blocks, target in [('Coral level', lv, level_blocks, 'live_coral_cover_pct'),
                                             ('Coral change', ch, change_blocks, 'lcc_change')]:
        tab, total, null95, p, d = decompose(df, blocks, target)
        var_rows += [{'target': target_label, 'block': b, **r} for b, r in tab.iterrows()]
        var_meta[target_label] = {'total_r2': total, 'chance95': null95, 'p_local': p, 'n': len(d), 'islands': d['island'].nunique()}
        c = coefs(d, blocks, target).loc[blocks['Local pressures']]
        c = c.mul([scale[i] for i in c.index], axis=0)
        coef_rows += [{'target': target_label, 'pressure': label[i], **r} for i, r in c.iterrows()]
    pd.DataFrame(var_rows).to_csv(DATA_DIR / 'eda_variation.csv', index=False)
    pd.DataFrame(coef_rows).to_csv(DATA_DIR / 'eda_local_coefs.csv', index=False)

    # --- EDA 3: site typology ------------------------------------------------------------------
    g = ch.groupby('island')
    sites = pd.DataFrame({
        'region': g['region'].first(), 'changes': g.size(), 'heat_changes': g['heat_exposed'].sum(),
        'calm_change_sum': ch[~ch['heat_exposed']].groupby('island')['lcc_change'].sum(),
        'heat_change_sum': ch[ch['heat_exposed']].groupby('island')['lcc_change'].sum(),
        'calm_change_per_survey': ch[~ch['heat_exposed']].groupby('island')['lcc_change'].mean(),
        'heat_change_per_survey': ch[ch['heat_exposed']].groupby('island')['lcc_change'].mean(),
        'median_sites': lv.groupby('island')['n_sites'].median(), 'boat_group': g['boat_group'].first(),
    }).fillna({'calm_change_sum': 0, 'heat_change_sum': 0})
    sites = sites[(sites['changes'] >= 5) & (sites['heat_changes'] >= 1) & (sites['changes'] - sites['heat_changes'] >= 2)]
    sites['net_change'] = sites['calm_change_sum'] + sites['heat_change_sum']
    calm_loss, heat_loss = -sites['calm_change_sum'].clip(upper=0), -sites['heat_change_sum'].clip(upper=0)
    sites['pattern'] = np.select([sites['net_change'] >= 0, calm_loss > heat_loss],
                                 ['Stable or gaining', 'Losses mainly in calm years (local action worthwhile)'],
                                 'Losses mainly after heat (thermal)')
    sites['low_reliability'] = sites['median_sites'] <= 3
    sites.sort_values('net_change').rename_axis('island').to_csv(DATA_DIR / 'eda_sites.csv')
    isl['site_type'] = sites['pattern'].reindex(isl.index).fillna('Not classified (too few surveys)')

    # --- EDA 4: boat pressure & shutdown -------------------------------------------------------
    sub = lv[lv['boat_group'].notna()]
    sub.groupby(['survey_year', 'boat_group'])['impact_anchor'].mean().rename('anchor_rate').reset_index() \
        .rename(columns={'survey_year': 'year'}).to_csv(DATA_DIR / 'eda_anchor_trend.csv', index=False)
    periods = {'Before 2017–19': (2017, 2019), 'Shutdown 2020–22': (2020, 2022), 'After 2023–25': (2023, 2025)}
    cs = ch[ch['boat_group'].notna()].copy()
    labels = np.select([cs['survey_year'].between(*v) for v in periods.values()], list(periods), default='')
    cs['period'] = pd.Categorical(np.where(labels == '', None, labels), categories=list(periods))
    cs = cs.dropna(subset=['period'])
    Xa = np.column_stack([np.ones(len(cs)), cs[['lcc_prev', 'dhw_peak_prev_year', 'noaa_max_dhw']].to_numpy(float)])
    cs['adj_change'] = cs['lcc_change'] - Xa @ np.linalg.lstsq(Xa, cs['lcc_change'].to_numpy(float), rcond=None)[0] + cs['lcc_change'].mean()
    shut = pd.concat([mean_ci(cs[cs['boat_group'] == grp], 'lcc_change', 'period').assign(boat_group=grp)
                      for grp in ['High boat pressure', 'Low boat pressure']])
    shut.rename(columns={'group': 'period'}).to_csv(DATA_DIR / 'eda_shutdown.csv', index=False)
    keys = list(periods)

    def did(d, col):
        m = d.groupby(['boat_group', 'period'], observed=True)[col].mean()
        get = lambda grp, k: m.get((grp, keys[k]), np.nan)
        return (get('High boat pressure', 1) - get('High boat pressure', 0)) - (get('Low boat pressure', 1) - get('Low boat pressure', 0))

    did_rows = []
    for col, name in [('lcc_change', 'raw'), ('adj_change', 'adjusted for cover & heat')]:
        lo, hi = island_boot(cs, lambda d, c=col: did(d, c))
        did_rows.append({'version': name, 'did': did(cs, col), 'ci_low': lo, 'ci_high': hi})
    pd.DataFrame(did_rows).to_csv(DATA_DIR / 'eda_did.csv', index=False)

    # --- EDA 5: model patterns -----------------------------------------------------------------
    d = ch.dropna(subset=['prev_island_vs_region_pct']).copy()
    d['bin'] = pd.cut(d['prev_island_vs_region_pct'], [-np.inf, -15, -5, 5, 15, np.inf],
                      labels=['< −15', '−15 to −5', '−5 to +5', '+5 to +15', '> +15'])
    mean_ci(d, 'lcc_change', 'bin').to_csv(DATA_DIR / 'eda_reversion.csv', index=False)
    d = ch.copy()
    d['band'] = pd.cut(d['dhw_peak_prev_year'], [-0.01, 1, 4, 8, np.inf], labels=['< 1', '1–4', '4–8', '≥ 8'])
    bands = mean_ci(d, 'lcc_change', 'band')
    bands.to_csv(DATA_DIR / 'eda_heat_bands.csv', index=False)
    yr = mean_ci(ch, 'lcc_change', 'survey_year')
    yr['mean_prev_dhw'] = yr['group'].map(ch.groupby('survey_year')['dhw_peak_prev_year'].mean())
    yr.to_csv(DATA_DIR / 'eda_yearly_change.csv', index=False)
    d = lv.dropna(subset=['lcc_change', 'n_sites']).copy()
    d['abs_change'] = d['lcc_change'].abs()
    d['sites'] = pd.cut(d['n_sites'], [0, 3, 5, 8, 40], labels=['1–3', '4–5', '6–8', '9+'])
    mean_ci(d, 'abs_change', 'sites').to_csv(DATA_DIR / 'eda_noise.csv', index=False)

    isl.rename_axis('island').to_csv(DATA_DIR / 'islands.csv')
    meta = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'latest_survey_year': int(raw['survey_year'].max()), 'noaa_last_date': noaa_last_date,
        'default_thresholds': DEFAULT_THRESHOLDS, 'boat_pressure_median': float(boat_median),
        'variation': var_meta, 'model_typical_error': 6.05,
        'heat_band_means': dict(zip(bands['group'].astype(str), bands['mean'].round(2))),
        'takeaways': {
            'trends': 'Average cover fell to 40% in 2025, the lowest of 2015–2025. Declines follow the regional heat events '
                      'of 2016 and 2024. Sabah has the lowest cover and the most frequent heat stress.',
            'heat2026': 'By the last NOAA update, Sabah has reached its highest heat stress on record, above its 2024 peak.',
            'typology': 'Of 28 sites, 10 lose coral mainly after heat stress (mostly Sabah), 9 mainly in calm years (local '
                        'action worthwhile: Redang, Tioman, the Johor islands) and 9 are stable or gaining.',
            'local': 'Local pressures account for about 7% of how much coral a reef has (islands with habitual anchor damage '
                     'carry about 6 points less) but add nothing beyond chance to year-to-year change.',
            'shutdown': 'Anchor damage halved at busy islands in 2020 and their reefs improved more during the shutdown, '
                        'but the difference is within the noise.',
            'patterns': 'Reefs drift back toward their regional average, lose more after hotter years, and small surveys '
                        '(1–3 sites) swing about twice as much as larger ones.',
        },
    }
    (DATA_DIR / 'meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')

    # --- checks against eda.ipynb results -------------------------------------------------------
    v = pd.DataFrame(var_rows).set_index(['target', 'block'])['share']
    assert round(v[('Coral level', 'Local pressures')], 3) == 0.067 and round(v[('Coral change', 'Local pressures')], 3) == 0.027
    assert sites['pattern'].value_counts().to_dict() == {'Losses mainly after heat (thermal)': 10,
                                                         'Losses mainly in calm years (local action worthwhile)': 9,
                                                         'Stable or gaining': 9}
    assert len(isl) == 56 and (~isl['stale']).sum() == 40
    print(f'islands: {len(isl)} ({(~isl["stale"]).sum()} current, {isl["stale"].sum()} stale); NOAA data to {noaa_last_date}')
    print('urgency (2026 heat to date):', scored['urgency'].value_counts().to_dict())
    print(f'wrote {len(list(DATA_DIR.glob("*")))} files to {DATA_DIR}')


if __name__ == '__main__':
    main()
