"""Reef Watch Malaysia: coral urgency map, Gemini action insights and EDA.

Run from the project root:  streamlit run dashboard/app.py
"""
import json
import sys
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_insights as gi  # noqa: E402
from logic import (DATA_DIR, DEFAULT_THRESHOLDS, SCENARIOS, STATION_LABEL, STATIONS,  # noqa: E402
                   load_model_spec, score_islands)

st.set_page_config(page_title='Reef Watch Malaysia', page_icon='🪸', layout='wide')

COLORS = {'red': '#d7263d', 'yellow': '#f0a202', 'green': '#2e9e44', 'grey': '#9aa0a6'}
LABELS = {'red': 'Act now', 'yellow': 'Watch closely', 'green': 'Healthy', 'grey': 'Data too old'}
BADGE = {'red': 'red', 'yellow': 'orange', 'green': 'green', 'grey': 'gray'}
PALETTE = ['#00798c', '#edae49', '#d1495b', '#6a4c93', '#30638e']
MISSING = 'dashboard/data is missing: run `python dashboard/prepare_data.py` first.'


# ----------------------------------------------------------------------------- data
@st.cache_data
def load_static():
    if not (DATA_DIR / 'islands.csv').exists():
        return None
    csv = lambda name: pd.read_csv(DATA_DIR / name)
    return {
        'islands': pd.read_csv(DATA_DIR / 'islands.csv', index_col='island'),
        'spec': load_model_spec(),
        'meta': json.loads((DATA_DIR / 'meta.json').read_text(encoding='utf-8')),
        **{name: csv(f'{name}.csv') for name in ['station_heat', 'eda_cover_trend', 'eda_variation', 'eda_local_coefs',
                                                 'eda_sites', 'eda_anchor_trend', 'eda_shutdown', 'eda_did',
                                                 'eda_reversion', 'eda_heat_bands', 'eda_yearly_change', 'eda_noise']},
    }


@st.cache_data
def load_insights(mtime: float):
    """Cached per file version, so insights regenerated from the command line show up on the next rerun."""
    return gi.load_insights()


def insights_mtime():
    return gi.INSIGHTS_PATH.stat().st_mtime if gi.INSIGHTS_PATH.exists() else 0.0


data = load_static()
if data is None:
    st.error(MISSING)
    st.stop()
meta, islands_base = data['meta'], data['islands']

# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header('Scenario')
    scenario = st.radio('Heat stress used for the forecast', SCENARIOS, index=0,
                        help='Peak degree-heating weeks (DHW) in the year before the next survey, per NOAA station. '
                             f'NOAA data run to {meta["noaa_last_date"]}.')
    custom = None
    if scenario == 'Custom':
        dhw26 = islands_base.groupby('noaa_station_id')['dhw_2026'].first()
        custom = {s: st.slider(f'{STATION_LABEL[s]} DHW', 0.0, 20.0, float(round(dhw26[s], 1)), 0.5) for s in STATIONS}

    with st.expander('Urgency thresholds'):
        th = {
            'poor': st.number_input('Red below projected cover (%)', 5.0, 45.0, DEFAULT_THRESHOLDS['poor'], 1.0),
            'good': st.number_input('Green from projected cover (%)', 30.0, 80.0, DEFAULT_THRESHOLDS['good'], 1.0),
            'severe_dhw': st.number_input('Severe heat (DHW)', 2.0, 16.0, DEFAULT_THRESHOLDS['severe_dhw'], 0.5),
            'severe_decline': st.number_input('Red if decline at or below (pts) under severe heat', -10.0, 0.0,
                                              DEFAULT_THRESHOLDS['severe_decline'], 0.5),
        }
        st.caption('Bands follow Reef Check: poor < 25%, fair 25–50%, good ≥ 50% live coral cover.')

    st.header('Filters')
    regions = st.multiselect('Region', sorted(islands_base['region'].unique()), placeholder='All regions')
    levels = st.multiselect('Urgency', list(LABELS), format_func=lambda k: LABELS[k], placeholder='All levels')

scored = score_islands(islands_base, data['spec'], scenario, custom, th)
keep = pd.Series(True, index=scored.index)
if regions:
    keep &= scored['region'].isin(regions)
if levels:
    keep &= scored['urgency'].isin(levels)
view = scored[keep]
insights = load_insights(insights_mtime())

# ----------------------------------------------------------------------------- header
st.title('🪸 Reef Watch Malaysia')
st.caption(f'Where to act first to protect coral for sustainable tourism. Reef Check surveys to '
           f'{meta["latest_survey_year"]}, NOAA heat stress to {meta["noaa_last_date"]}. Forecasts assume the '
           f'**{scenario}** heat scenario.')
counts = scored['urgency'].value_counts()
DOT = {'red': '🔴', 'yellow': '🟡', 'green': '🟢', 'grey': '⚪'}
for col, lvl in zip(st.columns(4), DOT):
    col.metric(f'{DOT[lvl]} {LABELS[lvl]}', int(counts.get(lvl, 0)), border=True)

# ----------------------------------------------------------------------------- map
st.subheader('Urgency map')
st.caption('Each dot is a surveyed island, sized by live coral cover. Hover for details; click a dot to open its '
           'insights below. Urgency combines projected cover (current cover + forecast change) with severe heat.')


def tooltip(name, r):
    if r['urgency'] == 'grey':
        body = f'Last surveyed {r.last_survey_year}; cover then {r.cover:.1f}%'
    else:
        body = (f'Cover {r.cover:.1f}% → projected {r.projected_cover:.1f}% '
                f'(forecast {r.forecast_change:+.1f} pts)<br>Heat {r.heat_dhw:.1f} DHW · {r.site_type}')
    return (f'<b>{name}</b> ({r.state})<br><span style="color:{COLORS[r.urgency]}"><b>{LABELS[r.urgency]}</b></span>: '
            f'{r.urgency_reason}<br>{body}')


# scroll_wheel_zoom off: otherwise scrolling the page down to the insights zooms the map instead
fmap = folium.Map(location=[4.3, 109.5], zoom_start=6, tiles='OpenStreetMap', control_scale=True, scroll_wheel_zoom=False)
for name, r in view.sort_values('urgency', key=lambda s: s.map({'grey': 0, 'green': 1, 'yellow': 2, 'red': 3})).iterrows():
    folium.CircleMarker(
        location=[r.latitude, r.longitude], radius=5 + (r.cover / 7), color='white', weight=1.2,
        fill=True, fill_color=COLORS[r.urgency], fill_opacity=0.9 if r.urgency != 'grey' else 0.55,
        tooltip=folium.Tooltip(tooltip(name, r), sticky=True),
    ).add_to(fmap)
if len(view):
    fmap.fit_bounds([[view['latitude'].min() - 0.4, view['longitude'].min() - 0.4],
                     [view['latitude'].max() + 0.4, view['longitude'].max() + 0.4]])
legend = ''.join(f'<span style="display:inline-block;margin-right:14px"><span style="display:inline-block;width:12px;'
                 f'height:12px;border-radius:50%;background:{COLORS[k]};margin-right:5px;vertical-align:-1px"></span>'
                 f'{LABELS[k]}</span>' for k in COLORS)
st.markdown(f'<div style="font-size:0.9rem">{legend}</div>', unsafe_allow_html=True)
map_state = st_folium(fmap, key='map', height=540, use_container_width=True,
                      returned_objects=['last_object_clicked', 'last_clicked'])

# A click on a dot, or anywhere near one, selects the nearest visible island (dots are small at this zoom)
click = (map_state or {}).get('last_object_clicked') or (map_state or {}).get('last_clicked')
if click and len(view):
    dist = np.hypot(view['latitude'] - click['lat'], view['longitude'] - click['lng'])
    click_id = (round(click['lat'], 5), round(click['lng'], 5))
    if dist.min() < 0.35 and st.session_state.get('last_click') != click_id:
        st.session_state['last_click'] = click_id
        st.session_state['selected'] = dist.idxmin()

# ----------------------------------------------------------------------------- insights
st.subheader('Insights and actions')
have_key = gi.has_api_key()


def stale_badge(record, payload):
    if record and record.get('_meta', {}).get('input_hash') != gi.payload_hash(payload):
        st.warning(f'Generated for the "{record["_meta"].get("scenario")}" scenario or earlier data/thresholds; '
                   'regenerate to update.', icon='⚠️')


# --- overview
ov = insights.get('overview')
with st.container(border=True):
    st.markdown('#### 🇲🇾 Malaysia-wide overview')
    if ov:
        stale_badge(ov, gi.overview_payload(scored, scenario, meta))
        st.markdown(f'**{ov["headline"]}**')
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown('**Key findings**\n' + '\n'.join(f'- {k}' for k in ov['key_findings']))
            st.markdown('**Regional patterns**\n' + '\n'.join(f'- **{p["region"]}**: {p["pattern"]}'
                                                             for p in ov['regional_patterns']))
        with c2:
            st.markdown('**Top priorities**\n' + '\n'.join(f'- **{p["island"]}**: {p["reason"]}'
                                                          for p in ov['top_priority_islands']))
            st.markdown(f'**2026 heat outlook**\n\n{ov["heat_outlook_2026"]}')
        st.caption(f'Caveats: {ov["caveats"]} · Generated by {ov["_meta"]["model"]} on {ov["_meta"]["generated_at"]}.')
    else:
        st.info('No insights generated yet. Add your Gemini key to a `.env` file in the project folder '
                '(copy `.env.example`), then run `python dashboard/generate_insights.py` or use **Regenerate** below.', icon='💡')

# --- island card
names = list(scored.sort_values(['urgency', 'projected_cover'],
                                key=lambda s: s.map({'red': 0, 'yellow': 1, 'green': 2, 'grey': 3}) if s.name == 'urgency' else s).index)
if st.session_state.get('selected') not in names:
    st.session_state['selected'] = names[0]
sel = st.selectbox('Island (or click a dot on the map)', names, key='selected',
                   format_func=lambda n: f'{n} ({scored.loc[n, "state"]}) · {LABELS[scored.loc[n, "urgency"]]}')
r = scored.loc[sel]
with st.container(border=True):
    head, badge = st.columns([4, 1])
    head.markdown(f'#### {sel}, {r.state}')
    head.caption(f'{r.marine_park} · NOAA station: {STATION_LABEL[r.noaa_station_id]} · last surveyed {r.last_survey_year}')
    with badge:
        st.badge(LABELS[r.urgency], color=BADGE[r.urgency])
    st.markdown(f'**Why this colour:** {r.urgency_reason}.')
    m = st.columns(5)
    m[0].metric('Live coral cover', f'{r.cover:.1f}%', f'{r.last_change:+.1f} pts' if pd.notna(r.last_change) else None,
                help='Change since the previous survey')
    if r.urgency != 'grey':
        m[1].metric('Forecast next change', f'{r.forecast_change:+.1f} pts', help='Typical error about ±6 points')
        m[2].metric('Projected cover', f'{r.projected_cover:.1f}%')
        m[3].metric('Heat stress (scenario)', f'{r.heat_dhw:.1f} DHW')
    m[4].metric('Sites surveyed', '–' if pd.isna(r.n_sites) else int(r.n_sites))
    pressure = {'Anchor damage': r.anchor_share, 'Trash': r.trash_share, 'Crown-of-thorns outbreak': r.cot_outbreak_share}
    st.caption('**EDA site type:** ' + r.site_type + ' · **Share of 2015–2025 surveys reporting** ' +
               ', '.join(f'{k.lower()}: {v:.0%}' for k, v in pressure.items() if pd.notna(v)) +
               (f' · **Pollution indicators:** {r.pollution_share:.0f}% of non-coral seabed' if pd.notna(r.pollution_share) else ''))

    rec = insights.get('islands', {}).get(sel)
    if r.urgency == 'grey':
        st.info('This island has not been surveyed since '
                f'{r.last_survey_year}, so it is not forecast. A new survey is the first action.', icon='🔍')
    elif rec:
        stale_badge(rec, gi.island_payload(r, scenario))
        st.markdown(f'### {rec["headline"]}')
        st.markdown(rec['why'])
        c1, c2 = st.columns([2, 3])
        with c1:
            st.markdown('**Drivers**\n' + '\n'.join(f'- **{d["factor"]}**: {d["evidence"]}' for d in rec['drivers']))
            st.markdown(f'**Monitor at the next survey:** {rec["monitoring"]}')
        with c2:
            st.markdown('**Recommended actions**')
            acts = pd.DataFrame(rec['actions']).sort_values('actor')
            st.dataframe(acts[['actor', 'action', 'timeframe', 'rationale']], hide_index=True, width='stretch',
                         column_config={'actor': 'Who', 'action': 'Action', 'timeframe': 'When', 'rationale': 'Why'})
        st.caption(f'Confidence: **{rec["confidence"]}** · {rec["caveats"]} · Generated by {rec["_meta"]["model"]} '
                   f'on {rec["_meta"]["generated_at"]}.')
    else:
        st.info('No Gemini insight for this island yet.', icon='💡')

    b1, b2, _ = st.columns([2, 2, 3])
    regen_one = b1.button('↻ Regenerate this island + overview', disabled=not have_key or r.urgency == 'grey', width='stretch')
    regen_all = b2.button('↻ Regenerate all islands', disabled=not have_key, width='stretch')
    if not have_key:
        st.caption('Regenerate needs a Gemini key: put `GOOGLE_API_KEY=...` in a `.env` file in the project folder '
                   '(see `.env.example`) and restart the app.')
    if regen_one or regen_all:
        targets = [sel] if regen_one else None
        ok = False
        with st.status('Asking Gemini…', expanded=True) as status:
            try:
                gi.generate(scenario, custom, th, islands=targets, overview=True, force=True, log=st.write)
                status.update(label='Insights updated', state='complete')
                ok = True
            except Exception as e:     # show the API/validation error without exposing credentials
                status.update(label='Gemini request failed', state='error')
                st.error(f'{type(e).__name__}: {e}')
        if ok:
            st.rerun()

# ----------------------------------------------------------------------------- EDA
st.subheader('What the survey data show')
tk = meta['takeaways']
tabs = st.tabs(['Trends & 2026 heat', 'Where losses come from', 'Local pressures', 'Model patterns'])


def base_layout(fig, title, h=380, **kw):
    fig.update_layout(title=title, height=h, margin=dict(l=10, r=10, t=50, b=10), template='plotly_white',
                      legend=dict(orientation='h', y=-0.2), **kw)
    return fig


def ci_bar(df, x_labels, color, title, ytitle):
    fig = go.Figure(go.Bar(x=x_labels, y=df['mean'], marker_color=color,
                           error_y=dict(type='data', symmetric=False, array=df['ci_high'] - df['mean'],
                                        arrayminus=df['mean'] - df['ci_low']),
                           customdata=df[['n']], hovertemplate='%{x}<br>mean %{y:.2f}<br>n=%{customdata[0]}<extra></extra>'))
    fig.add_hline(y=0, line_color='black', line_width=1)
    return base_layout(fig, title, yaxis_title=ytitle)


with tabs[0]:
    st.caption(tk['trends'])
    c1, c2 = st.columns(2)
    ct = data['eda_cover_trend']
    fig = go.Figure()
    for i, (reg, g) in enumerate(ct.groupby('region')):
        fig.add_scatter(x=g['year'], y=g['mean_cover'], name=reg, mode='lines+markers',
                        line=dict(width=4 if reg == 'All sites' else 2, color='black' if reg == 'All sites' else PALETTE[i % 5]))
    c1.plotly_chart(base_layout(fig, 'Mean live coral cover by region', yaxis_title='Live coral cover (%)'), width='stretch')
    sh = data['station_heat']
    fig = go.Figure()
    for i, s in enumerate(STATIONS):
        g = sh[(sh['station'] == s) & sh['year'].between(2015, 2025)]
        fig.add_bar(x=g['year'], y=g['peak_dhw'], name=STATION_LABEL[s], marker_color=PALETTE[i])
    fig.add_hline(y=4, line_dash='dash', annotation_text='4 DHW: significant bleaching expected',
                  annotation_position='top left', annotation_font_size=10)
    c2.plotly_chart(base_layout(fig, 'Peak heat stress per year by NOAA station', barmode='group', yaxis_title='Peak DHW (°C-weeks)'),
                    width='stretch')
    st.caption(tk['heat2026'])
    years = [2016, 2019, 2020, 2023, 2024, 2025, 2026]
    fig = go.Figure()
    reds = ['#fcbba1', '#fc9272', '#fb6a4a', '#ef3b2c', '#cb181d', '#d9d9d9', '#252525']
    for y, colr in zip(years, reds):
        g = sh[sh['year'] == y].set_index('station').reindex(STATIONS)
        fig.add_bar(x=[STATION_LABEL[s] for s in STATIONS], y=g['peak_dhw'], name=f'{y}{" (to date)" if y == 2026 else ""}', marker_color=colr)
    fig.add_hline(y=4, line_dash='dash')
    st.plotly_chart(base_layout(fig, f'2026 heat stress (to {meta["noaa_last_date"]}) against past bleaching years',
                                barmode='group', yaxis_title='Peak DHW (°C-weeks)'), width='stretch')

with tabs[1]:
    st.caption(tk['typology'])
    s = data['eda_sites'].sort_values('net_change', ascending=False)
    same_sign = (s['calm_change_sum'] < 0) == (s['heat_change_sum'] < 0)
    fig = go.Figure()
    fig.add_bar(y=s['island'], x=s['calm_change_sum'], orientation='h', name='Change in calm years', marker_color='#00798c')
    fig.add_bar(y=s['island'], x=s['heat_change_sum'], base=np.where(same_sign, s['calm_change_sum'], 0), orientation='h',
                name='Change after heat stress (≥ 4 DHW)', marker_color='#d1495b')
    fig.add_scatter(y=s['island'], x=s['net_change'], mode='markers', name='Net change 2015–2025',
                    marker=dict(color='black', size=7), customdata=s[['pattern']],
                    hovertemplate='%{y}: net %{x:.1f} pts<br>%{customdata[0]}<extra></extra>')
    fig.add_vline(x=0, line_color='black', line_width=1)
    st.plotly_chart(base_layout(fig, 'Where did each site lose coral: in calm years or after heat stress?', h=720,
                                barmode='overlay', xaxis_title='Summed change in live coral cover, 2015–2025 (points)'),
                    width='stretch')
    colors = {'Losses mainly in calm years (local action worthwhile)': '#00798c', 'Losses mainly after heat (thermal)': '#d1495b',
              'Stable or gaining': '#9aa0a6'}
    fig = go.Figure()
    for pat, g in s.groupby('pattern'):
        fig.add_scatter(x=g['heat_change_per_survey'], y=g['calm_change_per_survey'], mode='markers+text', name=pat,
                        text=g['island'], textposition='top center', textfont=dict(size=9),
                        marker=dict(size=g['changes'] * 2.2, color=colors[pat], opacity=0.8))
    fig.add_hline(y=0, line_color='black', line_width=1)
    fig.add_vline(x=0, line_color='black', line_width=1)
    st.plotly_chart(base_layout(fig, 'Site typology: below the line = losing coral even without heat stress', h=520,
                                xaxis_title='Average change per survey after heat stress (pts)',
                                yaxis_title='Average change per survey in calm years (pts)'), width='stretch')

with tabs[2]:
    st.caption(tk['local'])
    c1, c2 = st.columns(2)
    v = data['eda_variation']
    block_colors = {'Starting cover': '#8d99ae', 'Thermal stress': '#d1495b', 'Crown-of-thorns': '#edae49', 'Local pressures': '#00798c'}
    fig = go.Figure()
    for block, colr in block_colors.items():
        g = v[v['block'] == block]
        fig.add_bar(y=g['target'], x=g['share'] * 100, orientation='h', name=block, marker_color=colr,
                    hovertemplate='%{y}: %{x:.1f}%<extra>' + block + '</extra>')
    rest = 100 - v.groupby('target')['share'].sum() * 100
    fig.add_bar(y=rest.index, x=rest.values, orientation='h', name='Unexplained', marker_color='#e9ecef')
    c1.plotly_chart(base_layout(fig, 'Share of variation explained by each block (%)', barmode='stack', xaxis_range=[0, 100]),
                    width='stretch')
    lc = data['eda_local_coefs']
    fig = go.Figure()
    for i, (tgt, g) in enumerate(lc.groupby('target')):
        fig.add_scatter(x=g['coef'], y=g['pressure'] + ' · ' + tgt, mode='markers', name=tgt, marker=dict(size=10, color=PALETTE[i]),
                        error_x=dict(type='data', symmetric=False, array=g['ci_high'] - g['coef'], arrayminus=g['coef'] - g['ci_low']))
    fig.add_vline(x=0, line_color='black', line_width=1)
    c2.plotly_chart(base_layout(fig, 'Local pressures after heat and crown-of-thorns (95% CI)', xaxis_title='Effect (points)'),
                    width='stretch')
    st.caption(tk['shutdown'])
    c1, c2 = st.columns(2)
    at = data['eda_anchor_trend']
    fig = go.Figure()
    for grp, colr in [('High boat pressure', '#c1121f'), ('Low boat pressure', '#669bbc')]:
        g = at[at['boat_group'] == grp]
        fig.add_scatter(x=g['year'], y=g['anchor_rate'] * 100, name=grp, mode='lines+markers', line=dict(color=colr))
    fig.add_vrect(x0=2019.5, x1=2022.5, fillcolor='grey', opacity=0.15, line_width=0, annotation_text='shutdown')
    c1.plotly_chart(base_layout(fig, 'Did anchor damage drop during the 2020–22 shutdown?', yaxis_title='% of surveys'),
                    width='stretch')
    sd = data['eda_shutdown']
    fig = go.Figure()
    for grp, colr in [('High boat pressure', '#c1121f'), ('Low boat pressure', '#669bbc')]:
        g = sd[sd['boat_group'] == grp]
        fig.add_scatter(x=g['period'], y=g['mean'], name=grp, mode='markers', marker=dict(size=12, color=colr),
                        error_y=dict(type='data', symmetric=False, array=g['ci_high'] - g['mean'], arrayminus=g['mean'] - g['ci_low']))
    fig.add_hline(y=0, line_color='black', line_width=1)
    c2.plotly_chart(base_layout(fig, 'Coral change before, during and after the shutdown', yaxis_title='Mean change per survey (pts)',
                                scattermode='group'), width='stretch')
    did = data['eda_did'].set_index('version')
    st.caption('Difference-in-differences (high minus low boat pressure, shutdown minus before): ' +
               ' · '.join(f'{k}: {r.did:+.1f} pts (95% CI {r.ci_low:+.1f} to {r.ci_high:+.1f})' for k, r in did.iterrows()))

with tabs[3]:
    st.caption(tk['patterns'])
    c1, c2 = st.columns(2)
    rv = data['eda_reversion']
    c1.plotly_chart(ci_bar(rv, rv['group'], ['#00798c' if m > 0 else '#d1495b' for m in rv['mean']],
                           'Reefs drift back toward their regional average', 'Mean next change (pts)')
                    .update_xaxes(title='How far above its regional average at the last survey (pts)'), width='stretch')
    hb = data['eda_heat_bands']
    c2.plotly_chart(ci_bar(hb, hb['group'], ['#fcd5ce', '#f8ad9d', '#f07167', '#b5172a'],
                           'More heat last year → more coral lost', 'Mean change (pts)')
                    .update_xaxes(title='Peak heat stress in the year before the survey (DHW)'), width='stretch')
    c1, c2 = st.columns(2)
    yc = data['eda_yearly_change']
    c1.plotly_chart(ci_bar(yc, yc['group'].astype(str), [f'rgba(203,24,29,{0.25 + 0.7 * min(h / 10, 1):.2f})' for h in yc['mean_prev_dhw']],
                           'Year by year: darker = more heat the year before', 'Mean change (pts)'), width='stretch')
    nz = data['eda_noise']
    c2.plotly_chart(ci_bar(nz, nz['group'], '#6c757d', 'Small surveys swing much more (survey noise)', 'Typical |change| (pts)')
                    .update_xaxes(title='Sites surveyed'), width='stretch')

with st.expander('Method and caveats'):
    st.markdown(f"""
- **Forecast:** weighted Lasso on 7 features (previous cover, position vs regional average, previous change, previous-year heat \
stress, and three minor survey features). Evaluated by rolling-origin forecasts 2018–2025: typical error about ±{meta['model_typical_error']:.0f} \
points, about 4% better than predicting the average. Small forecast changes mostly reflect reefs drifting toward their regional average.
- **Urgency:** red if projected cover < {th['poor']:.0f}% or the forecast decline is ≤ {th['severe_decline']:.1f} pts under severe heat \
(≥ {th['severe_dhw']:.0f} DHW); yellow if projected cover is {th['poor']:.0f}–{th['good']:.0f}%; green otherwise. Grey = no survey since 2024 or earlier.
- **Heat stress:** NOAA Coral Reef Watch regional virtual stations; the 2026 values are the peak to date and can still rise.
- **Local pressures:** from Reef Check survey reports; tourism and development intensity aren't measured, and the boat-pressure \
index (share of 2015–2019 surveys reporting anchor damage) is a stand-in. Impact flags are reported more often in recent years.
- **Insights** are generated by Gemini from the numbers shown here and should be checked in the field. All results are associations, not proven causes.
""")
